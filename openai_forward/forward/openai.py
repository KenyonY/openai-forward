from .base import OpenaiBase


class OpenaiForward(OpenaiBase):
    def __init__(self, base_url: str, route_prefix: str, proxy=None):
        import httpx

        self.BASE_URL = base_url
        self.ROUTE_PREFIX = route_prefix
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL, proxies=proxy, http1=True, http2=False
        )

        super().__init__()


def create_openai_proxies():
    """
    Generate OPENAI api style OpenaiForward objects.

    Returns:
        _objs (list): A list of OpenaiForward objects.
    """
    from ..settings import OPENAI_BASE_URL, OPENAI_ROUTE_PREFIX, PROXY

    _objs = []
    for base_url, route_prefix in zip(OPENAI_BASE_URL, OPENAI_ROUTE_PREFIX):
        _objs.append(OpenaiForward(base_url, route_prefix, PROXY))
    return _objs
