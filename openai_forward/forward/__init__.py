from typing import List

from openai_forward.config.settings import (
    GENERAL_BASE_URL,
    GENERAL_ROUTE_PREFIX,
    OPENAI_BASE_URL,
    OPENAI_ROUTE_PREFIX,
    CUSTOM_BASE_URL, CUSTOM_ROUTE_PREFIX, CUSTOM_CONFIG,
    PROXY,
)

from .core import GenericForward, OpenaiForward, CustomForward


class ForwardManager:
    def __init__(self):
        """
        Initializes the class by creating OpenAI and Generic forward objects and their root objects.
        """
        self.openai_objs, self.openai_root_obj = self._create_forward_obj(
            OPENAI_BASE_URL, OPENAI_ROUTE_PREFIX, [{}]*len(OPENAI_BASE_URL), OpenaiForward
        )
        self.generic_objs, self.generic_root_obj = self._create_forward_obj(
            GENERAL_BASE_URL, GENERAL_ROUTE_PREFIX,[{}]*len(GENERAL_BASE_URL), GenericForward
        )
        self.custom_objs, self.custom_root_obj = self._create_forward_obj(
            CUSTOM_BASE_URL, CUSTOM_ROUTE_PREFIX, CUSTOM_CONFIG, CustomForward
        )
        self.root_objs = [i for i in [self.openai_root_obj, self.generic_root_obj, self.custom_root_obj] if i]
        assert len(self.root_objs) <= 1, "Only one root routing forwarding object can exist!"

    @staticmethod
    def _create_forward_obj(base_urls: List, route_prefixes: List, custom_configs: List,  Forward):
        """
        Generate OpenaiForward or GenericForward objects.

        Returns:
            _objs (list): A list of Forward objects.
        """

        root_forward_obj = None
        _objs = []
        for base_url, route_prefix, custom_config in zip(base_urls, route_prefixes, custom_configs):
            if route_prefix == "/":
                root_forward_obj = Forward(base_url, route_prefix, PROXY, custom_config=custom_config)
            else:
                _objs.append(Forward(base_url, route_prefix, PROXY, custom_config=custom_config))
        return _objs, root_forward_obj

    async def start_up(self):
        """
        Asynchronously starts up the objects by building clients for openai_objs, generic_objs, and root_objs.
        """
        [await obj.build_client() for obj in self.openai_objs]
        [await obj.build_client() for obj in self.custom_objs]
        [await obj.build_client() for obj in self.generic_objs]
        [await obj.build_client() for obj in self.root_objs]

    async def shutdown(self):
        """
        Asynchronous shut down the client connections.
        """
        [await obj.client.close() for obj in self.openai_objs]
        [await obj.client.close() for obj in self.custom_objs]
        [await obj.client.close() for obj in self.generic_objs]
        [await obj.client.close() for obj in self.root_objs]
