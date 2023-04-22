from fastapi import Request
from fastapi.responses import StreamingResponse
from loguru import logger
import httpx
from starlette.background import BackgroundTask
import os
from .content.chat import log_chat_completions, ChatSaver


class OpenaiBase:
    default_api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com")
    LOG_CHAT = os.environ.get("LOG_CHAT", "False").lower() == "true"
    stream_timeout = 20
    timeout = 30
    non_stream_timeout = 30
    allow_ips = []
    chatsaver = ChatSaver(save_interval=10)

    def add_allowed_ip(self, ip: str):
        if ip == "*":
            ...
        else:
            self.allow_ips.append(ip)

    def validate_request_host(self, ip):
        if ip == "*" or ip in self.allow_ips:
            return True
        else:
            return False

    @classmethod
    def log_chat_completions(cls, bytes_: bytes):
        target_info = log_chat_completions(bytes_)
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
            logger.warning(e)

    @classmethod
    async def _reverse_proxy(cls, request: Request):
        client: httpx.AsyncClient = request.app.state.client
        url = httpx.URL(path=request.url.path, query=request.url.query.encode('utf-8'))
        headers = dict(request.headers)
        auth = headers.pop("authorization", None)
        if auth and str(auth).startswith("Bearer sk-"):
            tmp_headers = {'Authorization': auth}
        elif cls.default_api_key:
            auth = "Bearer " + cls.default_api_key
            tmp_headers = {'Authorization': auth}
        else:
            tmp_headers = {}

        headers.pop("host", None)
        headers.update(tmp_headers)
        if cls.LOG_CHAT:
            try:
                input_info = await request.json()
                msgs = input_info['messages']
                cls.chatsaver.add_chat({
                    "model": input_info['model'],
                    "messages": [{msg['role']: msg['content']} for msg in msgs],
                })
            except Exception as e:
                logger.warning(e)
        req = client.build_request(
            request.method, url, headers=headers,
            content=request.stream(),
            timeout=cls.timeout,
        )
        r = await client.send(req, stream=True)

        aiter_bytes = cls.aiter_bytes(r) if cls.LOG_CHAT else r.aiter_bytes()
        return StreamingResponse(
            aiter_bytes,
            status_code=r.status_code,
            # headers=r.headers, # do not use r.headers, it will cause error
            media_type=r.headers.get("content-type"),
            background=BackgroundTask(r.aclose)
        )
