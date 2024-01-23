import base64
import pickle
import time

import pandas as pd
import streamlit as st
import zmq

from openai_forward.web.interface import *

# st.set_page_config(
#      page_title='config',
#      layout="wide",
#      initial_sidebar_state="expanded",
# )

if 'socket' not in st.session_state:
    context = zmq.Context()
    socket = context.socket(zmq.REQ)  # REQ (REQUEST) socket for request-reply pattern
    socket.connect("tcp://localhost:15555")
    st.session_state['socket'] = socket
    st.session_state['config'] = Config()


config = st.session_state['config']


with st.sidebar:
    selected_section = st.radio(
        "Select a configuration section",
        ("Forward", "API Key", "Cache", "Rate Limit", "Other"),
    )

    if st.button("Apply and Restart"):

        with st.spinner("Saving configuration and reloading openai forward..."):
            env_dict = config.convert_to_env(set_env=False)
            socket = st.session_state['socket']
            socket.send(pickle.dumps(env_dict))
            message: bytes = socket.recv()

        st.success(message.decode())

    def generate_env_content(config):
        env_dict = config.convert_to_env(set_env=False)
        env_content = "\n".join([f"{key}={value}" for key, value in env_dict.items()])
        return env_content

    st.download_button(
        label="Export to .env file",
        data=generate_env_content(config),
        file_name="config.env",
        mime="text/plain",
    )


def display_forward_configuration(config):
    forward_config = config.forward
    with st.container():
        st.subheader("OpenAI Forward")
        df = pd.DataFrame([i.to_dict() for i in forward_config.openai])
        edited_df = st.data_editor(df, num_rows="dynamic", key="editor1", width=500)
        forward_config.openai = [
            ForwardItem(row["base_url"], row["route_prefix"])
            for i, row in edited_df.iterrows()
            if row["route_prefix"] is not None
        ]

        st.subheader("General Forward")
        df2 = pd.DataFrame([i.to_dict() for i in forward_config.general])
        edited_df2 = st.data_editor(df2, num_rows="dynamic", key="editor2", width=500)
        forward_config.general = [
            ForwardItem(row["base_url"], row["route_prefix"])
            for i, row in edited_df2.iterrows()
            if row["route_prefix"] is not None
        ]

        st.subheader("Log Configuration")
        log = config.log
        log.chat = st.checkbox("Log Chat", log.chat)
        log.CHAT_COMPLETION_ROUTE = st.text_input(
            "Chat Completion Route", log.CHAT_COMPLETION_ROUTE
        )
        log.COMPLETION_ROUTE = st.text_input("Completion Route", log.COMPLETION_ROUTE)
        log.EMBEDDING_ROUTE = st.text_input("Embedding Route", log.EMBEDDING_ROUTE)


def display_api_key_configuration(config):
    with st.container():
        api_key = config.api_key
        st.subheader("OpenAI API Key")
        df = pd.DataFrame(
            [i.to_dict() for i in api_key.openai_key]
            # [{"api_key": "sk-***", "level": 0}]
        )
        edited_df = st.data_editor(df, num_rows="dynamic", key="editor1", width=500)
        api_key.openai_key = [
            ApiKeyItem(row["api_key"], row["level"]) for i, row in edited_df.iterrows()
        ]
        st.subheader("Forward Key")
        df = pd.DataFrame([i.to_dict() for i in api_key.forward_key])
        edited_df = st.data_editor(df, num_rows="dynamic", key="editor2", width=500)
        api_key.forward_key = [
            ApiKeyItem(row["api_key"], row["level"]) for i, row in edited_df.iterrows()
        ]

        st.subheader("Key Level")
        df = pd.DataFrame([i.to_dict() for i in api_key.level])
        edited_df = st.data_editor(df, num_rows="dynamic", key="editor3", width=500)
        api_key.level = [
            ApiKeyLevel(level=row["level"], models=row["models"])
            for i, row in edited_df.iterrows()
        ]

        st.write(
            """**说明**  
- 不同level对应不同权限，可以定义不同权限可以访问哪些模型。 例如, level为0，全权限，可访问任何模型; level为1，只可访问gpt3.5-turbo。
- 每个key对应一个level
- 对于api key而言，level的意义是区分该api key自身是否有权限访问哪些模型。
- 对于forward key而言，level表示它可以访问该level对应的所有api key。
        """
        )


def display_cache_configuration(config):
    with st.container():
        st.subheader("Cache Configuration")

        cache = config.cache

        cache.backend = st.selectbox(
            "Cache Backend",
            ["MEMORY", "LMDB", "LevelDB"],
            index=["MEMORY", "LMDB", "LevelDB"].index(cache.backend),
        )
        cache.root_path_or_url = st.text_input(
            "Root Path or URL", cache.root_path_or_url
        )
        cache.default_request_caching_value = st.checkbox(
            "Default Request Caching Value", cache.default_request_caching_value
        )
        cache.cache_chat_completion = st.checkbox(
            "Cache Chat Completion", cache.cache_chat_completion
        )
        cache.cache_embedding = st.checkbox("Cache Embedding", cache.cache_embedding)


def display_rate_limit_configuration(config):
    with st.container():
        st.subheader("Rate Limit Configuration")

        rate_limit = config.rate_limit

        rate_limit.global_rate_limit = st.text_input(
            "Global Rate Limit", rate_limit.global_rate_limit
        )
        rate_limit.iter_chunk = st.selectbox(
            "Iteration Chunk Type",
            ['one-by-one', 'efficiency'],
            index=['one-by-one', 'efficiency'].index(rate_limit.iter_chunk),
        )
        rate_limit.strategy = st.selectbox(
            "Rate Limit Strategy",
            ['fixed_window', 'moving-window', 'fixed-window-elastic-expiry'],
            index=[
                'fixed_window',
                'moving-window',
                'fixed-window-elastic-expiry',
            ].index(rate_limit.strategy),
        )

        st.subheader("Token Rate Limit")
        token_rate_limit_df = pd.DataFrame(
            [i.to_dict() for i in rate_limit.token_rate_limit]
        )
        edited_token_rate_limit_df = st.data_editor(
            token_rate_limit_df,
            num_rows="dynamic",
            key="editor_token_rate_limit",
            width=500,
        )
        rate_limit.token_rate_limit = [
            RateLimitType(row["route"], row["value"])
            for _, row in edited_token_rate_limit_df.iterrows()
        ]

        st.subheader("Request Rate Limit")
        req_rate_limit_df = pd.DataFrame(
            [i.to_dict() for i in rate_limit.req_rate_limit]
        )
        edited_req_rate_limit_df = st.data_editor(
            req_rate_limit_df,
            num_rows="dynamic",
            key="editor_req_rate_limit",
            width=500,
        )
        rate_limit.req_rate_limit = [
            RateLimitType(row["route"], row["value"])
            for _, row in edited_req_rate_limit_df.iterrows()
        ]


def display_other_configuration(config):
    with st.container():
        st.subheader("Other Configuration")

        config.timezone = st.text_input("Timezone", config.timezone)
        config.timeout = st.number_input(
            "Timeout (seconds)", value=config.timeout, min_value=1, step=1
        )


if selected_section == "Forward":
    display_forward_configuration(config)

elif selected_section == "API Key":
    display_api_key_configuration(config)

elif selected_section == "Cache":
    display_cache_configuration(config)

elif selected_section == "Rate Limit":
    display_rate_limit_configuration(config)


elif selected_section == "Other":
    display_other_configuration(config)
