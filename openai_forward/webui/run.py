import ast
import os
import pickle
import secrets
import threading

import orjson
import pandas as pd
import streamlit as st
import zmq
from flaxkv.helper import SimpleQueue

from openai_forward.config.interface import *
from openai_forward.webui.chat import ChatData
from openai_forward.webui.helper import mermaid

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
    restart_port = int(os.environ.get('WEBUI_RESTART_PORT', 15555))
    socket.connect(f"tcp://{openai_forward_host}:{restart_port}")

    log_socket = context.socket(zmq.DEALER)
    webui_log_port = int(os.environ.get("WEBUI_LOG_PORT", 15556))
    log_socket.connect(f"tcp://{openai_forward_host}:{webui_log_port}")
    log_socket.send_multipart([b"/subscribe", b"0"])

    def worker(log_socket: zmq.Socket, q: SimpleQueue):
        while True:
            message = log_socket.recv_multipart()
            uid, msg = message
            q.put((uid, msg))

    q = SimpleQueue(maxsize=100)
    threading.Thread(target=worker, args=(log_socket, q)).start()
    config = Config().come_from_env()
    chat_data = ChatData(100)
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

    st.write("---")

    if st.button(
        "Apply and Restart", help="Saving configuration and reloading openai forward"
    ):
        with st.spinner("Saving configuration and reloading openai forward..."):
            # env_dict = config.convert_to_env(set_env=False)
            socket = st.session_state['socket']
            socket.send(pickle.dumps(config.to_dict()))
            message: bytes = socket.recv()

        st.success(message.decode())

    if st.button(
        "Export to config.yaml",
    ):
        yaml_str = yaml.dump(config.to_dict(), default_flow_style=False)
        yaml_bytes = yaml_str.encode('utf-8')
        download = st.download_button(
            use_container_width=True,
            label="Export",
            data=yaml_bytes,
            file_name="config.yaml",
            mime="text/plain",
        )


def display_forward_configuration():
    st.subheader("AI Forward")
    with st.form("forward_configuration", border=False):
        df = pd.DataFrame([i.to_dict() for i in config.forward])
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

        # st.write("#")

        submitted = st.form_submit_button("Save", use_container_width=True)
        if submitted:
            config.forward = [
                ForwardItem(row["base_url"], row["route"], row["type"])
                for i, row in edited_df.iterrows()
                if row["route"] is not None and row["base_url"] is not None
            ]

            print("save forward config success")


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
    # from rich import print
    # client = OpenAI(api_key="sk-")
    # openai_model_list = [i.id for i in client.models.list()]
    # openai_model_list.sort()
    # print(openai_model_list)
    # print(len(openai_model_list))

    openai_model_list = [
        'babbage-002',
        'dall-e-2',
        'dall-e-3',
        'davinci-002',
        'gpt-3.5-turbo',
        'gpt-3.5-turbo-0125',
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
        'gpt-4-turbo',
        'gpt-4-turbo-2024-04-09',
        'gpt-4-turbo-preview',
        # https://platform.openai.com/docs/models#current-model-aliases
        'chatgpt-4o-latest',
        'gpt-4o',
        # 'gpt-4o-2024-05-13',
        'gpt-4o-mini',
        # 'gpt-4o-mini-2024-07-18',
        'o1',
        'o1-mini',
        'o3-mini',
        'o1-preview',
        'gpt-4o-realtime-preview',
        'gpt-4o-mini-realtime-preview',
        'gpt-4o-audio-preview',
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

        def to_list(x: str):
            x = str(x).replace('，', ',').strip()
            if x == '':
                return []
            try:
                x = ast.literal_eval(x)
                if isinstance(x, list):
                    return x
                if isinstance(x, tuple):
                    return list(x)
                else:
                    return [x]
            except:
                return str(x).split(',')

        to_int_list = lambda x: [int(i) for i in x]
        df = pd.DataFrame(
            [
                {'api_key': key, 'level': str(value)}
                for key, value in api_key.openai_key.items()
            ]
        )
        edited_df = st.data_editor(
            df, num_rows="dynamic", key="editor1", use_container_width=True
        )

        st.subheader("Forward Key")
        df2 = pd.DataFrame(
            [
                {'level': int(key), 'api_key': str(value)}
                for key, value in api_key.forward_key.items()
            ]
        )
        edited_df2 = st.data_editor(
            df2, num_rows="dynamic", key="editor2", use_container_width=True
        )

        submitted = st.form_submit_button("Save", use_container_width=True)
        if submitted:
            api_key.openai_key = {
                row["api_key"]: to_int_list(to_list(row["level"]))
                for i, row in edited_df.iterrows()
            }

            api_key.forward_key = {
                int(row["level"]): to_list(row["api_key"])
                for i, row in edited_df2.iterrows()
            }

            api_key.level = level_model_map

            print("save api key success")


def display_cache_configuration():
    cache = config.cache

    with st.container():
        st.subheader("Cache Configuration")

        cache_openai = st.checkbox("Cache OpenAI route", cache.openai)
        cache_default_request_caching_value = st.checkbox(
            "For OpenAI API, return using cache by default",
            cache.default_request_caching_value,
            disabled=not cache_openai,
        )

        cache_general = st.checkbox("Cache General route", cache.general)

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

        df = pd.DataFrame([{"cache_route": i} for i in cache.routes])
        edited_df = st.data_editor(
            df, num_rows="dynamic", key="editor1", use_container_width=True
        )

        submitted = st.button("Save", use_container_width=True)
        if submitted:
            cache.openai = cache_openai
            cache.general = cache_general

            cache.backend = cache_backend
            cache.root_path_or_url = cache_root_path_or_url
            cache.default_request_caching_value = cache_default_request_caching_value

            cache.routes = [
                row['cache_route']
                for i, row in edited_df.iterrows()
                if row["cache_route"] is not None
            ]

            print("save cache success")


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
            [i.to_dict_str() for i in rate_limit.token_rate_limit]
        )
        edited_token_rate_limit_df = st.data_editor(
            token_rate_limit_df,
            num_rows="dynamic",
            key="editor_token_rate_limit",
            use_container_width=True,
        )

        st.subheader("Request Rate Limit")
        req_rate_limit_df = pd.DataFrame(
            [i.to_dict_str() for i in rate_limit.req_rate_limit]
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
                RateLimitType(row["route"], ast.literal_eval(row["value"]))
                for _, row in edited_token_rate_limit_df.iterrows()
            ]

            rate_limit.req_rate_limit = [
                RateLimitType(row["route"], ast.literal_eval(row["value"]))
                for _, row in edited_req_rate_limit_df.iterrows()
            ]

            print("save rate limit success")


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

            print("save other config success")


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
    render_with_markdown = st.toggle("Using Markdown to render", value=True)
    st.write("\n")

    q = st.session_state['q']
    chat_data: ChatData = st.session_state['chat_data']
    chat_data.render_all_messages(markdown=render_with_markdown)
    while True:
        uid, msg = q.get()
        uid: bytes
        item = orjson.loads(msg)
        item['uid'] = uid[1:].decode()
        if uid.startswith(b"0"):
            item['user_role'] = True
        else:
            item['assistant_role'] = True

        chat_data.add_message(item, markdown=render_with_markdown)

elif selected_section == "Playground":
    st.write("## todo")

elif selected_section == "Statistics":
    st.write("## todo")
