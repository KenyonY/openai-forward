from fastapi import Request

from ..config import print_startup_info
from .base import OpenaiBase


class Openai(OpenaiBase):
    def __init__(self):
        if self.IP_BLACKLIST or self.IP_WHITELIST:
            self.validate_host = True
        else:
            self.validate_host = False
        print_startup_info(
            self.BASE_URL,
            self.ROUTE_PREFIX,
            self._openai_api_key_list,
            self._no_auth_mode,
            self._LOG_CHAT,
        )

    async def reverse_proxy(self, request: Request):
        if self.validate_host:
            self.validate_request_host(request.client.host)
        return await self._reverse_proxy(request)
