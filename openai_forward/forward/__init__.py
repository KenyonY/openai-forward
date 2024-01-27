from typing import List

from ..settings import (
    GENERAL_BASE_URL,
    GENERAL_ROUTE_PREFIX,
    OPENAI_BASE_URL,
    OPENAI_ROUTE_PREFIX,
    PROXY,
)
from .core import GenericForward, OpenaiForward


class ForwardManager:
    def __init__(self):
        """
        Initializes the class by creating OpenAI and Generic forward objects and their root objects.
        """
        self.openai_objs, self.openai_root_obj = self._create_forward_obj(
            OPENAI_BASE_URL, OPENAI_ROUTE_PREFIX, OpenaiForward
        )
        self.generic_objs, self.generic_root_obj = self._create_forward_obj(
            GENERAL_BASE_URL, GENERAL_ROUTE_PREFIX, GenericForward
        )
        self.root_objs = [i for i in [self.openai_root_obj, self.generic_root_obj] if i]
        if len(self.root_objs) == 2:
            raise ValueError("Only one root routing forwarding object can exist!")

    @staticmethod
    def _create_forward_obj(base_urls: List, route_prefixes: List, Forward):
        """
        Generate OpenaiForward or GenericForward objects.

        Returns:
            _objs (list): A list of Forward objects.
        """

        root_forward_obj = None
        _objs = []
        for base_url, route_prefix in zip(base_urls, route_prefixes):
            if route_prefix == "/":
                root_forward_obj = Forward(base_url, route_prefix, PROXY)
            else:
                _objs.append(Forward(base_url, route_prefix, PROXY))
        return _objs, root_forward_obj

    async def start_up(self):
        """
        Asynchronously starts up the objects by building clients for openai_objs, generic_objs, and root_objs.
        """
        [await obj.build_client() for obj in self.openai_objs]
        [await obj.build_client() for obj in self.generic_objs]
        [await obj.build_client() for obj in self.root_objs]

    async def shutdown(self):
        """
        Asynchronous shut down the client connections.
        """
        [await obj.client.close() for obj in self.openai_objs]
        [await obj.client.close() for obj in self.generic_objs]
        [await obj.client.close() for obj in self.root_objs]
