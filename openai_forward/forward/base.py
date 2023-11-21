import asyncio
import traceback
from asyncio import Queue
from itertools import cycle
from typing import Any, AsyncGenerator

import aiohttp
import anyio
from aiohttp import TCPConnector
from fastapi import HTTPException, Request, status
from flaxkv.pack import encode
from loguru import logger
from starlette.responses import BackgroundTask, Response, StreamingResponse

from ..cache.chat_completions import generate, stream_generate_efficient
from ..cache.database import db_dict
from ..content.openai import ChatLogger, CompletionLogger, WhisperLogger
from ..decorators import async_retry, async_token_rate_limit
from ..settings import *


class GenericForward:
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

    async def build_client(self):
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
    async def send(self, client_config: dict, data=None):

        return await self.client.request(
            method=client_config["method"],
            url=client_config['url'],
            data=data,
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

    def prepare_client(self, request: Request, return_origin_header=False) -> dict:
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

        auth = request.headers.get("Authorization", "")

        if return_origin_header:
            headers = request.headers
        else:
            headers = {
                "content-type": request.headers.get("content-type", "application/json"),
                "authorization": auth,
            }
            for key, value in request.headers.items():
                if key.startswith("openai"):
                    headers[key] = value

        return {
            'auth': auth,
            'headers': headers,
            "method": request.method,
            'url': url,
            'url_path': url_path,
        }

    async def reverse_proxy(self, request: Request):
        assert self.client
        client_config = self.prepare_client(request, return_origin_header=True)

        r = await self.send(client_config, data=await request.body())

        return StreamingResponse(
            self.aiter_bytes(r, request),
            status_code=r.status,
            media_type=r.headers.get("content-type"),
            background=BackgroundTask(r.release),
        )


class OpenaiForward(GenericForward):
    """
    Derived class for handling request forwarding specifically for the OpenAI (Style) API.
    """

    _cycle_api_key = cycle(OPENAI_API_KEY)
    _no_auth_mode = OPENAI_API_KEY != [] and FWD_KEY == []

    def __init__(self, base_url: str, route_prefix: str, proxy=None):
        super().__init__(base_url, route_prefix, proxy)
        if LOG_CHAT or PRINT_CHAT:
            self.chat_logger = ChatLogger(self.ROUTE_PREFIX)
            self.completion_logger = CompletionLogger(self.ROUTE_PREFIX)
            self.whisper_logger = WhisperLogger(self.ROUTE_PREFIX)

    def _handle_result(
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
        result_info = {}

        # If not configured to log or print chat, or the method is not POST, return early
        if not (LOG_CHAT or PRINT_CHAT) or request_method != "POST":
            return result_info

        try:
            # Determine which logger and method to use based on the route_path
            logger_instance = None
            if route_path == CHAT_COMPLETION_ROUTE:
                logger_instance = self.chat_logger
            elif route_path == COMPLETION_ROUTE:
                logger_instance = self.completion_logger
            elif route_path.startswith("/v1/audio/"):
                self.whisper_logger.log_buffer(buffer)
                return result_info

            # If a logger method is determined, parse bytearray and log if necessary
            if logger_instance:
                result_info = logger_instance.parse_bytearray(buffer)
                result_info["uid"] = uid

                if LOG_CHAT:
                    logger_instance.log(result_info)

                if PRINT_CHAT and logger_instance == self.chat_logger:
                    self.chat_logger.print_chat_info(result_info)

        except Exception:
            logger.warning(f"log result error:\n{traceback.format_exc()}")

        return result_info

    async def _handle_payload(self, request: Request, url_path: str):
        """
        Asynchronously logs the payload of the API call.

        Args:
            request (Request): The original FastAPI request object.
            url_path (str): The API route path.

        Returns:
            dict: A dictionary containing parsed messages, model, IP address, UID, and datetime.

        Raises:
            Suppress all errors.

        """
        payload_log_info = {"uid": None}

        if not (LOG_CHAT or PRINT_CHAT) or request.method != "POST":
            payload = await request.body()
            return False, payload_log_info, payload

        try:
            # Determine which logger and method to use based on the url_path
            logger_instance = None
            if url_path == CHAT_COMPLETION_ROUTE:
                logger_instance = self.chat_logger
            elif url_path == COMPLETION_ROUTE:
                logger_instance = self.completion_logger

            # If a logger method is determined, parse payload and log if necessary
            if logger_instance:
                payload_log_info, payload = await logger_instance.parse_payload(request)

                if payload_log_info and LOG_CHAT:
                    logger_instance.log(payload_log_info)

                if (
                    payload_log_info
                    and PRINT_CHAT
                    and logger_instance == self.chat_logger
                ):
                    self.chat_logger.print_chat_info(payload_log_info)
            else:
                payload = await request.body()

        except Exception as e:
            logger.warning(
                f"log chat error:\nhost:{request.client.host} method:{request.method}: {traceback.format_exc()}"
            )
            payload = await request.body()

        valid = True if payload_log_info['uid'] is not None else False
        return valid, payload_log_info, payload

    @staticmethod
    async def read_chunks(r: aiohttp.ClientResponse, queue):
        buffer = bytearray()

        # Efficiency Mode
        if ITER_CHUNK_TYPE == "efficiency":
            # yield all available data as soon as it is received.
            async for chunk in r.content.iter_any():
                buffer.extend(chunk)
                await queue.put(chunk)

        # Precision Mode
        else:
            async for chunk, _ in r.content.iter_chunks():
                buffer.extend(chunk)
                await queue.put(chunk)

        await queue.put(buffer)  # add all information when the stream ends

    @async_token_rate_limit(token_interval_conf)
    async def aiter_bytes(
        self,
        r: aiohttp.ClientResponse,
        request: Request,
        route_path: str,
        uid: str,
        cache_key: str | None = None,
    ):
        """
        Asynchronously iterates through the bytes in the given aiohttp.ClientResponse object
        and yields each chunk while also logging the request and response data.

        Args:
            r (aiohttp.ClientResponse): The aiohttp.ClientResponse object.
            request (Request): The original FastAPI request object.
            route_path (str): The API route path.
            uid (str): Unique identifier for the request.
            cache_key (bytes): The cache key.

        Returns:
             AsyncGenerator[bytes]: Each chunk of bytes from the server's response.
        """

        queue_is_complete = False

        queue = Queue()
        # todo:
        task = asyncio.create_task(self.read_chunks(r, queue))
        try:
            while True:
                chunk = await queue.get()
                if not isinstance(chunk, bytes):
                    queue.task_done()
                    queue_is_complete = True
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
            if r.ok and queue_is_complete:
                target_info = self._handle_result(
                    chunk, uid, route_path, request.method
                )
                if target_info and CACHE_CHAT_COMPLETION and cache_key is not None:
                    cached_value = db_dict.get(cache_key, [])
                    cached_value.append(target_info["assistant"])
                    db_dict[cache_key] = cached_value
            elif chunk is not None:
                logger.warning(
                    f'uid: {uid}\n status: {r.status}\n {chunk.decode("utf-8")}'
                )
            else:
                logger.warning(f'uid: {uid}\n' f'{r.status}')

    def handle_authorization(self, client_config):
        auth, auth_prefix = client_config["auth"], "Bearer "
        if self._no_auth_mode or auth and auth[len(auth_prefix) :] in FWD_KEY:
            auth = auth_prefix + next(self._cycle_api_key)
            client_config["headers"]["Authorization"] = auth
        return auth

    @staticmethod
    def _get_cached_response(payload_info, valid_payload, request):
        """
        Attempts to retrieve a cached response based on the current request's payload information.

        This function constructs a cache key based on various aspects of the request payload,
        checks if the response for this key has been cached, and if so, constructs and returns
        the appropriate cached response.

        Returns:
            Tuple[Union[Response, None], Union[str, None]]:
                - Response (Union[Response, None]): The cached response if available; otherwise, None.
                - cache_key (Union[str, None]): The constructed cache key for the request. None if caching is not applicable.

        Note:
            If a cache hit occurs, the cached response is immediately returned without contacting the external server.
        """
        # todo: refactor this function

        def construct_cache_key():
            elements = [
                payload_info["n"],
                payload_info['messages'],
                payload_info['model'],
                payload_info["max_tokens"],
                payload_info['response_format'],
                payload_info['seed'],
                # payload_info['temperature'],
                payload_info["tools"],
                payload_info["tool_choice"],
            ]

            return encode(elements)

        def get_response_from_cache(key):
            logger.info(f'uid: {payload_info["uid"]} >>>>> [cache hit]')
            cache_values = db_dict[key]
            # todo: handle multiple choices
            cache_value = cache_values[-1]
            if isinstance(cache_value, list):
                text = None
                tool_calls = cache_value
            else:
                text = cache_value
                tool_calls = None

            if payload_info["stream"]:
                return StreamingResponse(
                    stream_generate_efficient(
                        payload_info['model'],
                        text,
                        tool_calls,
                        request,
                    ),
                    status_code=200,
                    media_type="text/event-stream",
                )

            else:
                usage = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                }
                return Response(
                    content=generate(payload_info['model'], text, tool_calls, usage),
                    media_type="application/json",
                )

        if not (CACHE_CHAT_COMPLETION and valid_payload):
            return None, None

        cache_key = construct_cache_key()

        if payload_info['caching'] and cache_key in db_dict:
            return get_response_from_cache(cache_key), cache_key

        return None, cache_key

    async def reverse_proxy(self, request: Request):
        """
        Asynchronously handles reverse proxying the incoming request.

        Args:
            request (Request): The incoming FastAPI request object.

        Returns:
            StreamingResponse: A FastAPI StreamingResponse containing the server's response.
        """
        client_config = self.prepare_client(request, return_origin_header=False)
        url_path = client_config["url_path"]

        self.handle_authorization(client_config)
        valid_payload, payload_info, payload = await self._handle_payload(
            request, url_path
        )
        uid = payload_info["uid"]

        cached_response, cache_key = self._get_cached_response(
            payload_info, valid_payload, request
        )
        if cached_response:
            return cached_response

        r = await self.send(client_config, data=payload)
        return StreamingResponse(
            self.aiter_bytes(r, request, url_path, uid, cache_key),
            status_code=r.status,
            media_type=r.headers.get("content-type"),
        )
