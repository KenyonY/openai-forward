from collections import deque
from typing import Callable, Dict

import streamlit as st


def render_chat_log_message(msg: Dict):
    msg = msg.copy()
    if msg.get("user_role"):
        with st.chat_message(name="human"):
            messages = msg.pop('messages')
            for msg_item in messages:
                # https://github.com/streamlit/streamlit/issues/7978
                # st.write(f"`{msg_item['role']}`: {msg_item['content']}")
                st.text(f"`{msg_item['role']}`: {msg_item['content']}")
            st.write(msg)
    elif msg.get("assistant_role"):
        with st.chat_message(name="ai"):
            ass_content = msg.pop('assistant', None)
            st.write(ass_content)
            st.write(msg)
    else:
        print(f"{msg=}")


class ChatData:
    def __init__(self, max_len: int, callback: Callable):
        self.data = deque(maxlen=max_len)
        self.callback = callback

    def add_message(self, message):
        self.data.append(message)
        self.callback(message)

    def render_all_messages(self):
        for message in self.data:
            self.callback(message)
