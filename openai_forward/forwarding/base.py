import os
from itertools import cycle

import httpx
from fastapi import HTTPException, Request, status
from fastapi.responses import StreamingResponse
from loguru import logger
from starlette.background import BackgroundTask

from ..config import setting_log
from ..content import ChatSaver, ExtraForwardingSaver, WhisperSaver
from ..tool import env2list, format_route_prefix

BASE_URL_EXTRA = env2list("BASE_URL_EXTRA", sep=" ")
ROUTE_PREFIX_EXTRA = [
    format_route_prefix(i) for i in env2list("ROUTE_PREFIX_EXTRA", sep=" ")
]


class ForwardingBase:
    BASE_URL = None
    ROUTE_PREFIX = None
    IP_WHITELIST = env2list("IP_WHITELIST", sep=" ")
    IP_BLACKLIST = env2list("IP_BLACKLIST", sep=" ")

    timeout = 600

    _LOG_CHAT = os.environ.get("LOG_CHAT", "False").strip().lower() == "true"
    if _LOG_CHAT:
        setting_log(save_file=False)
        extrasaver = ExtraForwardingSaver()

    def validate_request_host(self, ip):
        if self.IP_WHITELIST and ip not in self.IP_WHITELIST:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden, ip={ip} not in whitelist!",
            )
        if self.IP_BLACKLIST and ip in self.IP_BLACKLIST:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden, ip={ip} in blacklist!",
            )

    @classmethod
    async def aiter_bytes(cls, r: httpx.Response):
        bytes_ = b""
        async for chunk in r.aiter_bytes():
            bytes_ += chunk
            yield chunk
        cls.extrasaver.add_log(bytes_)

    async def send(
        self, client: httpx.AsyncClient, req: httpx.Request, request: Request
    ):
        try:
            r = await client.send(req, stream=True)
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
        client = httpx.AsyncClient(base_url=self.BASE_URL, http1=True, http2=False)
        url_path = request.url.path
        url_path = url_path[len(self.ROUTE_PREFIX) :]
        url = httpx.URL(path=url_path, query=request.url.query.encode("utf-8"))
        headers = dict(request.headers)
        auth = headers.pop("authorization", "")
        content_type = headers.pop("content-type", "application/json")
        auth_headers_dict = {"Content-Type": content_type, "Authorization": auth}
        req_config = {
            'auth': auth,
            'headers': auth_headers_dict,
            'url': url,
            'url_path': url_path,
        }
        return client, url, req_config

    async def _reverse_proxy(self, request: Request):
        client, url, req_config = self.prepare_client(request)

        req = client.build_request(
            request.method,
            url,
            headers=req_config["headers"],
            content=request.stream(),
            timeout=self.timeout,
        )
        r = await self.send(client, req, request)

        return StreamingResponse(
            self.aiter_bytes(r),
            status_code=r.status_code,
            media_type=r.headers.get("content-type"),
            background=BackgroundTask(r.aclose),
        )


class OpenaiBase(ForwardingBase):
    BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com").strip()
    ROUTE_PREFIX = os.environ.get("OPENAI_ROUTE_PREFIX", "").strip()
    ROUTE_PREFIX = format_route_prefix(ROUTE_PREFIX)
    _openai_api_key_list = env2list("OPENAI_API_KEY", sep=" ")
    _cycle_api_key = cycle(_openai_api_key_list)
    _FWD_KEYS = set(env2list("FORWARD_KEY", sep=" "))
    _no_auth_mode = _openai_api_key_list != [] and _FWD_KEYS == set()
    _LOG_CHAT = os.environ.get("LOG_CHAT", "False").strip().lower() == "true"

    if _LOG_CHAT:
        setting_log(save_file=False)
        chatsaver = ChatSaver()
        whispersaver = WhisperSaver()

    async def aiter_bytes(self, r: httpx.Response, route_path: str, uid: str):
        bytes_ = b""
        async for chunk in r.aiter_bytes():
            bytes_ += chunk
            yield chunk
        try:
            if route_path == "/v1/chat/completions":
                target_info = self.chatsaver.parse_bytes_to_content(bytes_, route_path)
                self.chatsaver.add_chat(
                    {target_info["role"]: target_info["content"], "uid": uid}
                )
            elif route_path.startswith("/v1/audio/"):
                self.whispersaver.add_log(bytes_)
        except Exception as e:
            logger.debug(f"log chat (not) error:\n{e=}")

    async def _reverse_proxy(self, request: Request):
        client, url, req_config = self.prepare_client(request)
        auth_prefix = "Bearer "
        auth = req_config["auth"]
        auth_headers_dict = req_config["headers"]
        url_path = req_config["url_path"]
        if self._no_auth_mode or auth and auth[len(auth_prefix) :] in self._FWD_KEYS:
            auth = auth_prefix + next(self._cycle_api_key)
            auth_headers_dict["Authorization"] = auth

        if_log = False
        uid = None
        if self._LOG_CHAT and request.method == "POST":
            try:
                if url_path.startswith("/v1/audio/"):
                    if_log = True
                else:
                    chat_info = await self.chatsaver.parse_payload_to_content(
                        request, route_path=url_path
                    )
                    if chat_info:
                        self.chatsaver.add_chat(chat_info)
                        uid = chat_info.get("uid")
                        if_log = True
            except Exception as e:
                logger.debug(
                    f"log chat error:\n{request.client.host=} {request.method=}: {e}"
                )

        req = client.build_request(
            request.method,
            url,
            headers=auth_headers_dict,
            content=request.stream(),
            timeout=self.timeout,
        )
        r = await self.send(client, req, request)

        aiter_bytes = self.aiter_bytes(r, url_path, uid) if if_log else r.aiter_bytes()
        return StreamingResponse(
            aiter_bytes,
            status_code=r.status_code,
            media_type=r.headers.get("content-type"),
            background=BackgroundTask(r.aclose),
        )
