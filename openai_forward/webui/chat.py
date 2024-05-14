from collections import OrderedDict, deque
from typing import Callable, Dict

import streamlit as st


def render_chat_log_message(msg: Dict, markdown=True):
    msg = msg.copy()
    render = st.markdown if markdown else st.text
    if msg.get("user_role"):
        messages = msg.pop('messages')
        with st.chat_message(name="user", avatar='🧑'):
            for msg_item in messages:
                # https://github.com/streamlit/streamlit/issues/7978
                render(f"`{msg_item['role']}`: {msg_item['content']}")
            st.write(msg)
    elif msg.get("assistant_role"):
        with st.chat_message(name="assistant", avatar='🤖'):
            ass_content = msg.pop('assistant', None)
            render(ass_content)
            st.write(msg)
    else:
        print(f"{msg=}")


class ChatData:
    def __init__(self, max_len: int):
        self.data = OrderedDict()
        self.max_len = max_len

    def add_message(self, message, **callback_kwargs):
        uid = message.pop('uid')
        if message.get("user_role"):
            self.data.setdefault(uid, {'user_role': message})
        else:
            msg_item = self.data.get(uid, {})
            msg_item['assistant_role'] = message
        if len(self.data) >= self.max_len:
            self.data.popitem(last=False)
        render_chat_log_message(message, **callback_kwargs)

    def render_all_messages(self, **callback_kwargs):
        for uid, msg in self.data.items():
            message = msg.get("user_role")
            if message:
                render_chat_log_message(message, **callback_kwargs)
            message = msg.get("assistant_role")
            if message:
                render_chat_log_message(message, **callback_kwargs)
