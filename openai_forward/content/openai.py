import os
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

import orjson
from fastapi import Request
from loguru import logger
from orjson import JSONDecodeError

from ..helper import get_client_ip, get_unique_id, route_prefix_to_str
from ..settings import DEFAULT_REQUEST_CACHING_VALUE
from .helper import markdown_print, parse_sse_buffer, print


class LoggerBase(ABC):
    def __init__(self, route_prefix: str, _suffix: str):
        _prefix = route_prefix_to_str(route_prefix)
        kwargs = {f"{_prefix}{_suffix}": True}
        self.logger = logger.bind(**kwargs)

        self.webui = False
        if os.environ.get("OPENAI_FORWARD_WEBUI", "false").strip().lower() == 'true':
            self.webui = True

            import zmq
            from flaxkv.helper import SimpleQueue

            context = zmq.Context()
            socket = context.socket(zmq.DEALER)
            socket.connect("tcp://localhost:15556")

            self.q = SimpleQueue(maxsize=200)

            def _worker():
                while True:
                    message: dict = self.q.get(block=True)
                    if message.get("payload"):
                        uid = b"0" + message["uid"].encode()
                        msg = message["payload"]
                    else:
                        uid = b"1" + message["uid"].encode()
                        msg = message["result"]
                        msg = orjson.dumps(msg)

                    socket.send_multipart([uid, msg])

            threading.Thread(target=_worker, daemon=True).start()

    @staticmethod
    @abstractmethod
    def parse_payload(request: Request, raw_payload) -> Tuple[Dict, bytes]:
        pass

    @staticmethod
    @abstractmethod
    def parse_bytearray(buffer: bytearray) -> Dict:
        pass

    @abstractmethod
    def log_result(self, *args, **kwargs):
        pass


class CompletionLogger(LoggerBase):
    def __init__(self, route_prefix: str):
        """
        Initialize the Completions logger with a route prefix.

        Args:
            route_prefix (str): The prefix used for routing, e.g., '/openai'.
        """
        super().__init__(route_prefix, "_completion")

    @staticmethod
    def parse_payload(request: Request, raw_payload):
        uid = get_unique_id()
        payload = orjson.loads(raw_payload)
        print(f"{payload=}")

        content = {
            "prompt": payload['prompt'],
            "model": payload['model'],
            "stream": payload.get("stream", True),
            "temperature": payload.get("temperature", 1),
            "ip": get_client_ip(request) or "",
            "uid": uid,
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }
        return content, raw_payload

    @staticmethod
    def parse_bytearray(buffer: bytearray):
        """
        Parses a bytearray, usually from an API response, into a dictionary containing various information.

        Args:
            buffer (List[bytes]): A list of bytes to parse.

        Returns:
            Dict[str, Any]: A dictionary containing metadata and content. The keys include:
                - "text" (str)
        """
        start_token = "data: "
        start_token_len = len(start_token)
        if buffer.startswith(b'data: '):
            txt_lines = parse_sse_buffer(buffer)
            stream = True
            first_dict = orjson.loads(txt_lines[0][start_token_len:])
            text = first_dict["choices"][0]["text"]
        else:
            stream = False
            first_dict = orjson.loads(buffer)
            text = first_dict["choices"][0]["text"]

        target_info = dict()
        verbose = False
        if verbose:
            target_info["created"] = first_dict["created"]
            target_info["id"] = first_dict["id"]
            target_info["model"] = first_dict["model"]
            target_info["usage"] = first_dict.get("usage")

        target_info['text'] = text

        if not stream:
            return target_info

        # loop for stream
        for line in txt_lines[1:]:
            if line.startswith(start_token):
                try:
                    line_dict = orjson.loads(line[start_token_len:])
                    text += line_dict["choices"][0]["text"]
                except (JSONDecodeError, KeyError):
                    pass
        target_info['text'] = text
        return target_info

    def log_result(self, chat_info: dict):
        """
        Log chat information to the logger bound to this instance.

        Args:
            chat_info (dict): A dictionary containing chat information to be logged.
        """
        self.logger.debug(f"{chat_info}")


