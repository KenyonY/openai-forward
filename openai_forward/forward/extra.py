from .base import ForwardBase


class GenericForward(ForwardBase):
    def __init__(self, base_url: str, route_prefix: str, proxy=None):
        super().__init__(base_url, route_prefix, proxy)


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
