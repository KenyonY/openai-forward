from openai_forward.openai import OpenaiBase
from fastapi import HTTPException
import pytest


@pytest.fixture(scope="module")
def openai() -> OpenaiBase:
    return OpenaiBase()


class TestOpenai:
    def test_env(self, openai: OpenaiBase):
        assert openai._base_url == "https://api.openai.com"

    def test_validate_ip(self, openai: OpenaiBase):
        ip1 = "1.1.1.1"
        ip2 = "2.2.2.2"
        assert openai.validate_request_host("*") is None
        openai.IP_WHITELIST.append(ip1)
        assert openai.validate_request_host(ip1) is None
        with pytest.raises(HTTPException):
            openai.validate_request_host(ip2)
        openai.IP_WHITELIST = []
        openai.IP_BLACKLIST.append(ip1)
        assert openai.validate_request_host(ip2) is None
        with pytest.raises(HTTPException):
            openai.validate_request_host(ip1)
