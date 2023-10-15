import time
from typing import List

import orjson
from fastapi import Request
from loguru import logger
from orjson import JSONDecodeError

from ..helper import get_client_ip, get_unique_id, route_prefix_to_str
from .helper import markdown_print, parse_sse_buffer, print


class CompletionLogger:
    def __init__(self, route_prefix: str):
        """
        Initialize the Completions logger with a route prefix.

        Args:
            route_prefix (str): The prefix used for routing, e.g., '/openai'.
        """
        _prefix = route_prefix_to_str(route_prefix)
        kwargs = {_prefix + "_completion": True}
        self.logger = logger.bind(**kwargs)

    @staticmethod
    async def parse_payload(request: Request):
        uid = get_unique_id()
        payload = await request.json()

        content = {
            "prompt": payload['prompt'],
            "model": payload['model'],
            "stream": payload.get("stream", True),
            "temperature": payload.get("temperature", 1),
            "ip": get_client_ip(request) or "",
            "uid": uid,
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }
        return content

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

    def log(self, chat_info: dict):
        """
        Log chat information to the logger bound to this instance.

        Args:
            chat_info (dict): A dictionary containing chat information to be logged.
        """
        self.logger.debug(f"{chat_info}")


class ChatLogger:
    def __init__(self, route_prefix: str):
        """
        Initialize the Chat Completions logger with a route prefix.

        Args:
            route_prefix (str): The prefix used for routing, e.g., '/openai'.
        """
        _prefix = route_prefix_to_str(route_prefix)
        kwargs = {_prefix + "_chat": True}
        self.logger = logger.bind(**kwargs)

    @staticmethod
    async def parse_payload(request: Request):
        """
        Asynchronously parse the payload from a FastAPI request.

        Args:
            request (Request): A FastAPI request object.

        Returns:
            dict: A dictionary containing parsed messages, model, IP address, UID, and datetime.
        """
        uid = get_unique_id()
        payload = await request.json()
        msgs = payload["messages"]
        functions = payload.get("functions")
        model = payload["model"]
        if functions:
            content = {"functions": functions}
        else:
            content = {}
        content.update(
            {
                "messages": msgs,
                "model": model,
                "stream": payload.get("stream", True),
                "temperature": payload.get("temperature", 1),
                "ip": get_client_ip(request) or "",
                "uid": uid,
                "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            }
        )
        return content

    def parse_bytearray(self, buffer: bytearray):
        """
        Parses a bytearray, usually from an API response, into a dictionary containing various information.

        Args:
            buffer (List[bytes]): A list of bytes to parse.

        Returns:
            Dict[str, Any]: A dictionary containing metadata and content. The keys include:
                - "role" (str): "assistant"
                - "content" (str)
                - "is_function_call" (boolean)
        """
        start_token = "data: "
        start_token_len = len(start_token)
        if buffer.startswith(b'data: '):
            txt_lines = parse_sse_buffer(buffer)
            stream = True
            first_dict = orjson.loads(txt_lines[0][start_token_len:])
            msg = first_dict["choices"][0]["delta"]
        else:
            stream = False
            first_dict = orjson.loads(buffer)
            msg = first_dict["choices"][0]["message"]

        target_info = dict()
        verbose = False
        if verbose:
            target_info["created"] = first_dict["created"]
            target_info["id"] = first_dict["id"]
            target_info["model"] = first_dict["model"]
            target_info["role"] = msg["role"]
        role = msg["role"]

        content, function_call = msg.get("content"), msg.get("function_call")
        if function_call:
            target_info[role] = function_call
            target_info["is_function_call"] = True
            parse_content_key = "function_call"
        else:
            target_info[role] = content
            target_info["is_function_call"] = False
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
        if target_info['is_function_call']:
            target_info[role]['arguments'] = stream_content
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
            elif parse_key == "function_call":
                function_call = line_dict["choices"][0]["delta"][parse_key]
                return function_call["arguments"]
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


class WhisperLogger:
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
