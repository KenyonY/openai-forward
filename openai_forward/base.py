import os
from itertools import cycle

import httpx
from fastapi import HTTPException, Request, status
from fastapi.responses import StreamingResponse
from loguru import logger
from starlette.background import BackgroundTask

from .config import print_startup_info
from .tool import env2list


class OpenaiBase:
    BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com").strip()
    ROUTE_PREFIX = os.environ.get("ROUTE_PREFIX", "").strip()
    _openai_api_key_list = env2list("OPENAI_API_KEY", sep=" ")
    _cycle_api_key = cycle(_openai_api_key_list)
    _FWD_KEYS = set(env2list("FORWARD_KEY", sep=" "))
    _no_auth_mode = _openai_api_key_list != [] and _FWD_KEYS == set()
    IP_WHITELIST = env2list("IP_WHITELIST", sep=" ")
    IP_BLACKLIST = env2list("IP_BLACKLIST", sep=" ")

    timeout = 600

    print_startup_info(
        BASE_URL, ROUTE_PREFIX, _openai_api_key_list, _no_auth_mode, False
    )

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
    async def _reverse_proxy(cls, request: Request):
        client = httpx.AsyncClient(base_url=cls.BASE_URL, http1=True, http2=False)
        url_path = request.url.path
        url_path = url_path[len(cls.ROUTE_PREFIX) :]
        url = httpx.URL(path=url_path, query=request.url.query.encode("utf-8"))
        headers = dict(request.headers)
        auth = headers.pop("authorization", "")
        content_type = headers.pop("content-type", "application/json")
        auth_headers_dict = {"Content-Type": content_type, "Authorization": auth}
        auth_prefix = "Bearer "
        if cls._no_auth_mode or auth and auth[len(auth_prefix) :] in cls._FWD_KEYS:
            auth = auth_prefix + next(cls._cycle_api_key)
            auth_headers_dict["Authorization"] = auth

        req = client.build_request(
            request.method,
            url,
            headers=auth_headers_dict,
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
            logger.exception(f"{type(e)}:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e
            )

        aiter_bytes = r.aiter_bytes()
        return StreamingResponse(
            aiter_bytes,
            status_code=r.status_code,
            media_type=r.headers.get("content-type"),
            background=BackgroundTask(r.aclose),
        )
