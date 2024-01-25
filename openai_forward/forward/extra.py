from .core import GenericForward


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


generic_objs = create_generic_proxies()
