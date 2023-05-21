import os
from itertools import cycle

import httpx
from fastapi import HTTPException, Request, status
from fastapi.responses import StreamingResponse
from loguru import logger
from starlette.background import BackgroundTask

from .config import env2list, print_startup_info, setting_log
from .content.chat import ChatSaver


class OpenaiBase:
    BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com").strip()
    ROUTE_PREFIX = os.environ.get("ROUTE_PREFIX", "").strip()
    _LOG_CHAT = os.environ.get("LOG_CHAT", "False").strip().lower() == "true"
    _openai_api_key_list = env2list("OPENAI_API_KEY", sep=" ")
    _cycle_api_key = cycle(_openai_api_key_list)
    _FWD_KEYS = env2list("FORWARD_KEY", sep=" ")
    _use_forward_key = _openai_api_key_list != [] and _FWD_KEYS != []
    IP_WHITELIST = env2list("IP_WHITELIST", sep=" ")
    IP_BLACKLIST = env2list("IP_BLACKLIST", sep=" ")

    if ROUTE_PREFIX:
        if ROUTE_PREFIX.endswith('/'):
            ROUTE_PREFIX = ROUTE_PREFIX[:-1]
        if not ROUTE_PREFIX.startswith('/'):
            ROUTE_PREFIX = '/' + ROUTE_PREFIX
    timeout = 30

    print_startup_info(
        BASE_URL, ROUTE_PREFIX, _openai_api_key_list, _FWD_KEYS, _LOG_CHAT
    )
    if _LOG_CHAT:
        setting_log(save_file=False)
        chatsaver = ChatSaver(save_interval=10)

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
    async def aiter_bytes(cls, r: httpx.Response, route_path: str):
        bytes_ = b''
        async for chunk in r.aiter_bytes():
            bytes_ += chunk
            yield chunk
        try:
            target_info = cls.chatsaver.parse_bytes_to_content(bytes_, route_path)
            cls.chatsaver.add_chat({target_info['role']: target_info['content']})
        except Exception as e:
            logger.debug(f"log chat (not) error:\n{e=}")

    @classmethod
    async def _reverse_proxy(cls, request: Request):
        client = httpx.AsyncClient(base_url=cls.BASE_URL, http1=True, http2=False)
        url_path = request.url.path
        url_path = url_path[len(cls.ROUTE_PREFIX) :]
        url = httpx.URL(path=url_path, query=request.url.query.encode('utf-8'))
        headers = dict(request.headers)
        auth = headers.pop("authorization", None)
        if auth and str(auth).startswith("Bearer sk-"):
            tmp_headers = {'Authorization': auth}
        elif cls._openai_api_key_list:
            logger.info(f"Use forward key: {cls._use_forward_key}")
            if cls._use_forward_key:
                fk_prefix = "Bearer fk-"
                logger.info(f"current forward key: {auth}")
                if (
                    auth
                    and str(auth).startswith(fk_prefix)
                    and auth[len("Bearer ") :] in cls._FWD_KEYS
                ):
                    auth = "Bearer " + next(cls._cycle_api_key)
                    tmp_headers = {'Authorization': auth}
                else:
                    tmp_headers = {}
            else:
                auth = "Bearer " + next(cls._cycle_api_key)
                tmp_headers = {'Authorization': auth}
        else:
            tmp_headers = {}

        log_chat_completions = False
        if cls._LOG_CHAT and request.method == 'POST':
            try:
                chat_info = await cls.chatsaver.parse_payload_to_content(
                    request, route_path=url_path
                )
                if chat_info:
                    cls.chatsaver.add_chat(chat_info)
                    log_chat_completions = True
            except Exception as e:
                logger.debug(
                    f"log chat error:\n{request.client.host=} {request.method=}: {e}"
                )

        tmp_headers.update({"Content-Type": "application/json"})
        req = client.build_request(
            request.method,
            url,
            headers=tmp_headers,
            content=request.stream(),
            timeout=cls.timeout,
        )
        try:
            r = await client.send(req, stream=True)
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            error_info = (
                f"{type(e)}: {e} | "
                f"Please check if host={request.client.host} can access [{cls.BASE_URL}] successfully?"
            )
            logger.error(error_info)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_info
            )
        except Exception as e:
            error_info = f"{type(e)}: {e}"
            logger.error(error_info)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_info
            )

        aiter_bytes = (
            cls.aiter_bytes(r, url_path) if log_chat_completions else r.aiter_bytes()
        )
        return StreamingResponse(
            aiter_bytes,
            status_code=r.status_code,
            media_type=r.headers.get("content-type"),
            background=BackgroundTask(r.aclose),
        )
