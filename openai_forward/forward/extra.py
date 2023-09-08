from .base import ForwardBase


class GenericForward(ForwardBase):
    def __init__(self, base_url: str, route_prefix: str, proxy=None):
        import httpx

        self.BASE_URL = base_url
        self.ROUTE_PREFIX = route_prefix
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL, proxies=proxy, http1=True, http2=False
        )


def create_generic_proxies():
    """
    Generate extra forwarding objects.

    Returns:
        list: A list of GenericForward objects.
    """
    from ..settings import EXTRA_BASE_URL, EXTRA_ROUTE_PREFIX, PROXY

    _objs = []
    for base_url, route_prefix in zip(EXTRA_BASE_URL, EXTRA_ROUTE_PREFIX):
        _objs.append(GenericForward(base_url, route_prefix, PROXY))
    return _objs
