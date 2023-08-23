import traceback
import uuid
from itertools import cycle
from typing import Any, AsyncGenerator, List

import anyio
import httpx
from fastapi import HTTPException, Request, status
from fastapi.responses import StreamingResponse
from loguru import logger

from ..content import ChatSaver, WhisperSaver
from ..decorators import async_retry, token_rate_limit_decorator
from .settings import *


class ForwardingBase:
    BASE_URL = None
    ROUTE_PREFIX = None
    client: httpx.AsyncClient = None

    if IP_BLACKLIST or IP_WHITELIST:
        validate_host = True
    else:
        validate_host = False

    timeout = TIMEOUT

    @staticmethod
    def validate_request_host(ip):
        """
        Validates the request host IP address against the IP whitelist and blacklist.

        Args:
            ip (str): The IP address to be validated.

        Raises:
            HTTPException: If the IP address is not in the whitelist or if it is in the blacklist.
        """
        if IP_WHITELIST and ip not in IP_WHITELIST:
            logger.warning(f"IP {ip} is not in the whitelist")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden Error",
            )
        if IP_BLACKLIST and ip in IP_BLACKLIST:
            logger.warning(f"IP {ip} is in the blacklist")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden Error",
            )

    @staticmethod
    @token_rate_limit_decorator(token_interval_conf)
    async def aiter_bytes(r: httpx.Response) -> AsyncGenerator[bytes, Any]:
        async for chunk in r.aiter_bytes():
            yield chunk
        await r.aclose()

    @async_retry(
        max_retries=3,
        delay=0.5,
        backoff=2,
        exceptions=(HTTPException, anyio.EndOfStream),
    )
    async def try_send(self, client_config: dict, request: Request):
        """
        Try to send the request.

        Args:
            client_config (dict): The configuration for the client.
            request (Request): The request to be sent.

        Returns:
            Response: The response from the client.

        Raises:
            HTTPException: If there is a connection error or any other exception occurs.
        """
        try:
            req = self.client.build_request(
                method=request.method,
                url=client_config['url'],
                headers=client_config["headers"],
                content=request.stream(),
                timeout=self.timeout,
            )
            return await self.client.send(req, stream=True)

        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            error_info = (
                f"{type(e)}: {e} | "
                f"Please check if host={request.client.host} can access [{self.BASE_URL}] successfully?"
            )
            traceback_info = traceback.format_exc()
            logger.error(f"{error_info} traceback={traceback_info}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_info
            )

        except anyio.EndOfStream:
            error_info = "EndOfStream Error: trying to read from a stream that has been closed from the other end."
            traceback_info = traceback.format_exc()
            logger.error(f"{error_info} traceback={traceback_info}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_info
            )

        except Exception as e:
            error_info = f"{type(e)}: {e}"
            traceback_info = traceback.format_exc()
            logger.error(f"{error_info} traceback={traceback_info}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_info
            )

    def prepare_client(self, request: Request):
        """
        Prepares the client configuration based on the given request.

        Args:
            request (Request): The request object containing the necessary information.

        Returns:
            dict: The client configuration dictionary with the necessary parameters set.
                  The dictionary has the following keys:
                  - 'auth': The authorization header value.
                  - 'headers': The dictionary of headers.
                  - 'url': The URL object.
                  - 'url_path': The URL path.

        Raises:
            AssertionError: If the `BASE_URL` or `ROUTE_PREFIX` is not set.
        """
        assert self.BASE_URL is not None
        assert self.ROUTE_PREFIX is not None
        if self.validate_host:
            ip = get_client_ip(request)
            # print(f"{ip=}")
            self.validate_request_host(ip)

        _url_path = f"{request.scope.get('root_path')}{request.scope.get('path')}"
        prefix_index = 0 if self.ROUTE_PREFIX == '/' else len(self.ROUTE_PREFIX)

        url_path = _url_path[prefix_index:]
        url = httpx.URL(path=url_path, query=request.url.query.encode("utf-8"))
        headers = dict(request.headers)
        auth = headers.pop("authorization", "")
        content_type = headers.pop("content-type", "application/json")
        auth_headers_dict = {"Content-Type": content_type, "Authorization": auth}
        client_config = {
            'auth': auth,
            'headers': auth_headers_dict,
            'url': url,
            'url_path': url_path,
        }

        return client_config

    async def reverse_proxy(self, request: Request):
        """
        Reverse proxies the given request.

        Args:
            request (Request): The request to be reverse proxied.

        Returns:
            StreamingResponse: The response from the reverse proxied server, as a streaming response.
        """
        assert self.client is not None

        client_config = self.prepare_client(request)

        r = await self.try_send(client_config, request)

        return StreamingResponse(
            self.aiter_bytes(r),
            status_code=r.status_code,
            media_type=r.headers.get("content-type"),
        )


