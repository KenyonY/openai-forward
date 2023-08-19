import time

from .base import ChatSaver, OpenaiBase, WhisperSaver
from .settings import LOG_CHAT, print_chat


class OpenaiForwarding(OpenaiBase):
    def __init__(self, base_url: str, route_prefix: str, proxy=None):
        import httpx

        self.BASE_URL = base_url
        self.ROUTE_PREFIX = route_prefix
        if LOG_CHAT or print_chat:
            self.chatsaver = ChatSaver(route_prefix)
            self.whispersaver = WhisperSaver(route_prefix)
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL, proxies=proxy, http1=True, http2=False
        )


def fwd_openai_objs():
    """
    Generate OPENAI api style forwarding objects.

    Returns:
        fwd_objs (list): A list of OpenaiForwarding objects.
    """
    from .settings import OPENAI_BASE_URL, OPENAI_ROUTE_PREFIX, PROXY

    fwd_objs = []
    for base_url, route_prefix in zip(OPENAI_BASE_URL, OPENAI_ROUTE_PREFIX):
        fwd_objs.append(OpenaiForwarding(base_url, route_prefix, PROXY))
    return fwd_objs
