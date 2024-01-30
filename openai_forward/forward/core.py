from __future__ import annotations

import asyncio
import traceback
from asyncio import Queue
from itertools import cycle
from typing import Any, AsyncGenerator, Iterable

import aiohttp
import anyio
from aiohttp import TCPConnector
from fastapi import HTTPException, Request, status
from loguru import logger
from starlette.responses import BackgroundTask, StreamingResponse

from ..cache import (
    cache_generic_response,
    cache_response,
    get_cached_generic_response,
    get_cached_response,
)
from ..content.openai import (
    ChatLogger,
    CompletionLogger,
    EmbeddingLogger,
    WhisperLogger,
)
from ..decorators import async_retry, async_token_rate_limit
from ..helper import InfiniteSet
from ..settings import *

# from beartype import beartype


class GenericForward:
    """
    Base class for handling request forwarding to another service.
    Provides methods for request validation, logging, and proxying.
    """

    validate_host = bool(IP_BLACKLIST or IP_WHITELIST)
    timeout = aiohttp.ClientTimeout(connect=TIMEOUT)

    def __init__(self, base_url: str, route_prefix: str, proxy=None):
        """
        Args:
            base_url (str): The base URL to which requests will be forwarded.
            route_prefix (str): The prefix of the route.
            proxy (str, optional): The proxy to use for the requests. Defaults to None.
        """
        self.BASE_URL = base_url
        self.PROXY = proxy
        self.ROUTE_PREFIX = route_prefix
        self.client: aiohttp.ClientSession | None = None

    async def build_client(self):
        """
        Asynchronously build the client for making requests.
        """
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
        r: aiohttp.ClientResponse,
        request: Request,
        route_path: str,
        cache_key: str | None = None,
    ) -> AsyncGenerator[bytes, Any]:
        """
        Asynchronously iterates through the bytes in the given aiohttp.ClientResponse object
        and yields each chunk while also caching the response if necessary.

        Args:
            r (aiohttp.ClientResponse): The aiohttp.ClientResponse object.
            request (Request): The original FastAPI request object.
            route_path (str): The API route path.
            cache_key (str | None): The cache key. Defaults to None.

        Returns:
            AsyncGenerator[bytes, Any]: Each chunk of bytes from the server's response.
        """
        chunk_list = []
        cache = True if route_path in CACHE_ROUTE_SET else False

        async for chunk, _ in r.content.iter_chunks():  # yield chunk one by one.
            if cache:
                chunk_list.append(chunk)
            yield chunk

        if r.ok and cache and cache_key:
            cache_generic_response(cache_key, chunk_list, route_path)

        # Only log non-stream response:
        if len(chunk_list) == 1 and LOG_GENERAL:
            logger.debug(f"result: {chunk_list[0]}")

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
        """
        Asynchronously send the request and return the response.

        Args:
            client_config (dict): The configuration for the client.
            data (Any, optional): The data to send in the request. Defaults to None.

        Returns:
            aiohttp.ClientResponse: The response from the server.
        """

        return await self.client.request(
            method=client_config["method"],
            url=client_config['url'],
            data=data,
            headers=client_config["headers"],
            proxy=self.PROXY,
        )

    def handle_exception(self, e):
        """
        Handle exceptions that occur during the request.

        Args:
            e (Exception): The exception that occurred.

        Raises:
            HTTPException: An HTTPException with the appropriate status code and detail.
        """
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
        """
        Prepare the client for making a request.

        Args:
            request (Request): The original FastAPI request object.
            return_origin_header (bool, optional): Whether to return the original header. Defaults to False.

        Returns:
            dict: The configuration for the client.
        """
        assert self.BASE_URL and self.ROUTE_PREFIX
        if self.validate_host:
            ip = get_client_ip(request)
            self.validate_request_host(ip)

        _url_path = f"{request.scope.get('root_path')}{request.scope.get('path')}"
        route_path = (
            _url_path[len(self.ROUTE_PREFIX) :]
            if self.ROUTE_PREFIX != '/'
            else _url_path
        )
        if request.url.query:
            url = f"{self.BASE_URL}{route_path}?{request.url.query}"
        else:
            url = f"{self.BASE_URL}{route_path}"

        auth = request.headers.get("Authorization", "")

        if return_origin_header:
            headers = dict(request.headers)
            headers_to_remove = [
                "host",
                "cookie",
                # "user-agent",
                # "connection",
                # "cache-control", "upgrade-insecure-requests",
                # "sec-fetch-site", "sec-fetch-mode", "sec-fetch-user", "sec-fetch-dest",
                "accept-encoding",
                "accept-language",
            ]
            for key in headers_to_remove:
                headers.pop(key, None)

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
            'route_path': route_path,
        }

    async def reverse_proxy(self, request: Request):
        """
        Asynchronously handle reverse proxying the incoming request.

        Args:
            request (Request): The incoming FastAPI request object.

        Returns:
            StreamingResponse: A FastAPI StreamingResponse containing the server's response.
        """
        assert self.client
        data = await request.body()

        if LOG_GENERAL:
            logger.debug(f"payload: {data}")
        client_config = self.prepare_client(request, return_origin_header=True)

        route_path = client_config["route_path"]

        cached_response, cache_key = get_cached_generic_response(
            data, request, route_path
        )

        if cached_response:
            return cached_response

        r = await self.send(client_config, data=data)

        return StreamingResponse(
            self.aiter_bytes(r, request, cache_key),
            status_code=r.status,
            media_type=r.headers.get("content-type"),
            background=BackgroundTask(r.release),
        )