class OpenaiBase(ForwardingBase):
    _cycle_api_key = cycle(OPENAI_API_KEY)
    _no_auth_mode = OPENAI_API_KEY != [] and FWD_KEY == set()

    chatsaver: ChatSaver = None
    whispersaver: WhisperSaver = None

    def _add_result_log(
        self, byte_list: List[bytes], uid: str, route_path: str, request_method: str
    ):
        """
        Adds a result log for the given byte list, uid, route path, and request method.

        Args:
            byte_list (List[bytes]): The list of bytes to be processed.
            uid (str): The unique identifier.
            route_path (str): The route path.
            request_method (str): The request method.

        Returns:
            None
        """
        try:
            if (LOG_CHAT or print_chat) and request_method == "POST":
                if route_path == CHAT_COMPLETION_ROUTE:
                    target_info = self.chatsaver.parse_iter_bytes(byte_list)
                    if LOG_CHAT:
                        self.chatsaver.log_chat(
                            {target_info["role"]: target_info["content"], "uid": uid}
                        )
                    if print_chat:
                        self.chatsaver.print_chat_info(
                            {target_info["role"]: target_info["content"], "uid": uid}
                        )

                elif route_path.startswith("/v1/audio/"):
                    self.whispersaver.add_log(b"".join([_ for _ in byte_list]))

                else:
                    ...
        except Exception as e:
            logger.warning(f"log chat (not) error:\n{traceback.format_exc()}")

    async def _add_payload_log(self, request: Request, url_path: str):
        """
        Adds a payload log for the given request.

        Args:
            request (Request): The request object.
            url_path (str): The URL path of the request.

        Returns:
            str: The unique identifier (UID) of the payload log, which is used to match the chat result log.

        Raises:
            Suppress all errors.

        """
        uid = None
        if (LOG_CHAT or print_chat) and request.method == "POST":
            try:
                if url_path == CHAT_COMPLETION_ROUTE:
                    chat_info = await self.chatsaver.parse_payload(request)
                    uid = chat_info.get("uid")
                    if chat_info:
                        if LOG_CHAT:
                            self.chatsaver.log_chat(chat_info)
                        if print_chat:
                            self.chatsaver.print_chat_info(chat_info)

                elif url_path.startswith("/v1/audio/"):
                    uid = uuid.uuid4().__str__()

                else:
                    ...

            except Exception as e:
                logger.warning(
                    f"log chat error:\nhost:{request.client.host} method:{request.method}: {traceback.format_exc()}"
                )
        return uid

    @token_rate_limit_decorator(token_interval_conf)
    async def aiter_bytes(
        self, r: httpx.Response, request: Request, route_path: str, uid: str
    ):
        """
        Asynchronously iterates over the bytes of the response and yields each chunk.

        Args:
            r (httpx.Response): The HTTP response object.
            request (Request): The original request object.
            route_path (str): The route path.
            uid (str): The unique identifier.

        Returns:
            A generator that yields each chunk of bytes from the response.
        """
        byte_list = []
        async for chunk in r.aiter_bytes():
            byte_list.append(chunk)
            yield chunk

        await r.aclose()

        if uid:
            if r.is_success:
                self._add_result_log(byte_list, uid, route_path, request.method)
            else:
                response_info = b"".join([_ for _ in byte_list])
                logger.warning(f'uid: {uid}\n' f'{response_info}')

    async def reverse_proxy(self, request: Request):
        """
        Reverse proxies the given requests.

        Args:
            request (Request): The incoming request object.

        Returns:
            StreamingResponse: The response from the reverse proxied server, as a streaming response.
        """
        client_config = self.prepare_client(request)
        url_path = client_config["url_path"]

        def set_apikey_from_preset():
            nonlocal client_config
            auth_prefix = "Bearer "
            auth = client_config["auth"]
            if self._no_auth_mode or auth and auth[len(auth_prefix) :] in FWD_KEY:
                auth = auth_prefix + next(self._cycle_api_key)
                client_config["headers"]["Authorization"] = auth

        set_apikey_from_preset()

        uid = await self._add_payload_log(request, url_path)

        r = await self.try_send(client_config, request)

        return StreamingResponse(
            self.aiter_bytes(r, request, url_path, uid),
            status_code=r.status_code,
            media_type=r.headers.get("content-type"),
        )
