import pickle
import threading

import orjson
import pandas as pd
import streamlit as st
import zmq
from flaxkv.helper import SimpleQueue

from openai_forward.webui.interface import *

st.set_page_config(
    page_title="Openai Forward ",
    page_icon="🚀",
    # layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get help': 'https://github.com/KenyonY/openai-forward',
        'Report a bug': "https://github.com/KenyonY/openai-forward/issues",
        'About': "# Openai Forward",
    },
)


@st.cache_resource
def get_socket():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    # socket.setsockopt(zmq.CONNECT_TIMEOUT, 20000) # 20s
    log_socket = context.socket(zmq.ROUTER)

    socket.connect("tcp://localhost:15555")
    log_socket.bind("tcp://*:15556")

    def worker(log_socket: zmq.Socket, q: SimpleQueue):
        while True:
            message = log_socket.recv_multipart()
            print(f"{message=}")
            identify, uid, msg = message
            q.put((uid, msg))

    q = SimpleQueue(maxsize=200)
    threading.Thread(target=worker, args=(log_socket, q)).start()
    config = Config()
    return socket, log_socket, q, config


if 'socket' not in st.session_state:
    socket, log_socket, q, config = get_socket()

    st.session_state['q'] = q
    st.session_state['socket'] = socket
    st.session_state['log_socket'] = log_socket
    st.session_state['config'] = config


config = st.session_state['config']


with st.sidebar:
    selected_section = st.radio(
        "Select a configuration section",
        (
            "Forward",
            "API Key",
            "Cache",
            "Rate Limit",
            "Other",
            "Real-time Logs",
            "Playground",
        ),
    )

    if st.button(
        "Apply and Restart", help="Saving configuration and reloading openai forward"
    ):

        with st.spinner("Saving configuration and reloading openai forward..."):
            env_dict = config.convert_to_env(set_env=False)
            socket = st.session_state['socket']
            socket.send(pickle.dumps(env_dict))
            message: bytes = socket.recv()

        st.success(message.decode())

    def generate_env_content():
        env_dict = config.convert_to_env(set_env=False)
        env_content = "\n".join([f"{key}={value}" for key, value in env_dict.items()])
        return env_content

    if st.button(
        "Export to .env file",
    ):
        # Deferred data for download button: https://github.com/streamlit/streamlit/issues/5053
        download = st.download_button(
            use_container_width=True,
            label="Export",
            data=generate_env_content(),
            file_name="config.env",
            mime="text/plain",
        )


def display_forward_configuration():
    forward_config = config.forward

    with st.form("forward_configuration", border=False):
        st.subheader("OpenAI Forward")
        df = pd.DataFrame([i.to_dict() for i in forward_config.openai])
        edited_df = st.data_editor(
            df, num_rows="dynamic", key="editor1", use_container_width=True
        )

        st.subheader("General Forward")
        df2 = pd.DataFrame([i.to_dict() for i in forward_config.general])
        edited_df2 = st.data_editor(
            df2, num_rows="dynamic", key="editor2", use_container_width=True
        )

        submitted = st.form_submit_button("Save", use_container_width=True)
        if submitted:
            forward_config.openai = [
                ForwardItem(row["base_url"], row["route_prefix"])
                for i, row in edited_df.iterrows()
                if row["route_prefix"] is not None
            ]

            forward_config.general = [
                ForwardItem(row["base_url"], row["route_prefix"])
                for i, row in edited_df2.iterrows()
                if row["route_prefix"] is not None
            ]

            print(forward_config.convert_to_env())


def display_api_key_configuration():
    st.header("【WIP】")
    api_key = config.api_key
    with st.form("api_key_form", border=False):

        st.subheader("OpenAI API Key")
        df = pd.DataFrame([i.to_dict() for i in api_key.openai_key])
        edited_df = st.data_editor(
            df, num_rows="dynamic", key="editor1", use_container_width=True
        )

        st.subheader("Forward Key")
        df2 = pd.DataFrame([i.to_dict() for i in api_key.forward_key])
        edited_df2 = st.data_editor(
            df2, num_rows="dynamic", key="editor2", use_container_width=True
        )

        st.subheader("Key Level")
        df3 = pd.DataFrame([i.to_dict() for i in api_key.level])
        edited_df3 = st.data_editor(
            df3,
            num_rows="dynamic",
            key="editor3",
            use_container_width=True,
        )

        submitted = st.form_submit_button("Save", use_container_width=True)
        if submitted:
            api_key.openai_key = [
                ApiKeyItem(row["api_key"], row["level"])
                for i, row in edited_df.iterrows()
            ]

            api_key.forward_key = [
                ApiKeyItem(row["api_key"], row["level"])
                for i, row in edited_df2.iterrows()
            ]

            api_key.level = [
                ApiKeyLevel(level=row["level"], models=row["models"])
                for i, row in edited_df3.iterrows()
            ]
            print(api_key.convert_to_env())
        st.write(
            """\
> **说明**  
> - 不同level对应不同权限，可以定义不同权限可以访问哪些模型。 例如, level为0，全权限，可访问任何模型; level为1，只可访问gpt-3.5-turbo。
> - 对于api key而言，level的意义是区分该api key自身是否有权限访问哪些模型。每个api key可对应多个level。
> - 对于forward key而言，每个key对应一个level，level表示它可以访问该level对应的所有api key。

        """
        )


