from .base import OpenaiBase


class OpenaiForward(OpenaiBase):
    def __init__(self, base_url: str, route_prefix: str, proxy=None):
        super().__init__(base_url, route_prefix, proxy)


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
