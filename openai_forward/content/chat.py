import time
import uuid

import orjson
from fastapi import Request
from httpx._decoders import LineDecoder
from loguru import logger
from orjson import JSONDecodeError

decoder = LineDecoder()


def _parse_iter_line_content(line: str):
    try:
        line_dict = orjson.loads(line)
        return line_dict["choices"][0]["delta"]["content"]
    except JSONDecodeError:
        return ""
    except KeyError:
        return ""


def parse_chat_completions(bytes_: bytes):
    txt_lines = decoder.decode(bytes_.decode("utf-8"))
    line0 = txt_lines[0]
    target_info = dict()
    _start_token = "data: "
    if line0.startswith(_start_token):
        is_stream = True
        line0 = orjson.loads(line0[len(_start_token) :])
        msg = line0["choices"][0]["delta"]
    else:
        is_stream = False
        line0 = orjson.loads("".join(txt_lines))
        msg = line0["choices"][0]["message"]

    target_info["created"] = line0["created"]
    target_info["id"] = line0["id"]
    target_info["model"] = line0["model"]
    target_info["role"] = msg["role"]
    target_info["content"] = msg.get("content", "")
    if not is_stream:
        return target_info
    # loop for stream
    for line in txt_lines[1:]:
        if line in ("", "\n", "\n\n"):
            continue
        elif line.startswith(_start_token):
            target_info["content"] += _parse_iter_line_content(
                line[len(_start_token) :]
            )
        else:
            logger.warning(f"line not startswith data: {line}")
    return target_info


class ChatSaver:
    def __init__(self):
        self.logger = logger.bind(chat=True)

    @staticmethod
    async def parse_payload_to_content(request: Request, route_path: str):
        if route_path == "/v1/chat/completions":
            uid = uuid.uuid4().__str__()
            payload = await request.json()
            msgs = payload["messages"]
            model = payload["model"]
            content = {
                "messages": [{msg["role"]: msg["content"]} for msg in msgs],
                "model": model,
                "forwarded-for": request.headers.get("x-forwarded-for") or "",
                "uid": uid,
                "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            }
        else:
            content = {}
        return content

    @staticmethod
    def parse_bytes_to_content(bytes_: bytes, route_path: str):
        if route_path == "/v1/chat/completions":
            return parse_chat_completions(bytes_)
        else:
            return {}

    def add_chat(self, chat_info: dict):
        self.logger.debug(f"{chat_info}")
