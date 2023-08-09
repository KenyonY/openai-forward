from itertools import cycle

import pytest
from fastapi import HTTPException

from openai_forward.forwarding.openai import OpenaiForwarding


@pytest.fixture(scope="module")
def openai() -> OpenaiForwarding:
    return OpenaiForwarding("https://api.openai-forward.com", "/")


class TestOpenai:
    @staticmethod
    def teardown_method():
        OpenaiForwarding.IP_BLACKLIST = []
        OpenaiForwarding.IP_WHITELIST = []
        OpenaiForwarding._default_api_key_list = []

    def test_env(self, openai: OpenaiForwarding):
        from openai_forward.forwarding.settings import (
            LOG_CHAT,
            OPENAI_BASE_URL,
            OPENAI_ROUTE_PREFIX,
        )

        assert LOG_CHAT is False
        assert OPENAI_BASE_URL == ["https://api.openai.com"]
        assert OPENAI_ROUTE_PREFIX == ["/"]

    def test_api_keys(self, openai: OpenaiForwarding):
        assert openai._default_api_key_list == []
        openai._default_api_key_list = ["a", "b"]
        openai._cycle_api_key = cycle(openai._default_api_key_list)
        assert next(openai._cycle_api_key) == "a"
        assert next(openai._cycle_api_key) == "b"
        assert next(openai._cycle_api_key) == "a"
        assert next(openai._cycle_api_key) == "b"
        assert next(openai._cycle_api_key) == "a"

    def test_validate_ip(self, openai: OpenaiForwarding):
        from openai_forward.forwarding.settings import IP_BLACKLIST, IP_WHITELIST

        ip1 = "1.1.1.1"
        ip2 = "2.2.2.2"
        IP_WHITELIST.append(ip1)
        with pytest.raises(HTTPException):
            openai.validate_request_host(ip2)
        IP_WHITELIST.clear()
        IP_BLACKLIST.append(ip1)
        with pytest.raises(HTTPException):
            openai.validate_request_host(ip1)
