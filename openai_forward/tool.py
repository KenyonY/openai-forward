import ast
import os
from typing import Dict, List, Union

import orjson
from rich import print
from sparrow import MeasureTime, relp


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
    mt = MeasureTime()
    mt.start()
    msg_len, ass_len = len(messages), len(assistant)
    if msg_len != ass_len:
        print(f"message({msg_len}) 与 assistant({ass_len}) 长度不匹配")
    matches = []
    assis_idx_to_remove, msg_idx_to_remove = [], []

    def cvt(msg: dict, ass: dict):
        return {
            "datetime": msg.get('datetime'),
            "forwarded-for": msg.get("forwarded-for"),
            "model": msg.get("model"),
            "messages": msg.get("messages"),
            "assistant": ass.get("assistant"),
        }

    for idx_msg in range(len(messages)):
        win = min(max(abs(ass_len - msg_len), 16), len(messages) - 1)
        range_list = [idx_msg + (i + 1) // 2 * (-1) ** (i + 1) for i in range(win)]
        # range_list = [idx_msg + 0, idx_msg + 1, idx_msg - 1, idx_msg + 2, idx_msg - 2, ...]
        for idx_ass in range_list:
            if idx_ass >= len(assistant):
                break
            if messages[idx_msg]["uid"] == assistant[idx_ass]["uid"]:
                matches.append(cvt(messages[idx_msg], assistant[idx_ass]))
                assis_idx_to_remove.append(idx_ass)
                msg_idx_to_remove.append(idx_msg)
                break
    assis_remain = [i for j, i in enumerate(assistant) if j not in assis_idx_to_remove]
    msg_remain = [i for j, i in enumerate(messages) if j not in msg_idx_to_remove]
    remains = [
        cvt(x, y) for x in msg_remain for y in assis_remain if x["uid"] == y["uid"]
    ]
    matches.extend(remains)
    ref_len = max(msg_len, ass_len)
    if len(matches) != ref_len:
        print(f"存在{ref_len-len(matches)}条未匹配数据")
    mt.show_interval("计算耗时：")
    return matches


def parse_chat_log(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        messages, assistant = [], []
        for line in f.readlines():
            content: dict = ast.literal_eval(line)
            if content.get("messages"):
                messages.append(content)
            else:
                assistant.append(content)
        return get_matches(messages, assistant)


def convert_chatlog_to_jsonl(log_path: str, target_path: str):
    content_list = parse_chat_log(log_path)
    json_dump(content_list, target_path, indent_2=True)
