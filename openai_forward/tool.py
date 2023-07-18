import ast
import os
from typing import Dict, List, Union

import orjson
from rich import print
from sparrow import MeasureTime, ls, relp


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


def get_matches(messages: List[Dict], assistants: List[Dict]):
    mt = MeasureTime()
    mt.start()
    msg_len, ass_len = len(messages), len(assistants)
    if msg_len != ass_len:
        print(f"message({msg_len}) 与 assistant({ass_len}) 长度不匹配")

    cvt = lambda msg, ass: {
        "datetime": msg.get('datetime'),
        "forwarded-for": msg.get("forwarded-for"),
        "model": msg.get("model"),
        "messages": msg.get("messages"),
        "assistant": ass.get("assistant"),
    }

    msg_uid_dict = {m.pop("uid"): m for m in messages}
    ass_uid_dict = {a.pop("uid"): a for a in assistants}
    matches = [
        cvt(msg_uid_dict[uid], ass_uid_dict[uid])
        for uid in msg_uid_dict
        if uid in ass_uid_dict
    ]

    ref_len = max(msg_len, ass_len)
    if len(matches) != ref_len:
        print(f"存在{ref_len - len(matches)}条未匹配数据")
    mt.show_interval("计算耗时：")
    return matches


def parse_log_to_list(log_path: str):
    with open(log_path, "r", encoding="utf-8") as f:
        messages, assistant = [], []
        for line in f.readlines():
            content: dict = ast.literal_eval(line)
            if content.get("messages"):
                messages.append(content)
            else:
                assistant.append(content)
    return messages, assistant


def convert_chatlog_to_jsonl(log_path: str, target_path: str):
    message_list, assistant_list = parse_log_to_list(log_path)
    content_list = get_matches(messages=message_list, assistants=assistant_list)
    json_dump(content_list, target_path, indent_2=True)


def sort_logname_by_datetime(log_path: str):
    return ls(log_path, "*.log", relp=False)


def convert_folder_to_jsonl(folder_path: str, target_path: str):
    log_files = sort_logname_by_datetime(folder_path)
    messages = []
    assistants = []
    for log_path in log_files:
        msg, ass = parse_log_to_list(log_path)

        msg_len, ass_len = len(msg), len(ass)
        if msg_len != ass_len:
            print(f"{log_path=} message({msg_len}) 与 assistant({ass_len}) 长度不匹配")
        messages.extend(msg)
        assistants.extend(ass)
    content_list = get_matches(messages=messages, assistants=assistants)
    json_dump(content_list, target_path, indent_2=True)
