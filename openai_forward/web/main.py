import pandas as pd
import streamlit as st

from openai_forward.web.interface import *

# st.set_page_config(
#      page_title='config',
#      layout="wide",
#      initial_sidebar_state="expanded",
# )
# 加载或初始化配置
# 这里假设你有一个函数来加载配置，如果没有，则创建一个新的
config = Config()


def save_config(config):
    # 实现保存配置的功能
    pass


# 使用侧边栏为不同配置部分创建选项卡
with st.sidebar:
    selected_section = st.radio(
        "Select a configuration section",
        ("Forward", "API Key", "Cache", "Rate Limit", "Other"),
    )


def display_forward_configuration(forward_config):
    with st.container():
        tab1, tab2 = st.tabs(["OpenAI", "General"])
        with tab1:
            st.subheader("OpenAI Forward")
            df = pd.DataFrame([i.to_dict() for i in forward_config.openai])
            print(df)
            edited_df = st.data_editor(df, num_rows="dynamic", key="editor1", width=500)
            forward_config.openai = [
                ForwardItem(row["base_url"], row["route_prefix"])
                for i, row in edited_df.iterrows()
            ]
        with tab2:
            st.subheader("General Forward")
            df2 = pd.DataFrame([i.to_dict() for i in forward_config.general])
            edited_df2 = st.data_editor(
                df2, num_rows="dynamic", key="editor2", width=500
            )
            forward_config.general = [
                ForwardItem(row["base_url"], row["route_prefix"])
                for i, row in edited_df2.iterrows()
            ]

        print(forward_config)


if selected_section == "Forward":
    display_forward_configuration(config.forward)

elif selected_section == "API Key":
    with st.container():
        api_key = config.api_key
        tab1, tab2, tab3 = st.tabs(["api key", "forward key", "Level"])
        with tab1:
            st.subheader("OpenAI Key")
            df = pd.DataFrame(
                [i.to_dict() for i in api_key.openai_key]
                # [{"api_key": "sk-***", "level": 0}]
            )
            edited_df = st.data_editor(df, num_rows="dynamic", key="editor1", width=500)
            api_key.openai_key = [
                ApiKeyItem(row["api_key"], row["level"])
                for i, row in edited_df.iterrows()
            ]
        with tab2:
            st.subheader("Forward Key")
            df = pd.DataFrame([i.to_dict() for i in api_key.forward_key])
            edited_df = st.data_editor(df, num_rows="dynamic", key="editor2", width=500)
            api_key.forward_key = [
                ApiKeyItem(row["api_key"], row["level"])
                for i, row in edited_df.iterrows()
            ]
        with tab3:
            st.subheader("level")
            df = pd.DataFrame([i.to_dict() for i in api_key.level])
            edited_df = st.data_editor(df, num_rows="dynamic", key="editor3", width=500)
            api_key.level = [
                ApiKeyLevel(level=row["level"], models=row["models"])
                for i, row in edited_df.iterrows()
            ]

        st.write("说明： xxx")
        print(api_key)

elif selected_section == "Cache":
    # 添加与Cache相关的控件
    pass
elif selected_section == "Rate Limit":
    # 添加与Rate Limit相关的控件
    pass
elif selected_section == "Other":
    # 添加与Other（如日志、时区等）相关的控件
    pass

# 保存按钮
# if st.button("Save Configuration"):
#     save_config(config)
#     st.success("Configuration saved!")
