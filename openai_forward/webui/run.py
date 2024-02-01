import os
import pickle
import threading
import time

import orjson
import pandas as pd
import streamlit as st
import zmq
from flaxkv.helper import SimpleQueue

from openai_forward.webui.chat import ChatData, render_chat_log_message
from openai_forward.webui.helper import mermaid
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
def get_global_vars():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    # socket.setsockopt(zmq.CONNECT_TIMEOUT, 20000) # 20s
    openai_forward_host = os.environ.get("OPENAI_FORWARD_HOST", "localhost")
    socket.connect(f"tcp://{openai_forward_host}:15555")

    log_socket = context.socket(zmq.DEALER)
    log_socket.connect(f"tcp://{openai_forward_host}:15556")
    log_socket.send_multipart([b"/subscribe", b"0"])

    def worker(log_socket: zmq.Socket, q: SimpleQueue):
        while True:
            message = log_socket.recv_multipart()
            uid, msg = message
            q.put((uid, msg))

    q = SimpleQueue(maxsize=100)
    threading.Thread(target=worker, args=(log_socket, q)).start()
    config = Config().come_from_env()
    chat_data = ChatData(100, render_chat_log_message)
    return {
        "socket": socket,
        "log_socket": log_socket,
        "q": q,
        "config": config,
        "chat_data": chat_data,
    }


if 'socket' not in st.session_state:
    st.session_state.update(get_global_vars())

config = st.session_state['config']

