from fastapi import Request, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger
import httpx
from starlette.background import BackgroundTask
import os
from itertools import cycle
from .content.chat import parse_chat_completions, ChatSaver
from .config import env2list


class OpenaiBase:
    _base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com").strip()
    _LOG_CHAT = os.environ.get("LOG_CHAT", "False").lower() == "true"
    _ROUTE_PREFIX = os.environ.get("ROUTE_PREFIX", "").strip()
    _default_api_key_list = env2list("OPENAI_API_KEY", sep=" ")
    _cycle_api_key = cycle(_default_api_key_list)
    IP_WHITELIST = env2list("IP_WHITELIST", sep=" ")
    IP_BLACKLIST = env2list("IP_BLACKLIST", sep=" ")

    if _ROUTE_PREFIX:
        if _ROUTE_PREFIX.endswith('/'):
            _ROUTE_PREFIX = _ROUTE_PREFIX[:-1]
        if not _ROUTE_PREFIX.startswith('/'):
            _ROUTE_PREFIX = '/' + _ROUTE_PREFIX
    timeout = 30
    chatsaver = ChatSaver(save_interval=10)

    def validate_request_host(self, ip):
        if self.IP_WHITELIST and ip not in self.IP_WHITELIST:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Forbidden, ip={ip} not in whitelist!")
        if self.IP_BLACKLIST and ip in self.IP_BLACKLIST:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Forbidden, ip={ip} in blacklist!")

    @classmethod
    def log_chat_completions(cls, bytes_: bytes):
        target_info = parse_chat_completions(bytes_)
        cls.chatsaver.add_chat({target_info['role']: target_info['content']})

    @classmethod
    async def aiter_bytes(cls, r: httpx.Response):
        bytes_ = b''
        async for chunk in r.aiter_bytes():
            bytes_ += chunk
            yield chunk
        try:
            cls.log_chat_completions(bytes_)
        except Exception as e:
            logger.debug(f"log chat (not) error:\n{e=}")

    @classmethod
    async def _reverse_proxy(cls, request: Request):
        client: httpx.AsyncClient = request.app.state.client
        url_path = request.url.path
        url_path = url_path[len(cls._ROUTE_PREFIX):]
        url = httpx.URL(path=url_path, query=request.url.query.encode('utf-8'))
        headers = dict(request.headers)
        auth = headers.pop("authorization", None)
        if auth and str(auth).startswith("Bearer sk-"):
            tmp_headers = {'Authorization': auth}
        elif cls._default_api_key_list:
            auth = "Bearer " + next(cls._cycle_api_key)
            tmp_headers = {'Authorization': auth}
        else:
            tmp_headers = {}

        headers.pop("host", None)
        headers.update(tmp_headers)
        if cls._LOG_CHAT:
            try:
                input_info = await request.json()
                msgs = input_info['messages']
                cls.chatsaver.add_chat({
                    "host": request.client.host,
                    "model": input_info['model'],
                    "messages": [{msg['role']: msg['content']} for msg in msgs],
                })
            except Exception as e:
                logger.debug(f"log chat (not) error:\n{request.client.host=}: {e}")
        req = client.build_request(
            request.method, url, headers=headers,
            content=request.stream(),
            timeout=cls.timeout,
        )
        logger.warning(f"{url=}")

        try:
            r = await client.send(req, stream=True)
        except httpx.ConnectError as e:
            error_info = f"{type(e)}: {e} | " \
                         f"Please check if host={request.client.host} can access [{cls._base_url}] successfully."
            logger.error(error_info)
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_info)
        except Exception as e:
            error_info = f"{type(e)}: {str(e)}"
            logger.error(error_info)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_info)

        aiter_bytes = cls.aiter_bytes(r) if cls._LOG_CHAT else r.aiter_bytes()
        return StreamingResponse(
            aiter_bytes,
            status_code=r.status_code,
            # headers=r.headers, # do not use r.headers, it will cause error
            media_type=r.headers.get("content-type"),
            background=BackgroundTask(r.aclose)
        )