class ChatLogger(LoggerBase):
    def __init__(self, route_prefix: str):
        """
        Initialize the Chat Completions logger with a route prefix.

        Args:
            route_prefix (str): The prefix used for routing, e.g., '/openai'.
        """
        super().__init__(route_prefix, "_chat")

    def parse_payload(self, request: Request, raw_payload):
        """
        Asynchronously parse the payload from a FastAPI request.

        Args:
            request (Request): A FastAPI request object.

        Returns:
            dict: A dictionary containing parsed messages, model, IP address, UID, and datetime.
        """
        uid = get_unique_id()

        if self.webui:
            self.q.put({"uid": uid, "payload": raw_payload})

        payload = orjson.loads(raw_payload)
        caching = payload.pop("caching", None)
        if caching is None:
            caching = DEFAULT_REQUEST_CACHING_VALUE
            payload_return = raw_payload
        else:
            payload_return = orjson.dumps(payload)

        info = {
            "messages": payload["messages"],
            "model": payload["model"],
            "stream": payload.get("stream", False),
            "max_tokens": payload.get("max_tokens", None),
            "response_format": payload.get("response_format", None),
            "n": payload.get("n", 1),
            "temperature": payload.get("temperature", 1),
            "top_p": payload.get("top_p", 1),
            "logit_bias": payload.get("logit_bias", None),
            "frequency_penalty": payload.get("frequency_penalty", 0),
            "presence_penalty": payload.get("presence_penalty", 0),
            "seed": payload.get("seed", None),
            "stop": payload.get("stop", None),
            "user": payload.get("user", None),
            "tools": payload.get("tools", None),
            "tool_choice": payload.get("tool_choice", None),
            "ip": get_client_ip(request) or "",
            "uid": uid,
            "caching": caching,
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }

        return info, payload_return

    def parse_bytearray(self, buffer: bytearray):
        """
        Parses a bytearray, usually from an API response, into a dictionary containing various information.

        Args:
            buffer (List[bytes]): A list of bytes to parse.

        Returns:
            Dict[str, Any]: A dictionary containing metadata and content. The keys include:
                - "assistant" (str): content
                - "is_tool_calls" (boolean)
        """
        start_token = "data: "
        start_token_len = len(start_token)
        if buffer.startswith(b'data: '):
            txt_lines = parse_sse_buffer(buffer)
            stream = True
            first_dict = orjson.loads(txt_lines[0][start_token_len:])
            # todo: multiple choices
            msg = first_dict["choices"][0]["delta"]
        else:
            stream = False
            first_dict = orjson.loads(buffer)
            # todo: multiple choices
            msg = first_dict["choices"][0]["message"]

        target_info = dict()
        verbose = False
        if verbose:
            target_info["created"] = first_dict["created"]
            target_info["id"] = first_dict["id"]
            target_info["model"] = first_dict["model"]
            target_info["role"] = msg["role"]
        role = msg["role"]  # always be "assistant"

        content, tool_calls = msg.get("content"), msg.get("tool_calls")
        if tool_calls:
            """
            tool_calls:
                [{
                "index": 0,
                "id": 'xx',
                'type": 'function',
                'function': {'name': 'xxx', 'arguments': ''}
                 }]
            """
            target_info[role] = tool_calls
            target_info["is_tool_calls"] = True
            parse_content_key = "tool_calls"

        else:
            target_info[role] = content
            target_info["is_tool_calls"] = False
            parse_content_key = "content"

        if not stream:
            return target_info

        # loop for stream
        stream_content = ""
        for line in txt_lines[1:]:
            if line.startswith(start_token):
                stream_content += self._parse_one_line_content(
                    line[start_token_len:], parse_content_key
                )
        if target_info['is_tool_calls']:
            tool_calls[0]['function']['arguments'] = stream_content
            target_info[role] = tool_calls
        else:
            target_info[role] = stream_content
        return target_info

    @staticmethod
    def _parse_one_line_content(line: str, parse_key="content"):
        """
        Helper method to parse a single line.

        Args:
            line (str): The line to parse.
            parse_key (str): .

        Returns:
            str: The parsed content from the line.
        """
        try:
            line_dict = orjson.loads(line)
            if parse_key == "content":
                return line_dict["choices"][0]["delta"][parse_key]
            elif parse_key == "tool_calls":
                tool_calls = line_dict["choices"][0]["delta"]["tool_calls"]
                return tool_calls[0]["function"]['arguments']
            else:
                logger.error(f"Unknown parse key: {parse_key}")
                return ""
        except JSONDecodeError:
            return ""
        except KeyError:
            return ""

    def log(self, chat_info: dict):
        """
        Log chat information to the logger bound to this instance.

        Args:
            chat_info (dict): A dictionary containing chat information to be logged.
        """
        self.logger.debug(f"{chat_info}")

    def log_result(self, chat_info: dict):
        """
        Log chat information to the logger bound to this instance.

        Args:
            chat_info (dict): A dictionary containing chat information to be logged.
        """
        self.logger.debug(f"{chat_info}")

    @staticmethod
    def print_chat_info(chat_info: dict):
        """
        Print chat information in a formatted manner.

        Args:
            chat_info (dict): A dictionary containing chat information to be printed.
        """
        messages = chat_info.get("messages")
        if messages:
            print(50 * "-", role='other')
            for msg in messages:
                for key, value in msg.items():
                    markdown_print(f"{key}: {value}", role=key)
            print(
                f"{chat_info.get('ip')}@{chat_info.get('model')} uid: {chat_info.get('uid')}",
                role='other',
            )
            print(50 * "-", role='other')
        else:
            assistant = chat_info.get("assistant")
            if assistant:
                print(77 * "=", role='assistant')
                markdown_print(f"assistant: {assistant}", role='assistant')
                print(f'uid: {chat_info.get("uid")}')
                print(77 * "=", role='assistant')