class OpenaiForward(GenericForward):
    """
    Derived class for handling request forwarding specifically for the OpenAI (Style) API.
    Inherits from the GenericForward class and adds specific functionality for the OpenAI API.
    """

    _fk_to_level = FWD_KEY
    _sk_to_levels = OPENAI_API_KEY
    _level_to_model_set = {level: set(models) for level, models in LEVEL_MODELS.items()}

    _zero_level_model_set = InfiniteSet()

    _level_to_sks = {}
    for sk, levels in _sk_to_levels.items():
        for level in levels:
            _level_to_sks[level] = _level_to_sks.get(level, []) + [sk]

    _level_to_sk = {}
    for level, sks in _level_to_sks.items():
        _level_to_sk[level] = cycle(sks)

    def __init__(self, base_url: str, route_prefix: str, proxy=None):
        """
        Initialize the OpenaiForward class.

        Args:
            base_url (str): The base URL to which requests will be forwarded.
            route_prefix (str): The prefix of the route.
            proxy (str, optional): The proxy to use for the requests. Defaults to None.
        """
        super().__init__(base_url, route_prefix, proxy)
        if LOG_OPENAI or PRINT_CHAT:
            self.chat_logger = ChatLogger(self.ROUTE_PREFIX)
            self.completion_logger = CompletionLogger(self.ROUTE_PREFIX)
            self.whisper_logger = WhisperLogger(self.ROUTE_PREFIX)
            self.embedding_logger = EmbeddingLogger(self.ROUTE_PREFIX)

    @classmethod
    def fk_to_sk(cls, forward_key: str):
        """
        Convert a forward key to a secret key.

        Args:
            forward_key (str): The forward key to convert.

        Returns:
            str: The corresponding secret key, if it exists. Otherwise, None.
        """
        level = cls._fk_to_level.get(forward_key)
        if level is not None:
            sk = cls._level_to_sk.get(level)
            if sk:
                return next(sk), level
        return None, level

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
        if not (LOG_OPENAI or PRINT_CHAT) or request_method != "POST":
            return result_info

        try:
            logger_instance = self.get_logger(route_path)
            if logger_instance:
                result_info = logger_instance.parse_bytearray(buffer)
                result_info["uid"] = uid

                if LOG_OPENAI:
                    if logger_instance.webui:
                        logger_instance.q.put({"uid": uid, "result": result_info})
                    logger_instance.log_result(result_info)

                # todo: Deprecated soon
                if PRINT_CHAT and logger_instance == self.chat_logger:
                    self.chat_logger.print_chat_info(result_info)

        except Exception:
            logger.warning(f"log result error:\n{traceback.format_exc()}")

        return result_info

    def get_logger(self, route_path: str):
        """
        Get which logger to use based on the route_path
        """
        if LOG_OPENAI:
            if route_path == CHAT_COMPLETION_ROUTE:
                return self.chat_logger
            elif route_path == COMPLETION_ROUTE:
                return self.completion_logger
            elif route_path == EMBEDDING_ROUTE:
                return self.embedding_logger
        return None

    async def _handle_payload(self, request: Request, route_path: str, model_set):
        """
        Asynchronously logs the payload of the API call.

        Args:
            request (Request): The original FastAPI request object.
            route_path (str): The API route path.
            model_set (set): The set of models that can be accessed.

        Returns:
            valid, payload_info, payload

        Raises:
            Suppress all errors.

        """
        payload_log_info = {"uid": None}

        payload = await request.body()

        if not (LOG_OPENAI or PRINT_CHAT) or request.method != "POST":
            return False, payload_log_info, payload

        try:

            logger_instance = self.get_logger(route_path)
            # If a logger method is determined, parse payload and log if necessary
            if logger_instance:
                payload_log_info, payload = logger_instance.parse_payload(
                    request, payload
                )

                if payload_log_info and LOG_OPENAI:
                    logger_instance.logger.debug(payload_log_info)

                if (
                    payload_log_info
                    and PRINT_CHAT
                    and logger_instance == self.chat_logger
                ):
                    self.chat_logger.print_chat_info(payload_log_info)
            else:
                ...

        except Exception as e:
            logger.warning(
                f"log chat error:\nhost:{request.client.host} method:{request.method}: {traceback.format_exc()}"
            )

        valid = True if payload_log_info['uid'] is not None else False

        if valid:
            if payload_log_info["model"] not in model_set:
                print(f"{model_set=}")
                logger.warning(
                    f"[Auth Warning] model: {payload_log_info['model']} is not allowed"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"model: {payload_log_info['model']} is not allowed",
                )

        return valid, payload_log_info, payload

    @staticmethod
    async def read_chunks(r: aiohttp.ClientResponse, queue):
        """
        Read chunks of data from the response.

        Args:
            r (aiohttp.ClientResponse): The aiohttp.ClientResponse object.
            queue (Queue): The queue to put the chunks into.

        """
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
        chunk_list = []
        try:
            while True:
                chunk = await queue.get()
                if not isinstance(chunk, bytes):
                    queue.task_done()
                    queue_is_complete = True
                    break
                if CACHE_OPENAI:
                    chunk_list.append(chunk)
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
                if CACHE_OPENAI:
                    cache_response(cache_key, target_info, route_path, chunk_list)

            elif chunk is not None:
                logger.warning(
                    f'uid: {uid}\n status: {r.status}\n {chunk.decode("utf-8")}'
                )
            else:
                logger.warning(f'uid: {uid}\n' f'{r.status}')

    def handle_authorization(self, client_config):
        """
        Handle the authorization for the client.

        Args:
            client_config (dict): The configuration for the client.

        Returns:
            str: The authorization string.
            set: The set of models can be accessed.
        """
        auth, auth_prefix = client_config["auth"], "Bearer "
        model_set = self._zero_level_model_set

        if auth:
            fk = auth[len(auth_prefix) :]
            if fk in FWD_KEY:
                sk, level = self.fk_to_sk(fk)
                assert level is not None
                if level != 0:
                    model_set = self._level_to_model_set[level]
                if sk:
                    auth = auth_prefix + sk
                    client_config["headers"]["Authorization"] = auth
        return auth, model_set

    async def reverse_proxy(self, request: Request):
        """
        Asynchronously handles reverse proxying the incoming request.

        Args:
            request (Request): The incoming FastAPI request object.

        Returns:
            StreamingResponse: A FastAPI StreamingResponse containing the server's response.
        """
        client_config = self.prepare_client(request, return_origin_header=False)
        route_path = client_config["route_path"]

        _, model_set = self.handle_authorization(client_config)
        valid_payload, payload_info, payload = await self._handle_payload(
            request, route_path, model_set
        )
        uid = payload_info["uid"]

        cached_response, cache_key = get_cached_response(
            payload,
            payload_info,
            valid_payload,
            route_path,
            request,
            logger_instance=self.get_logger(route_path),
        )

        if cached_response:
            return cached_response

        r = await self.send(client_config, data=payload)
        return StreamingResponse(
            self.aiter_bytes(r, request, route_path, uid, cache_key),
            status_code=r.status,
            media_type=r.headers.get("content-type"),
        )
