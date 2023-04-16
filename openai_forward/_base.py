import orjson
from orjson import JSONDecodeError
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import StreamingResponse, RedirectResponse, FileResponse
from loguru import logger
import httpx
from httpx._decoders import LineDecoder
from starlette.background import BackgroundTask
import os
from dotenv import load_dotenv
from sparrow import yaml_dump, yaml_load
from pathlib import Path
from threading import Thread
from .config import setting_log

load_dotenv()
setting_log(log_name="openai_forward.log")


class OpenaiBase:
    default_api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com")
    LOG_CHAT = os.environ.get("LOG_CHAT", "False").lower() == "true"
    stream_timeout = 20
    timeout = 30
    non_stream_timeout = 30
    allow_ips = []
    chat_info_list = []
    _current_chat_info = []
    _chat_file_idx = 0
    _save_freq_idx = 1

    @classmethod
    def save_chat_info(cls, save_freq=0.02, save_threshold=4000):
        chat_file = f"chat_{cls._chat_file_idx}.yaml"
        if Path(chat_file).exists():
            chat_info_list = yaml_load(chat_file)
        else:
            chat_info_list = []

        cls.chat_info_list.append(cls._current_chat_info)
        cls._current_chat_info = []
        chat_info_list.extend(cls.chat_info_list)
        if len(chat_info_list) >= save_threshold:
            cls._chat_file_idx += 1
            chat_file = f"chat_{cls._chat_file_idx}.yaml"
        if len(chat_info_list) >= save_threshold * save_freq*cls._save_freq_idx:
            cls._save_freq_idx += 1
            yaml_dump(chat_file, chat_info_list)
            cls.chat_info_list = []

    def add_allowed_ip(self, ip: str):
        if ip == "*":
            ...
        else:
            self.allow_ips.append(ip)

    def validate_request_host(self, ip):
        if ip == "*" or ip in self.allow_ips:
            return True
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Forbidden, please add {ip=} to `allow_ips`")

    @staticmethod
    def _parse_iter_line_content(line: str):
        line = line[6:]
        try:
            line_dict = orjson.loads(line)
            return line_dict['choices'][0]['delta']['content']
        except JSONDecodeError:
            return ""
        except KeyError:
            return ""

    @classmethod
    def log_chat_completions(cls, bytes_: bytes):
        decoder = LineDecoder()
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
                target_info['content'] += cls._parse_iter_line_content(line)
            else:
                logger.warning(f"line not startswith data: {line}")
        logger.info(f"{target_info}")
        cls._current_chat_info.append({target_info['role']: target_info['content']})
        Thread(target=cls.save_chat_info).start()

    @classmethod
    async def aiter_bytes(cls, r: httpx.Response):
        bytes_ = b''
        async for chunk in r.aiter_bytes():
            bytes_ += chunk
            yield chunk
        try:
            cls.log_chat_completions(bytes_)
        except Exception as e:
            logger.warning(e)

    @classmethod
    async def _reverse_proxy(cls, request: Request):
        client: httpx.AsyncClient = request.app.state.client
        url = httpx.URL(path=request.url.path, query=request.url.query.encode('utf-8'))
        headers = dict(request.headers)
        auth = headers.pop("authorization", None)
        if auth and str(auth).startswith("Bearer sk-"):
            tmp_headers = {'Authorization': auth}
        elif cls.default_api_key:
            auth = "Bearer " + cls.default_api_key
            tmp_headers = {'Authorization': auth}
        else:
            tmp_headers = {}

        headers.pop("host", None)
        # headers.pop("user-agent", None)
        headers.update(tmp_headers)
        if cls.LOG_CHAT:
            try:
                input_info = await request.json()
                msgs = input_info['messages']
                cls._current_chat_info.append(
                    {
                        "model": input_info['model'],
                        "messages": [{msg['role']: msg['content']} for msg in msgs],
                    }
                )
                logger.info(f"{input_info}")
            except Exception as e:
                logger.warning(e)
        req = client.build_request(
            request.method, url, headers=headers,
            content=request.stream(),
            timeout=cls.timeout,
        )
        r = await client.send(req, stream=True)

        aiter_bytes = cls.aiter_bytes(r) if cls.LOG_CHAT else r.aiter_bytes()
        return StreamingResponse(
            aiter_bytes,
            status_code=r.status_code,
            # headers=r.headers,
            media_type=r.headers.get("content-type"),
            background=BackgroundTask(r.aclose)
        )
