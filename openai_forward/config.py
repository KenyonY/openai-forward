import ast
import logging
import os
import sys
import time
from typing import Dict, List, Union

import orjson
from loguru import logger
from rich import print
from rich.panel import Panel
from rich.table import Table
from sparrow import relp


def print_startup_info(base_url, route_prefix, api_key, forward_key, log_chat):
    try:
        from dotenv import load_dotenv

        load_dotenv(".env")
    except Exception:
        ...
    route_prefix = route_prefix or "/"
    api_key_info = True if len(api_key) else False
    forward_key_info = True if len(forward_key) else False
    table = Table(title="", box=None, width=100)
    table.add_column("base-url", justify="left", style="#df412f")
    table.add_column("route-prefix", justify="center", style="#df412f")
    table.add_column("openai-api-key", justify="center", style="green")
    table.add_column("forward-key", justify="center", style="green")
    table.add_column("Log-chat", justify="center", style="green")
    table.add_column("Log-dir", justify="center", style="#f5bb00")
    table.add_row(
        base_url,
        route_prefix,
        str(api_key_info),
        str(forward_key_info),
        str(log_chat),
        "./Log/chat.log",
    )
    print(Panel(table, title="🤗openai-forward is ready to serve!", expand=False))


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 6
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setting_log(save_file=False, log_name="openai_forward", multi_process=True):
    # TODO 修复时区配置
    if os.environ.get("TZ") == "Asia/Shanghai":
        os.environ["TZ"] = "UTC-8"
        if hasattr(time, "tzset"):
            time.tzset()

    logging.root.handlers = [InterceptHandler()]
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    config_handlers = [
        {"sink": sys.stdout, "level": "DEBUG"},
        {
            "sink": f"./Log/chat.log",
            "enqueue": multi_process,
            "rotation": "20 MB",
            "filter": lambda record: "chat" in record["extra"],
            "format": "{message}",
        },
    ]
    if save_file:
        config_handlers += [
            {
                "sink": f"./Log/{log_name}.log",
                "enqueue": multi_process,
                "rotation": "100 MB",
                "level": "INFO",
            }
        ]

    logger_config = {"handlers": config_handlers}
    logger.configure(**logger_config)


def yaml_dump(data, filepath, rel_path=False, mode="w"):
    abs_path = relp(filepath, parents=1) if rel_path else filepath
    from yaml import dump

    try:
        from yaml import CDumper as Dumper
    except ImportError:
        from yaml import Dumper
    with open(abs_path, mode=mode, encoding="utf-8") as fw:
        fw.write(dump(data, Dumper=Dumper, allow_unicode=True, indent=4))


def yaml_load(filepath, rel_path=False, mode="r"):
    abs_path = relp(filepath, parents=1) if rel_path else filepath
    from yaml import load

    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader
    with open(abs_path, mode=mode, encoding="utf-8") as stream:
        content = load(stream, Loader=Loader)
    return content


def json_load(filepath: str, rel=False, mode="rb"):
    abs_path = relp(filepath, parents=1) if rel else filepath
    with open(abs_path, mode=mode) as f:
        return orjson.loads(f.read())


def json_dump(
    data: Union[List, Dict], filepath: str, rel=False, indent_2=False, mode="wb"
):
    orjson_option = 0
    if indent_2:
        orjson_option = orjson.OPT_INDENT_2
    abs_path = relp(filepath, parents=1) if rel else filepath
    with open(abs_path, mode=mode) as f:
        f.write(orjson.dumps(data, option=orjson_option))


def str2list(s: str, sep=" "):
    if s:
        return [i.strip() for i in s.split(sep) if i.strip()]
    else:
        return []


def env2list(env_name: str, sep=" "):
    return str2list(os.environ.get(env_name, "").strip(), sep=sep)


def get_matches(messages: List[Dict], assistant: List[Dict]):
    matches = []
    assis_idx_to_remove, msg_idx_to_remove = [], []
    for idx_msg in range(len(messages)):
        win = min(5, len(messages) - 1)
        range_list = [idx_msg + (i + 1) // 2 * (-1) ** (i + 1) for i in range(win)]
        # range_list = [idx_msg + 0, idx_msg + 1, idx_msg - 1, idx_msg + 2, idx_msg - 2, ...]
        for idx_ass in range_list:
            if idx_ass >= len(assistant):
                break
            if messages[idx_msg]['uid'] == assistant[idx_ass]['uid']:
                matches.append(
                    [
                        {"q": messages[idx_msg]['messages']},
                        {"a": assistant[idx_ass]['assistant']},
                    ]
                )
                assis_idx_to_remove.append(idx_ass)
                msg_idx_to_remove.append(idx_msg)
                break
    assis_remain = [i for j, i in enumerate(assistant) if j not in assis_idx_to_remove]
    msg_remain = [i for j, i in enumerate(messages) if j not in msg_idx_to_remove]
    remains = [
        [{"q": x['messages']}, {"a": y['assistant']}]
        for x in msg_remain
        for y in assis_remain
        if x['uid'] == y['uid']
    ]
    matches.extend(remains)
    return matches


def load_chat(filepath: str):
    with open(filepath, 'r', encoding='utf-8') as f:
        messages, assistant = [], []
        for line in f.readlines():
            content: dict = ast.literal_eval(line)
            if content.get('messages'):
                messages.append(content)
            else:
                assistant.append(content)
        return get_matches(messages, assistant)
