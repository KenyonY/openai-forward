import time
import uuid
from typing import List

import orjson
from fastapi import Request
from loguru import logger
from orjson import JSONDecodeError

from .decode import parse_to_lines


def _parse_iter_line_content(line: str):
    try:
        line_dict = orjson.loads(line)
        return line_dict["choices"][0]["delta"]["content"]
    except JSONDecodeError:
        return ""
    except KeyError:
        return ""


class ChatSaver:
    def __init__(self):
        self.logger = logger.bind(chat=True)

    @staticmethod
    async def parse_payload_to_content(request: Request):
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
        return content

    @staticmethod
    def parse_byte_list_to_target(byte_list: List[bytes]):
        txt_lines = parse_to_lines(byte_list)

        line0 = txt_lines[0]
        target_info = dict()
        _start_token = "data: "
        if line0.startswith(_start_token):
            stream = True
            line0 = orjson.loads(line0[len(_start_token) :])
            msg = line0["choices"][0]["delta"]
        else:
            stream = False
            line0 = orjson.loads("".join(txt_lines))
            msg = line0["choices"][0]["message"]

        target_info["created"] = line0["created"]
        target_info["id"] = line0["id"]
        target_info["model"] = line0["model"]
        target_info["role"] = msg["role"]
        target_info["content"] = msg.get("content", "")
        if not stream:
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

    def add_chat(self, chat_info: dict):
        self.logger.debug(f"{chat_info}")
