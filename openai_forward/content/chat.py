import os
from pathlib import Path
from typing import Dict, List

import orjson
from fastapi import Request
from httpx._decoders import LineDecoder
from loguru import logger
from orjson import JSONDecodeError
from sparrow import relp

decoder = LineDecoder()


def _parse_iter_line_content(line: str):
    line = line[6:]
    try:
        line_dict = orjson.loads(line)
        return line_dict['choices'][0]['delta']['content']
    except JSONDecodeError:
        return ""
    except KeyError:
        return ""


def parse_chat_completions(bytes_: bytes):
    txt_lines = decoder.decode(bytes_.decode('utf-8'))
    line0 = txt_lines[0]
    target_info = dict()
    if line0.startswith("data:"):
        line0 = orjson.loads(line0[6:])
        msg = line0['choices'][0]['delta']
    else:
        line0 = orjson.loads(line0)
        msg = line0['choices'][0]['message']

    target_info['created'] = line0['created']
    target_info['id'] = line0['id']
    target_info['model'] = line0['model']
    target_info['role'] = msg['role']
    target_info['content'] = msg.get("content", "")
    # loop for stream
    for line in txt_lines[1:]:
        if line in ("", "\n", "\n\n"):
            continue
        elif line.startswith("data: "):
            target_info['content'] += _parse_iter_line_content(line)
        else:
            logger.warning(f"line not startswith data: {line}")
    return target_info


class ChatSaver:
    def __init__(self, max_chat_size=2000, save_interval=2, _dir='./Log'):
        self._chat_list = []
        self._file_idx = 0
        self._save_interval = save_interval
        self._max_chat_file_size = max_chat_size
        self._cur_chat_file_size = 0
        self._log_dir = _dir
        self._init_chat_file()

    @property
    def chat_file(self):
        return os.path.join(self._log_dir, f"chat_{self._file_idx}.txt")

    def _init_chat_file(self):
        _log_dir = Path(self._log_dir)
        if not _log_dir.exists():
            _log_dir.mkdir(parents=True)
        while Path(self.chat_file).exists():
            self._file_idx += 1

    @staticmethod
    async def parse_payload_to_content(request: Request, route_path: str):
        payload = await request.json()
        if route_path == "/v1/chat/completions":
            msgs = payload['messages']
            model = payload['model']
            return {
                "host": request.client.host,
                "model": model,
                "messages": [{msg['role']: msg['content']} for msg in msgs],
            }
        else:
            return {}

    @staticmethod
    def parse_bytes_to_content(bytes_: bytes, route_path: str):
        if route_path == "/v1/chat/completions":
            return parse_chat_completions(bytes_)
        else:
            return {}

    def add_chat(self, chat_info: dict):
        logger.info(str(chat_info))
        self._chat_list.append(chat_info)
        self._cur_chat_file_size += 1
        self._save_chat()

    def _save_chat(self):
        if len(self._chat_list) >= self._save_interval:
            logger.info(f"save chat to {self.chat_file}")
            if self._cur_chat_file_size > self._max_chat_file_size:
                logger.info(f"{self._cur_chat_file_size} is too large, create new file")
                self._file_idx += 1
                self._cur_chat_file_size = 1
            self.dump_chat_list(self._chat_list, self.chat_file, mode='a+', _end='\n')
            self._chat_list = []

    @staticmethod
    def dump_chat_list(
        data: List[Dict], filepath: str, rel=False, mode='w', _sep='\n', _end="\n"
    ):
        str_data = _sep.join([str(i) for i in data]) + _end
        abs_path = relp(filepath, parents=1) if rel else filepath
        with open(abs_path, mode=mode) as f:
            f.write(str_data)

    @staticmethod
    def load_chat_list(filepath: str, rel=False, mode='r', _sep='\n'):
        abs_path = relp(filepath, parents=1) if rel else filepath
        with open(abs_path, mode=mode, encoding='utf-8') as f:
            str_result = f.read()
        result_list = str_result.split(_sep)
        result = [eval(i) for i in result_list if i]
        return result
