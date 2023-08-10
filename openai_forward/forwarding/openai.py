from ..config import print_startup_info
from .base import OpenaiBase
from .settings import LOG_CHAT, OPENAI_API_KEY


class OpenaiForwarding(OpenaiBase):
    def __init__(self, base_url: str, route_prefix: str, proxy=None):
        import httpx

        self.BASE_URL = base_url
        self.ROUTE_PREFIX = route_prefix
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL, proxies=proxy, http1=True, http2=False
        )
        print_startup_info(
            self.BASE_URL,
            self.ROUTE_PREFIX,
            OPENAI_API_KEY,
            self._no_auth_mode,
            LOG_CHAT,
        )


def get_fwd_openai_style_objs():
    """获取openai风格路由转发对象"""
    from .settings import OPENAI_BASE_URL, OPENAI_ROUTE_PREFIX, PROXY

    fwd_objs = []
    for base_url, route_prefix in zip(OPENAI_BASE_URL, OPENAI_ROUTE_PREFIX):
        fwd_objs.append(OpenaiForwarding(base_url, route_prefix, PROXY))
    return fwd_objs
