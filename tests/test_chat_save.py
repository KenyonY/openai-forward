from openai_forward.content.chat import ChatSaver
import pytest
from utils import rm


@pytest.fixture(scope="module")
def saver() -> ChatSaver:
    return ChatSaver(save_interval=1, max_chat_size=2)


class TestChatSaver:

    @classmethod
    def teardown_class(cls):
        rm("Log/chat*.txt")

    def test_init(self, saver: ChatSaver):
        assert saver.chat_file.endswith("chat_0.txt")

    def test_add_chat(self, saver: ChatSaver):
        saver.add_chat({"id": 1, "content": "hello"})
        assert saver.chat_file.endswith("chat_0.txt")
        saver.add_chat({"id": 2, "content": "hello"})
        assert saver.chat_file.endswith("chat_0.txt")
        saver.add_chat({"id": 3, "content": "hello"})
        assert saver.chat_file.endswith("chat_1.txt")
        saver.add_chat({"id": 4, "content": "hello"})
        assert saver.chat_file.endswith("chat_1.txt")
        saver.add_chat({"id": 5, "content": "hello"})
        assert saver.chat_file.endswith("chat_2.txt")

    def test_init_file(self):
        saver = ChatSaver()
        assert saver.chat_file.endswith("chat_3.txt")
