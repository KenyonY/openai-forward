import os
from loguru import logger

import httpx
from fastapi import HTTPException, Request, status
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from openai_forward.routers.schemas import AnthropicChatCompletion
from openai_forward.tool import env2list

class AnthropicBase:
    BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").strip()
    ROUTE_PREFIX = os.environ.get("ROUTE_PREFIX", "").strip()
    IP_WHITELIST = env2list("IP_WHITELIST", sep=" ")
    IP_BLACKLIST = env2list("IP_BLACKLIST", sep=" ")

    if ROUTE_PREFIX:
        if ROUTE_PREFIX.endswith("/"):
            ROUTE_PREFIX = ROUTE_PREFIX[:-1]
        if not ROUTE_PREFIX.startswith("/"):
            ROUTE_PREFIX = "/" + ROUTE_PREFIX
    timeout = 600

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
        auth_headers_dict = {"Content-Type": content_type, "Authorization": auth,
                             "accept": "application/json", "anthropic-version": "2023-06-01",
                             "x-api-key": headers.pop("x-api-key", "")}

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


class Anthropic(AnthropicBase):
    def __init__(self):
        if self.IP_BLACKLIST or self.IP_WHITELIST:
            self.validate_host = True
        else:
            self.validate_host = False

    async def reverse_proxy(self, request: Request):
        if self.validate_host:
            self.validate_request_host(request.client.host)
        return await self._reverse_proxy(request)

    async def v1_chat_completions(self, data: AnthropicChatCompletion, request: Request):
        ...
