from .core import OpenaiForward


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


openai_objs = create_openai_proxies()
