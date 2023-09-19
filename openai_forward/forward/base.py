import traceback
from itertools import cycle
from typing import Any, AsyncGenerator, List

import anyio
import httpx
from fastapi import HTTPException, Request, status
from loguru import logger
from starlette.responses import StreamingResponse

from ..content.openai import ChatLogger, WhisperLogger
from ..decorators import async_retry, async_token_rate_limit
from ..helper import get_unique_id
from ..settings import *


class ForwardBase:
    """
    Base class for handling request forwarding to another service.
    Provides methods for request validation, logging, and proxying.
    """

    # BASE_URL = None
    # ROUTE_PREFIX = None
    # PROXY = None
    # client: httpx.AsyncClient = None

    validate_host = bool(IP_BLACKLIST or IP_WHITELIST)

    timeout = TIMEOUT

    def __init__(self, base_url: str, route_prefix: str, proxy=None):
        self.BASE_URL = base_url
        self.ROUTE_PREFIX = route_prefix
        self.PROXY = proxy
        self.client: httpx.AsyncClient | None = None
        self.build_client()

    def build_client(self):
        """
        Builds the httpx.AsyncClient object.

        Returns:
            httpx.AsyncClient: The httpx.AsyncClient object.
        """
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL, proxies=self.PROXY, http1=True, http2=False
        )

    @staticmethod
    def validate_request_host(ip):
        """
        Validates the incoming IP address against a whitelist and blacklist.

        Args:
            ip (str): The IP address to validate.

        Raises:
            HTTPException: If the IP is not in the whitelist or if it is in the blacklist.
        """
        if (
            IP_WHITELIST
            and ip not in IP_WHITELIST
            or IP_BLACKLIST
            and ip in IP_BLACKLIST
        ):
            logger.warning(f"IP {ip} is unauthorized")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden Error",
            )

    @staticmethod
    @async_token_rate_limit(token_interval_conf)
    async def aiter_bytes(
        r: httpx.Response, request: Request
    ) -> AsyncGenerator[bytes, Any]:
        """
        Asynchronously iterates through the bytes in the given httpx.Response object
        and yields each chunk.

        Args:
            r (httpx.Response): The httpx.Response object containing the server's response.
            request (Request): The original FastAPI request object.

        Yields:
            bytes: Each chunk of bytes from the server's response.
        """
        async for chunk in r.aiter_bytes():
            yield chunk
        await r.aclose()

    @async_retry(
        max_retries=3,
        delay=0.2,
        backoff=2,
        exceptions=(
            httpx.NetworkError,
            httpx.TimeoutException,
            anyio.EndOfStream,
            Exception,
        ),
        raise_callback_name="build_client",
        raise_handler_name="handle_exception",
    )
    async def try_send(self, client_config: dict, request: Request):
        """
        Asynchronously sends a request to the target service with retry logic.

        Args:
            client_config (dict): Configuration dictionary for creating the client request.
            request (Request): The original FastAPI request object.

        Returns:
            httpx.Response: The httpx.Response object containing the server's response.

        Raises:
            HTTPException: If the request fails after all retry attempts.
        """
        req = self.client.build_request(
            method=request.method,
            url=client_config['url'],
            headers=client_config["headers"],
            content=request.stream(),
            timeout=self.timeout,
        )
        return await self.client.send(req, stream=True)

    def handle_exception(self, e):
        """Handle exceptions and raise HTTPException."""
        if isinstance(e, (httpx.NetworkError, httpx.ConnectTimeout)):
            error_info = (
                f"{type(e)}: {e} | "
                f"Please check if your host can access [{self.BASE_URL}] successfully?"
            )
            status_code = status.HTTP_504_GATEWAY_TIMEOUT

        elif isinstance(e, anyio.EndOfStream):
            error_info = "EndOfStream Error: trying to read from a stream that has been closed from the other end."
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        else:
            error_info = f"{type(e)}: {e}"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        logger.error(f"{error_info}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status_code, detail=error_info)

    def prepare_client(self, request: Request) -> dict:
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
        assert self.BASE_URL and self.ROUTE_PREFIX
        if self.validate_host:
            ip = get_client_ip(request)
            self.validate_request_host(ip)

        _url_path = f"{request.scope.get('root_path')}{request.scope.get('path')}"
        # _url_path = normalize_route(_url_path) # already use middleware instead
        url_path = (
            _url_path[len(self.ROUTE_PREFIX) :]
            if self.ROUTE_PREFIX != '/'
            else _url_path
        )
        url = httpx.URL(path=url_path, query=request.url.query.encode("utf-8"))

        headers = dict(request.headers)
        auth = headers.pop("authorization", "")
        content_type = headers.pop("content-type", "application/json")

        return {
            'auth': auth,
            'headers': {"Content-Type": content_type, "Authorization": auth},
            'url': url,
            'url_path': url_path,
        }

    async def reverse_proxy(self, request: Request):
        """
        Reverse proxies the given request.

        Args:
            request (Request): The request to be reverse proxied.

        Returns:
            StreamingResponse: The response from the reverse proxied server, as a streaming response.
        """
        client_config = self.prepare_client(request)

        r = await self.try_send(client_config, request)

        return StreamingResponse(
            self.aiter_bytes(r, request),
            status_code=r.status_code,
            media_type=r.headers.get("content-type"),
        )


class OpenaiBase(ForwardBase):
    """
    Derived class for handling request forwarding specifically for the OpenAI (Style) API.
    """

    _cycle_api_key = cycle(OPENAI_API_KEY)
    _no_auth_mode = OPENAI_API_KEY != [] and FWD_KEY == []

    def __init__(self, base_url: str, route_prefix: str, proxy=None):
        super().__init__(base_url, route_prefix, proxy)
        if LOG_CHAT or print_chat:
            self.chat_logger = ChatLogger(self.ROUTE_PREFIX)
            self.whisper_logger = WhisperLogger(self.ROUTE_PREFIX)

    def _add_result_log(
        self, byte_list: List[bytes], uid: str, route_path: str, request_method: str
    ):
        """
        Logs the result of the API call.

        Args:
            byte_list (List[bytes]): List of bytes, usually from the API response.
            uid (str): Unique identifier for the request.
            route_path (str): API route path.
            request_method (str): HTTP method (e.g., 'GET', 'POST').

        Raises:
            Suppress all errors.
        """
        try:
            if (LOG_CHAT or print_chat) and request_method == "POST":
                if route_path == CHAT_COMPLETION_ROUTE:
                    target_info = self.chat_logger.parse_iter_bytes(byte_list)
                    if LOG_CHAT:
                        self.chat_logger.log_chat(
                            {target_info["role"]: target_info["content"], "uid": uid}
                        )
                    if print_chat:
                        self.chat_logger.print_chat_info(
                            {target_info["role"]: target_info["content"], "uid": uid}
                        )

                elif route_path.startswith("/v1/audio/"):
                    self.whisper_logger.add_log(b"".join([_ for _ in byte_list]))

                else:
                    ...
        except Exception:
            logger.warning(f"log chat (not) error:\n{traceback.format_exc()}")

    async def _add_payload_log(self, request: Request, url_path: str):
        """
        Asynchronously logs the payload of the API call.

        Args:
            request (Request): The original FastAPI request object.
            url_path (str): The API route path.

        Returns:
            str: The unique identifier (UID) of the payload log, which is used to match the chat result log.

        Raises:
            Suppress all errors.

        """
        uid = None
        if (LOG_CHAT or print_chat) and request.method == "POST":
            try:
                if url_path == CHAT_COMPLETION_ROUTE:
                    chat_info = await self.chat_logger.parse_payload(request)
                    uid = chat_info.get("uid")
                    if chat_info:
                        if LOG_CHAT:
                            self.chat_logger.log_chat(chat_info)
                        if print_chat:
                            self.chat_logger.print_chat_info(chat_info)

                elif url_path.startswith("/v1/audio/"):
                    uid = get_unique_id()

                else:
                    ...

            except Exception as e:
                logger.warning(
                    f"log chat error:\nhost:{request.client.host} method:{request.method}: {traceback.format_exc()}"
                )
        return uid

    @async_token_rate_limit(token_interval_conf)
    async def aiter_bytes(
        self, r: httpx.Response, request: Request, route_path: str, uid: str
    ):
        """
        Asynchronously iterates through the bytes in the given httpx.Response object
        and yields each chunk while also logging the request and response data.

        Args:
            r (httpx.Response): The httpx.Response object.
            request (Request): The original FastAPI request object.
            route_path (str): The API route path.
            uid (str): Unique identifier for the request.

        Returns:
             AsyncGenerator[bytes]: Each chunk of bytes from the server's response.
        """
        byte_list = []
        try:
            async for chunk in r.aiter_bytes():
                byte_list.append(chunk)
                yield chunk

        except httpx.RemoteProtocolError:
            logger.warning(f"RemoteProtocolError:\n{traceback.format_exc()}")

        except Exception:
            logger.warning(
                f"aiter_bytes error:\nhost:{request.client.host} method:{request.method}: {traceback.format_exc()}"
            )

        finally:
            await r.aclose()

        if uid:
            if r.is_success:
                self._add_result_log(byte_list, uid, route_path, request.method)
            else:
                response_info = b"".join([_ for _ in byte_list])
                logger.warning(f'uid: {uid}\n' f'{response_info}')

    async def reverse_proxy(self, request: Request):
        """
        Asynchronously handles reverse proxying the incoming request.

        Args:
            request (Request): The incoming FastAPI request object.

        Returns:
            StreamingResponse: A FastAPI StreamingResponse containing the server's response.
        """
        client_config = self.prepare_client(request)
        url_path = client_config["url_path"]

        # set apikey from preset
        auth, auth_prefix = client_config["auth"], "Bearer "
        if self._no_auth_mode or auth and auth[len(auth_prefix) :] in FWD_KEY:
            client_config["headers"]["Authorization"] = auth_prefix + next(
                self._cycle_api_key
            )

        uid = await self._add_payload_log(request, url_path)

        r = await self.try_send(client_config, request)

        return StreamingResponse(
            self.aiter_bytes(r, request, url_path, uid),
            status_code=r.status_code,
            media_type=r.headers.get("content-type"),
        )
