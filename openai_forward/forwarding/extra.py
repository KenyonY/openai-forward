from ..config import print_startup_info
from .base import LOG_CHAT, ForwardingBase


class AnyForwarding(ForwardingBase):
    def __init__(self, base_url: str, route_prefix: str, proxy=None):
        import httpx

        self.BASE_URL = base_url
        self.ROUTE_PREFIX = route_prefix
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL, proxies=proxy, http1=True, http2=False
        )
        print_startup_info(self.BASE_URL, self.ROUTE_PREFIX, [], "\\", LOG_CHAT)


def get_fwd_anything_objs():
    """获取extra路由转发对象"""
    from .settings import EXTRA_BASE_URL, EXTRA_ROUTE_PREFIX, PROXY

    extra_fwd_objs = []
    for base_url, route_prefix in zip(EXTRA_BASE_URL, EXTRA_ROUTE_PREFIX):
        extra_fwd_objs.append(AnyForwarding(base_url, route_prefix, PROXY))
    return extra_fwd_objs