class EmbeddingLogger(LoggerBase):
    def __init__(self, route_prefix: str):
        super().__init__(route_prefix, "_embedding")

    @staticmethod
    def parse_payload(request: Request, raw_payload: bytes):
        uid = get_unique_id()
        payload = orjson.loads(raw_payload)
        caching = payload.pop("caching", None)
        if caching is None:
            caching = DEFAULT_REQUEST_CACHING_VALUE
            payload_return = raw_payload
        else:
            payload_return = orjson.dumps(payload)

        content = {
            "input": payload['input'],
            "model": payload['model'],
            "encoding_format": payload.get("encoding_format", 'float'),
            "ip": get_client_ip(request) or "",
            "uid": uid,
            "caching": caching,
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }
        return content, payload_return

    def parse_bytearray(self, buffer: bytearray):
        """
        Parse a bytearray into a dictionary.
        """
        result_dict = orjson.loads(buffer)
        target_info = {
            "object": result_dict["object"],
            "usage": result_dict["usage"],
            "model": result_dict["model"],
            "buffer": buffer,
        }
        return target_info

    def log(self, info: dict):
        self.logger.debug(f"{info}")

    def log_result(self, info: dict):
        result_info = {
            "object": info["object"],
            "usage": info["usage"],
            "model": info["model"],
            "uid": info["uid"],
        }
        self.logger.debug(f"{result_info}")


class WhisperLogger:
    # todo
    def __init__(self, route_prefix: str):
        """
        Initialize the Audio logger with a route prefix.

        Args:
            route_prefix (str): The prefix used for routing, e.g., '/openai'.
        """
        _prefix = route_prefix_to_str(route_prefix)
        self.logger = logger.bind(**{f"{_prefix}_whisper": True})

    def log_buffer(self, bytes_: bytes):
        """
        Add a log entry containing the decoded text from bytes.

        Args:
            bytes_ (bytes): The byte string to decode and log.
        """
        text_content = bytes_.decode("utf-8")
        self.logger.info(text_content)
