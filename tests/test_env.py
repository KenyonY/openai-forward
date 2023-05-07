import pytest
import os
import importlib
import openai_forward
import time
from dotenv import load_dotenv

class TestEnv:
    with open(".env", 'r', encoding='utf-8') as f:
        defualt_env = f.read()

    @classmethod
    def setup_class(cls):
        env = """\
LOG_CHAT=true
OPENAI_BASE_URL=https://api.openai.com
OPENAI_API_KEY=key1 key2
PASSWORD=ps1 ps2 ps3
ROUTE_PREFIX=
IP_WHITELIST=
IP_BLACKLIST=
"""
        with open(".env", 'w', encoding='utf-8') as f:
            f.write(env)
            time.sleep(0.1)

        load_dotenv(override=True)
        importlib.reload(openai_forward.base)
        cls.aibase = openai_forward.base.OpenaiBase()

    @classmethod
    def teardown_class(cls):
        with open(".env", 'w', encoding='utf-8') as f:
            f.write(cls.defualt_env)

    def test_env1(self):
        assert self.aibase._PASSWORD == ['ps1', 'ps2', 'ps3']
        assert self.aibase._default_api_key_list == ['key1', 'key2']
        assert self.aibase._use_password
