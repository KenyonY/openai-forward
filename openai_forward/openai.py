from ._base import OpenaiBase
from .routers.schemas import OpenAIV1ChatCompletion
from fastapi import Request, HTTPException, status
from .config import setting_log

setting_log(log_name="openai_forward.log")


class Openai(OpenaiBase):
    def __init__(self):
        self.validate_host = False

    async def reverse_proxy(self, request: Request):
        if self.validate_host:
            if not self.validate_request_host(request.client.host):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f"Forbidden, please add ip={request.client.host} to `allow_ips`")

        return await self._reverse_proxy(request)

    async def v1_chat_completions(self, data: OpenAIV1ChatCompletion, request: Request):
        ...
