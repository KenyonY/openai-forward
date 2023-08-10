import traceback
from itertools import cycle
from typing import Any, AsyncGenerator

import httpx
from fastapi import HTTPException, Request, status
from fastapi.responses import StreamingResponse
from loguru import logger

from ..content import ChatSaver, ExtraForwardingSaver, WhisperSaver
from .settings import *


class ForwardingBase:
    BASE_URL = None
    ROUTE_PREFIX = None
    client: httpx.AsyncClient = None
    if IP_BLACKLIST or IP_WHITELIST:
        validate_host = True
    else:
        validate_host = False

    timeout = 600

    if LOG_CHAT:
        extrasaver = ExtraForwardingSaver()

    @staticmethod
    def validate_request_host(ip):
        if IP_WHITELIST and ip not in IP_WHITELIST:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden, ip={ip} not in whitelist!",
            )
        if IP_BLACKLIST and ip in IP_BLACKLIST:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden, ip={ip} in blacklist!",
            )

    @classmethod
    async def aiter_bytes(
        cls, r: httpx.Response, **kwargs
    ) -> AsyncGenerator[bytes, Any]:
        bytes_ = b""
        async for chunk in r.aiter_bytes():
            bytes_ += chunk
            yield chunk
        cls.extrasaver.add_log(bytes_)

    async def try_send(self, req: httpx.Request, request: Request):
        try:
            r = await self.client.send(req, stream=True)
            return r
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            error_info = (
                f"{type(e)}: {e} | "
                f"Please check if host={request.client.host} can access [{self.BASE_URL}] successfully?"
            )
            logger.error(error_info)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_info
            )
        except Exception as e:
            logger.exception(f"{type(e)}:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e
            )

    def prepare_client(self, request: Request):
        assert self.BASE_URL is not None
        assert self.ROUTE_PREFIX is not None
        if self.validate_host:
            ip = request.headers.get("x-forwarded-for") or ""
            self.validate_request_host(ip)

        url_path = request.url.path
        prefix_index = 0 if self.ROUTE_PREFIX == '/' else len(self.ROUTE_PREFIX)

        route_path = url_path[prefix_index:]
        url = httpx.URL(path=route_path, query=request.url.query.encode("utf-8"))
        headers = dict(request.headers)
        auth = headers.pop("authorization", "")
        content_type = headers.pop("content-type", "application/json")
        auth_headers_dict = {"Content-Type": content_type, "Authorization": auth}
        client_config = {
            'auth': auth,
            'headers': auth_headers_dict,
            'url': url,
            'url_path': route_path,
        }

        return client_config

    async def reverse_proxy(self, request: Request):
        assert self.client is not None
        client_config = self.prepare_client(request)

        req = self.client.build_request(
            request.method,
            client_config['url'],
            headers=client_config["headers"],
            content=request.stream(),
            timeout=self.timeout,
        )
        r = await self.try_send(req, request)

        return StreamingResponse(
            self.aiter_bytes(r),
            status_code=r.status_code,
            media_type=r.headers.get("content-type"),
        )


class OpenaiBase(ForwardingBase):
    _cycle_api_key = cycle(OPENAI_API_KEY)
    _no_auth_mode = OPENAI_API_KEY != [] and FWD_KEY == set()

    if LOG_CHAT:
        chatsaver = ChatSaver()
        whispersaver = WhisperSaver()

    async def aiter_bytes(
        self, r: httpx.Response, request: Request, route_path: str, uid: str
    ):
        byte_list = []
        async for chunk in r.aiter_bytes():
            byte_list.append(chunk)
            yield chunk
        await r.aclose()
        try:
            if LOG_CHAT and request.method == "POST":
                if route_path == "/v1/chat/completions":
                    target_info = self.chatsaver.parse_iter_bytes(byte_list)
                    self.chatsaver.add_chat(
                        {target_info["role"]: target_info["content"], "uid": uid}
                    )
                elif route_path.startswith("/v1/audio/"):
                    self.whispersaver.add_log(b"".join([_ for _ in byte_list]))
        except Exception as e:
            logger.debug(f"log chat (not) error:\n{traceback.format_exc()}")

    async def reverse_proxy(self, request: Request):
        client_config = self.prepare_client(request)
        auth_prefix = "Bearer "
        auth = client_config["auth"]
        auth_headers_dict = client_config["headers"]
        url_path = client_config["url_path"]
        if self._no_auth_mode or auth and auth[len(auth_prefix) :] in FWD_KEY:
            auth = auth_prefix + next(self._cycle_api_key)
            auth_headers_dict["Authorization"] = auth

        uid = None
        if LOG_CHAT and request.method == "POST":
            try:
                if url_path == "/v1/chat/completions":
                    chat_info = await self.chatsaver.parse_payload(request)
                    if chat_info:
                        self.chatsaver.add_chat(chat_info)
                        uid = chat_info.get("uid")
            except Exception as e:
                logger.debug(
                    f"log chat error:\n{request.client.host=} {request.method=}: {traceback.format_exc()}"
                )

        req = self.client.build_request(
            request.method,
            client_config['url'],
            headers=auth_headers_dict,
            content=request.stream(),
            timeout=self.timeout,
        )
        r = await self.try_send(req, request)
        aiter_bytes = self.aiter_bytes(r, request, url_path, uid)
        return StreamingResponse(
            aiter_bytes,
            status_code=r.status_code,
            media_type=r.headers.get("content-type"),
        )
