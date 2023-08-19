from .base import ForwardingBase


class AnyForwarding(ForwardingBase):
    def __init__(self, base_url: str, route_prefix: str, proxy=None):
        import httpx

        self.BASE_URL = base_url
        self.ROUTE_PREFIX = route_prefix
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL, proxies=proxy, http1=True, http2=False
        )


def fwd_anything_objs():
    """
    Generate extra forwarding objects.

    Returns:
        list: A list of AnyForwarding objects.
    """
    from .settings import EXTRA_BASE_URL, EXTRA_ROUTE_PREFIX, PROXY

    extra_fwd_objs = []
    for base_url, route_prefix in zip(EXTRA_BASE_URL, EXTRA_ROUTE_PREFIX):
        extra_fwd_objs.append(AnyForwarding(base_url, route_prefix, PROXY))
    return extra_fwd_objs
