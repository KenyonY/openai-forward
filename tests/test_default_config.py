from openai_forward.settings import *


def test_env():
    assert "FORWARD_CONFIG" in os.environ
