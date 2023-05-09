from .base import OpenaiBase
from .routers.schemas import OpenAIV1ChatCompletion
from fastapi import Request
from .config import setting_log

setting_log(log_name="openai_forward")


class Openai(OpenaiBase):
    def __init__(self):
        if self.IP_BLACKLIST or self.IP_WHITELIST:
            self.validate_host = True
        else:
            self.validate_host = False

    async def reverse_proxy(self, request: Request):
        if self.validate_host:
            self.validate_request_host(request.client.host)
        return await self._reverse_proxy(request)

    async def v1_chat_completions(self, data: OpenAIV1ChatCompletion, request: Request):
        ...
