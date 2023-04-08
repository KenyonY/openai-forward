from ._base import OpenaiBase, Request
from .routers.schemas import OpenAIV1ChatCompletion
from dotenv import load_dotenv
import os

load_dotenv()


class Openai(OpenaiBase):
    def __init__(self):
        self.validate_host = False

    async def reverse_proxy(self, request: Request):
        if self.validate_host:
            self.validate_request_host(request.client.host)
        return await self._reverse_proxy(request)

    async def _forward(self, route: str, request: Request, data=None):
        url = os.path.join(self.base_url, route)
        if self.validate_host:
            self.validate_request_host(request.client.host)
        return await self.forwarding(url,
                                     request,
                                     data,
                                     default_openai_auth=self.default_api_key)

    async def v1_chat_completions(self, data: OpenAIV1ChatCompletion, request: Request):
        return await self._forward("v1/chat/completions", request, data)
