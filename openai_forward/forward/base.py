import asyncio
import traceback
from asyncio import Queue
from itertools import cycle
from typing import Any, AsyncGenerator

import aiohttp
import anyio
from aiohttp import TCPConnector
from fastapi import HTTPException, Request, status
from loguru import logger
from starlette.responses import BackgroundTask, StreamingResponse

from ..content.openai import ChatLogger, WhisperLogger
from ..decorators import async_retry, async_token_rate_limit
from ..helper import get_unique_id
from ..settings import *


class ForwardBase:
    """
    Base class for handling request forwarding to another service.
    Provides methods for request validation, logging, and proxying.
    """

    validate_host = bool(IP_BLACKLIST or IP_WHITELIST)
    timeout = aiohttp.ClientTimeout(connect=TIMEOUT)

    def __init__(self, base_url: str, route_prefix: str, proxy=None):
        self.BASE_URL = base_url
        self.PROXY = proxy
        self.ROUTE_PREFIX = route_prefix
        self.client: aiohttp.ClientSession | None = None
        self.build_client()

    def build_client(self):
        connector = TCPConnector(limit=500, limit_per_host=0, force_close=False)
        self.client = aiohttp.ClientSession(connector=connector, timeout=self.timeout)

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
        r: aiohttp.ClientResponse, request: Request
    ) -> AsyncGenerator[bytes, Any]:
        async for chunk, _ in r.content.iter_chunks():  # yield chunk one by one.
            yield chunk

    @async_retry(
        max_retries=3,
        delay=0.2,
        backoff=2,
        exceptions=(
            aiohttp.ServerTimeoutError,
            aiohttp.ServerConnectionError,
            aiohttp.ServerDisconnectedError,
            asyncio.TimeoutError,
            anyio.EndOfStream,
            RuntimeError,
        ),
        # raise_callback_name="build_client",
        raise_handler_name="handle_exception",
    )
    async def try_send(self, client_config: dict, request: Request):
        return await self.client.request(
            method=request.method,
            url=client_config['url'],
            data=await request.body(),
            headers=client_config["headers"],
            proxy=self.PROXY,
        )

    def handle_exception(self, e):
        if isinstance(
            e,
            (
                asyncio.TimeoutError,
                aiohttp.ServerConnectionError,
                aiohttp.ServerDisconnectedError,
                aiohttp.ServerTimeoutError,
            ),
        ):
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
        assert self.BASE_URL and self.ROUTE_PREFIX
        if self.validate_host:
            ip = get_client_ip(request)
            self.validate_request_host(ip)

        _url_path = f"{request.scope.get('root_path')}{request.scope.get('path')}"
        url_path = (
            _url_path[len(self.ROUTE_PREFIX) :]
            if self.ROUTE_PREFIX != '/'
            else _url_path
        )
        url = f"{self.BASE_URL}{url_path}?{request.url.query}"

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
        client_config = self.prepare_client(request)

        r = await self.try_send(client_config, request)

        return StreamingResponse(
            self.aiter_bytes(r, request),
            status_code=r.status,
            media_type=r.headers.get("content-type"),
            background=BackgroundTask(r.release),
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
        self, buffer: bytearray, uid: str, route_path: str, request_method: str
    ):
        """
        Logs the result of the API call.

        Args:
            buffer (bytearray): List of bytes, usually from the API response.
            uid (str): Unique identifier for the request.
            route_path (str): API route path.
            request_method (str): HTTP method (e.g., 'GET', 'POST').

        Raises:
            Suppress all errors.
        """
        try:
            if (LOG_CHAT or print_chat) and request_method == "POST":
                if route_path == CHAT_COMPLETION_ROUTE:
                    target_info = self.chat_logger.parse_bytearray(buffer)
                    if LOG_CHAT:
                        self.chat_logger.log_chat(
                            {target_info["role"]: target_info["content"], "uid": uid}
                        )
                    if print_chat:
                        self.chat_logger.print_chat_info(
                            {target_info["role"]: target_info["content"], "uid": uid}
                        )

                elif route_path.startswith("/v1/audio/"):
                    self.whisper_logger.add_log(buffer)

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

    @staticmethod
    async def read_chunks(r: aiohttp.ClientResponse, queue):
        buffer = bytearray()
        async for chunk in r.content.iter_any():  # yield all available data as soon as it is received.
            buffer.extend(chunk)
            await queue.put(chunk)

        await queue.put(buffer)  # add all information when the stream ends

    @async_token_rate_limit(token_interval_conf)
    async def aiter_bytes(
        self, r: aiohttp.ClientResponse, request: Request, route_path: str, uid: str
    ):
        """
        Asynchronously iterates through the bytes in the given aiohttp.ClientResponse object
        and yields each chunk while also logging the request and response data.

        Args:
            r (aiohttp.ClientResponse): The aiohttp.ClientResponse object.
            request (Request): The original FastAPI request object.
            route_path (str): The API route path.
            uid (str): Unique identifier for the request.

        Returns:
             AsyncGenerator[bytes]: Each chunk of bytes from the server's response.
        """
        queue = Queue()
        is_complete = False

        # todo:
        task = asyncio.create_task(self.read_chunks(r, queue))
        try:
            while True:
                chunk = await queue.get()
                if not isinstance(chunk, bytes):
                    queue.task_done()
                    is_complete = True
                    break
                yield chunk
        except Exception:
            logger.warning(
                f"aiter_bytes error:\nhost:{request.client.host} method:{request.method}: {traceback.format_exc()}"
            )
        finally:
            if not task.done():
                task.cancel()
            r.release()
        if uid:
            if r.ok and is_complete:
                self._add_result_log(chunk, uid, route_path, request.method)
            elif chunk is not None:
                logger.warning(
                    f'uid: {uid}\n status: {r.status}\n {chunk.decode("utf-8")}'
                )
            else:
                logger.warning(f'uid: {uid}\n' f'{r.status}')

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
            status_code=r.status,
            media_type=r.headers.get("content-type"),
        )
