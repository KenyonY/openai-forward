from fastapi import Request

from ..config import print_startup_info
from .base import BASE_URL_EXTRA, ROUTE_PREFIX_EXTRA, ForwardingBase


class ExtraForwarding(ForwardingBase):
    def __init__(self, base_url: str, route_prefix: str):
        self.BASE_URL = base_url
        self.ROUTE_PREFIX = route_prefix
        if self.IP_BLACKLIST or self.IP_WHITELIST:
            self.validate_host = True
        else:
            self.validate_host = False
        print_startup_info(self.BASE_URL, self.ROUTE_PREFIX, [], False, self._LOG_CHAT)

    async def reverse_proxy(self, request: Request):
        if self.validate_host:
            self.validate_request_host(request.client.host)
        return await self._reverse_proxy(request)


def get_extra_fwd_objs():
    extra_fwd_objs = []
    for base_url, route_prefix in zip(BASE_URL_EXTRA, ROUTE_PREFIX_EXTRA):
        extra_fwd_objs.append(ExtraForwarding(base_url, route_prefix))
    return extra_fwd_objs
