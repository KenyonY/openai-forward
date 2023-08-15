import time
import traceback
import uuid
from itertools import cycle
from typing import Any, AsyncGenerator, List

import httpx
from fastapi import HTTPException, Request, status
from fastapi.responses import StreamingResponse
from loguru import logger

from ..content import ChatSaver, WhisperSaver
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

    async def aiter_bytes(
        self, r: httpx.Response, **kwargs
    ) -> AsyncGenerator[bytes, Any]:
        async for chunk in r.aiter_bytes():
            yield chunk
        await r.aclose()

    async def try_send(self, client_config: dict, request: Request):
        try:
            req = self.client.build_request(
                method=request.method,
                url=client_config['url'],
                headers=client_config["headers"],
                content=request.stream(),
                timeout=self.timeout,
            )

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

        _url_path = request.url.path
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
        try:
            if LOG_CHAT and request_method == "POST":
                if route_path == "/v1/chat/completions":
                    target_info = self.chatsaver.parse_iter_bytes(byte_list)
                    self.chatsaver.log_chat(
                        {target_info["role"]: target_info["content"], "uid": uid}
                    )

                elif route_path.startswith("/v1/audio/"):
                    self.whispersaver.add_log(b"".join([_ for _ in byte_list]))

                else:
                    ...
        except Exception as e:
            logger.warning(f"log chat (not) error:\n{traceback.format_exc()}")

    async def _add_payload_log(self, request: Request, url_path: str):
        uid = None
        if LOG_CHAT and request.method == "POST":
            try:
                if url_path == "/v1/chat/completions":
                    chat_info = await self.chatsaver.parse_payload(request)
                    uid = chat_info.get("uid")
                    if chat_info:
                        self.chatsaver.log_chat(chat_info)

                elif url_path.startswith("/v1/audio/"):
                    uid = uuid.uuid4().__str__()

                else:
                    ...

            except Exception as e:
                logger.warning(
                    f"log chat error:\nhost:{request.client.host} method:{request.method}: {traceback.format_exc()}"
                )
        return uid

    async def aiter_bytes(
        self, r: httpx.Response, request: Request, route_path: str, uid: str
    ):
        byte_list = []
        start_time = time.perf_counter()
        idx = 0
        async for chunk in r.aiter_bytes():
            idx += 1
            byte_list.append(chunk)
            # print(f"{chunk=}")
            if TOKEN_INTERVAL > 0:
                current_time = time.perf_counter()
                delta = current_time - start_time
                sleep_time = TOKEN_INTERVAL - delta
                print(f"{delta=} {sleep_time=}")
                if sleep_time > 0:
                    time.sleep(sleep_time)
                start_time = time.perf_counter()
            yield chunk

        await r.aclose()

        if uid:
            if r.is_success:
                self._add_result_log(byte_list, uid, route_path, request.method)
            else:
                response_info = b"".join([_ for _ in byte_list])
                logger.warning(f'uid: {uid}\n' f'{response_info}')

    async def reverse_proxy(self, request: Request):
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