def display_cache_configuration():
    log = config.log
    cache = config.cache

    with st.container():

        st.subheader("Log Configuration")
        log_chat = st.checkbox("Log Chat", log.chat)
        log_CHAT_COMPLETION_ROUTE = st.text_input(
            "Chat Completion Route", log.CHAT_COMPLETION_ROUTE, disabled=not log_chat
        )
        log_COMPLETION_ROUTE = st.text_input(
            "Completion Route", log.COMPLETION_ROUTE, disabled=not log_chat
        )
        log_EMBEDDING_ROUTE = st.text_input(
            "Embedding Route", log.EMBEDDING_ROUTE, disabled=not log_chat
        )

        st.subheader("Cache Configuration")

        cache_backend = st.selectbox(
            "Cache Backend",
            ["MEMORY", "LMDB", "LevelDB"],
            index=["MEMORY", "LMDB", "LevelDB"].index(cache.backend),
        )
        cache_root_path_or_url = st.text_input(
            "Root Path or URL",
            cache.root_path_or_url,
            disabled=cache_backend == "MEMORY",
        )
        cache_default_request_caching_value = st.checkbox(
            "Default Request Caching Value", cache.default_request_caching_value
        )
        cache_cache_chat_completion = st.checkbox(
            "Cache Chat Completion", cache.cache_chat_completion
        )
        cache_cache_embedding = st.checkbox("Cache Embedding", cache.cache_embedding)

        submitted = st.button("Save", use_container_width=True)
        if submitted:
            log.chat = log_chat
            log.CHAT_COMPLETION_ROUTE = log_CHAT_COMPLETION_ROUTE
            log.COMPLETION_ROUTE = log_COMPLETION_ROUTE
            log.EMBEDDING_ROUTE = log_EMBEDDING_ROUTE

            cache.backend = cache_backend
            cache.root_path_or_url = cache_root_path_or_url
            cache.default_request_caching_value = cache_default_request_caching_value
            cache.cache_chat_completion = cache_cache_chat_completion
            cache.cache_embedding = cache_cache_embedding

            print(cache.convert_to_env())
            print(log.convert_to_env())


def display_rate_limit_configuration():
    rate_limit = config.rate_limit

    with st.form("rate_limit_form", border=False):
        st.subheader("Rate Limit Configuration")

        global_rate_limit = st.text_input(
            "Global Rate Limit", rate_limit.global_rate_limit
        )
        iter_chunk = st.selectbox(
            "Iteration Chunk Type",
            ['one-by-one', 'efficiency'],
            index=['one-by-one', 'efficiency'].index(rate_limit.iter_chunk),
        )
        strategy = st.selectbox(
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
            use_container_width=True,
        )

        st.subheader("Request Rate Limit")
        req_rate_limit_df = pd.DataFrame(
            [i.to_dict() for i in rate_limit.req_rate_limit]
        )
        edited_req_rate_limit_df = st.data_editor(
            req_rate_limit_df,
            num_rows="dynamic",
            key="editor_req_rate_limit",
            use_container_width=True,
        )

        if st.form_submit_button("Save", use_container_width=True):
            rate_limit.global_rate_limit = global_rate_limit
            rate_limit.iter_chunk = iter_chunk
            rate_limit.strategy = strategy

            rate_limit.token_rate_limit = [
                RateLimitType(row["route"], row["value"])
                for _, row in edited_token_rate_limit_df.iterrows()
            ]

            rate_limit.req_rate_limit = [
                RateLimitType(row["route"], row["value"])
                for _, row in edited_req_rate_limit_df.iterrows()
            ]

            print(rate_limit.convert_to_env())


def display_other_configuration():
    with st.form("other_form", border=False):
        st.subheader("Other Configuration")

        timezone = st.text_input("Timezone", config.timezone)
        timeout = st.number_input(
            "Timeout (seconds)", value=config.timeout, min_value=1, step=1
        )
        proxy = st.text_input(
            "Proxy", config.proxy, placeholder="e.g. http://127.0.0.1:7890"
        )
        benchmark_mode = st.checkbox("Benchmark Mode", config.benchmark_mode)

        if st.form_submit_button("Save", use_container_width=True):
            config.timezone = timezone
            config.timeout = timeout
            config.proxy = proxy
            config.benchmark_mode = benchmark_mode

            print(config.convert_to_env())


if selected_section == "Forward":
    display_forward_configuration()

elif selected_section == "API Key":
    display_api_key_configuration()

elif selected_section == "Cache":
    display_cache_configuration()

elif selected_section == "Rate Limit":
    display_rate_limit_configuration()

elif selected_section == "Other":
    display_other_configuration()

elif selected_section == "Real-time Logs":
    st.write("### Real-time Logs")
    st.write("\n")

    with st.container():

        q = st.session_state['q']
        while True:
            uid, msg = q.get()
            uid: bytes
            item = orjson.loads(msg)
            if uid.startswith(b"0"):
                with st.chat_message("user"):
                    messages = item.pop('messages')
                    st.write(
                        {msg_item['role']: msg_item['content'] for msg_item in messages}
                    )
                    st.write(item)
            else:
                with st.chat_message("assistant"):
                    ass_content = item.pop('assistant')
                    st.write(ass_content)
                    st.write(item)

elif selected_section == "Playground":
    st.write("## todo")

elif selected_section == "Static":
    st.write("## todo")