with st.sidebar:
    selected_section = st.radio(
        "Select a configuration section",
        (
            "Forward",
            "API Key && Level",
            "Cache",
            "Rate Limit",
            "Other",
            "Real-time Logs",
            "Playground",
            "Statistics",
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

    st.subheader("AI Forward")
    with st.form("forward_configuration", border=False):
        df = pd.DataFrame([i.to_dict() for i in forward_config.forward])
        edited_df = st.data_editor(
            df, num_rows="dynamic", key="editor1", use_container_width=True
        )

        with st.expander("See explanation"):
            df_demo = pd.DataFrame(
                [
                    {
                        'base_url': 'https://api.openai.com',
                        'route': '/',
                        'type': 'openai',
                    },
                    {
                        "base_url": "https://generativelanguage.googleapis.com",
                        "route": "/gemini",
                        "type": "general",
                    },
                ]
            )

            st.write(df_demo)
            st.write(
                "> 在以上设置下:  \n"
                "> - openai转发地址为： http://localhost:8000/  \n"
                "> - type=openai转发下的服务需要满足openai api 格式才能被正确解析  \n\n"
                "> - gemini转发地址为： http://localhost:8000/gemini  \n"
                "> - type=general转发下的服务可以是任何服务（暂不支持websocket)"
            )

        st.write("#")

        submitted = st.form_submit_button("Save", use_container_width=True)
        if submitted:
            forward_config.forward = [
                ForwardItem(row["base_url"], row["route"], row["type"])
                for i, row in edited_df.iterrows()
                if row["route"] is not None and row["base_url"] is not None
            ]

            print(forward_config.convert_to_env())


def display_api_key_configuration():

    with st.expander("See explanation"):
        st.write(
            """
> - 不同level对应不同权限，可以定义不同权限可以访问哪些模型。 例如, level为1，只可访问gpt-3.5-turbo；level为2，可访问embedding 和tts等等。(level为0，全权限，可访问任何模型，不可更改)
> - 对于api key而言，level的意义是区分该api key自身是否有权限访问哪些模型。每个api key可对应多个level，因为这些level不必是从属关系。
> - 对于forward key而言，每个key对应一个level，level表示它可以访问该level对应的所有api key。
"""
        )
        mermaid(
            """
graph TD
fk1(FK1) --> level0(Level 0)
fk2(FK2) --> level0
level0 --> sk1(SK1)
level0 --> sk2(SK2)
level0 --> sk3(SK3)

fk3(FK3) --> level1(Level 1)
level1 --> sk4(SK4)
level1 --> sk3(SK3)

fk(FK_x) --> level_n(Level n)
level_n --> sk_n(SK_n)
"""
        )

    # check openai models:
    # from openai import OpenAI
    # client = OpenAI(api_key=)
    # openai_model_list = [i.id for i in client.models.list()]
    # openai_model_list.sort()

    openai_model_list = [
        'babbage-002',
        'dall-e-2',
        'dall-e-3',
        'davinci-002',
        'gpt-3.5-turbo',
        'gpt-3.5-turbo-0301',
        'gpt-3.5-turbo-0613',
        'gpt-3.5-turbo-1106',
        'gpt-3.5-turbo-16k',
        'gpt-3.5-turbo-16k-0613',
        'gpt-3.5-turbo-instruct',
        'gpt-3.5-turbo-instruct-0914',
        'gpt-4',
        'gpt-4-0125-preview',
        'gpt-4-0613',
        'gpt-4-1106-preview',
        'gpt-4-turbo-preview',
        'gpt-4-vision-preview',
        'text-embedding-3-large',
        'text-embedding-3-small',
        'text-embedding-ada-002',
        'tts-1',
        'tts-1-1106',
        'tts-1-hd',
        'tts-1-hd-1106',
        'whisper-1',
    ]

    api_key = config.api_key

    st.subheader("Key Level")

    level_model_map = {}
    api_key.level: dict
    # sort api_key.level by key, so that level 1 is always the first one
    sorted_list = sorted(api_key.level.items(), key=lambda x: x[0], reverse=False)
    levels = [i[0] for i in sorted_list]
    models_list = [i[1] for i in sorted_list]
    num_levels = st.number_input(
        '请选择你需定义几个level (不包含level 0,它是全权限)', 0, 1000, len(levels), 1
    )
    for level in range(num_levels):
        level += 1
        models = st.multiselect(
            f'请选择该`{level=}`可访问的模型',
            openai_model_list,
            default=models_list[min(level - 1, len(levels) - 1)],
            key=f"level_{level}",
        )
        level_model_map[level] = models

    with st.form("api_key_form", border=False):
        st.subheader("OpenAI API Key")
        df = pd.DataFrame(
            [
                {'api_key': key, 'level': value}
                for key, value in api_key.openai_key.items()
            ]
        )
        edited_df = st.data_editor(
            df, num_rows="dynamic", key="editor1", use_container_width=True
        )

        st.subheader("Forward Key")
        df2 = pd.DataFrame(
            [
                {'api_key': key, 'level': value}
                for key, value in api_key.forward_key.items()
            ]
        )
        edited_df2 = st.data_editor(
            df2, num_rows="dynamic", key="editor2", use_container_width=True
        )

        submitted = st.form_submit_button("Save", use_container_width=True)
        if submitted:
            api_key.openai_key = {
                row["api_key"]: row["level"] for i, row in edited_df.iterrows()
            }

            api_key.forward_key = {
                row["api_key"]: row["level"] for i, row in edited_df2.iterrows()
            }

            api_key.level = level_model_map

            print(api_key.convert_to_env())


def display_cache_configuration():
    cache = config.cache

    with st.container():
        st.subheader("Cache Configuration")

        cache_openai = st.checkbox("Cache OpenAI route", cache.cache_openai)
        cache_default_request_caching_value = st.checkbox(
            "For OpenAI API, return using cache by default",
            cache.default_request_caching_value,
            disabled=not cache_openai,
        )

        cache_general = st.checkbox("Cache General route", cache.cache_general)

        cache_backend = st.selectbox(
            "Cache Backend",
            ["MEMORY", "LMDB", "LevelDB"],
            index=["memory", "lmdb", "leveldb"].index(cache.backend.lower()),
        )

        cache_root_path_or_url = st.text_input(
            "Root Path or URL",
            cache.root_path_or_url,
            disabled=cache_backend == "MEMORY",
        )

        df = pd.DataFrame([{"cache_route": i} for i in cache.cache_routes])
        edited_df = st.data_editor(
            df, num_rows="dynamic", key="editor1", use_container_width=True
        )

        submitted = st.button("Save", use_container_width=True)
        if submitted:
            cache.cache_openai = cache_openai
            cache.cache_general = cache_general

            cache.backend = cache_backend
            cache.root_path_or_url = cache_root_path_or_url
            cache.default_request_caching_value = cache_default_request_caching_value

            cache.cache_routes = [
                row['cache_route']
                for i, row in edited_df.iterrows()
                if row["cache_route"] is not None
            ]

            print(cache.convert_to_env())


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
            ['fixed-window', 'moving-window', 'fixed-window-elastic-expiry'],
            index=[
                'fixed-window',
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
            "Timeout (seconds)", value=int(config.timeout), min_value=1, step=1
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

elif selected_section == "API Key && Level":
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
        chat_data: ChatData = st.session_state['chat_data']
        chat_data.render_all_messages()
        while True:
            uid, msg = q.get()
            uid: bytes
            print(f"{uid=}")
            item = orjson.loads(msg)
            if uid.startswith(b"0"):
                item['user_role'] = True
            else:
                item['assistant_role'] = True

            chat_data.add_message(item)

elif selected_section == "Playground":
    st.write("## todo")

elif selected_section == "Statistics":
    st.write("## todo")
