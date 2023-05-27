import ast
import os
from typing import Dict, List, Union

import orjson
from sparrow import relp


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
            if messages[idx_msg]["uid"] == assistant[idx_ass]["uid"]:
                matches.append(
                    [
                        {"q": messages[idx_msg]["messages"]},
                        {"a": assistant[idx_ass]["assistant"]},
                    ]
                )
                assis_idx_to_remove.append(idx_ass)
                msg_idx_to_remove.append(idx_msg)
                break
    assis_remain = [i for j, i in enumerate(assistant) if j not in assis_idx_to_remove]
    msg_remain = [i for j, i in enumerate(messages) if j not in msg_idx_to_remove]
    remains = [
        [{"q": x["messages"]}, {"a": y["assistant"]}]
        for x in msg_remain
        for y in assis_remain
        if x["uid"] == y["uid"]
    ]
    matches.extend(remains)
    return matches


def load_chat(filepath: str):
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
    try:
        import orjsonl
    except ImportError:
        raise ImportError(
            "import orjsonl error, please `pip install openai_forward[tool]` first"
        )
    content_list = load_chat(log_path)
    orjsonl.save(target_path, content_list)
