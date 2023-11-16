from openai_forward.settings import *


def test_env():
    assert "OPENAI_BASE_URL" in os.environ
