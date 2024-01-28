from __future__ import annotations

import random
from typing import List

from fastapi.responses import Response, StreamingResponse
from flaxkv.pack import encode
from loguru import logger

from ...settings import CACHE_OPENAI
from ..database import db_dict
from .chat_completions import (
    async_token_rate_limit,
    generate,
    stream_generate_efficient,
    token_interval_conf,
)


def construct_cache_key(payload_info: dict):
    elements = [
        payload_info["n"],
        payload_info['messages'],
        payload_info['model'],
        payload_info["max_tokens"],
        payload_info['response_format'],
        payload_info['seed'],
        # payload_info['temperature'],
        payload_info["tools"],
        payload_info["tool_choice"],
    ]

    return encode(elements)


def get_response_from_key(key, payload_info, request, **kwargs):
    value = db_dict[key]
    cache_values = value['data']
    idx = random.randint(0, len(cache_values) - 1) if len(cache_values) > 1 else 0
    uid = payload_info["uid"]
    logger.info(f'chat uid: {uid} >>>{idx}>>>> [cache hit]')
    # todo: handle multiple choices
    cache_value = cache_values[idx]
    if isinstance(cache_value, list):
        text = None
        tool_calls = cache_value
        is_tool_calls = True
    else:
        text = cache_value
        tool_calls = None
        is_tool_calls = False

    logger_instance = kwargs.get("logger_instance")
    if logger_instance:
        result_info = {
            "assistant": cache_value,
            "is_tool_calls": is_tool_calls,
            'uid': uid,
        }
        if logger_instance.webui:
            logger_instance.q.put({"uid": uid, "result": result_info})

        logger_instance.log_result(result_info)

    if payload_info["stream"]:
        return StreamingResponse(
            stream_generate_efficient(
                payload_info['model'],
                text,
                tool_calls,
                request,
            ),
            status_code=200,
            media_type="text/event-stream",
        )

    else:
        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        return Response(
            content=generate(payload_info['model'], text, tool_calls, usage),
            media_type="application/json",
        )


def get_cached_chat_response(payload_info, valid_payload, request, **kwargs):
    """
    Attempts to retrieve a cached response based on the current request's payload information.

    This function constructs a cache key based on various aspects of the request payload,
    checks if the response for this key has been cached, and if so, constructs and returns
    the appropriate cached response.

    Returns:
        Tuple[Union[Response, None], Union[str, None]]:
            - Response (Union[Response, None]): The cached response if available; otherwise, None.
            - cache_key (Union[str, None]): The constructed cache key for the request. None if caching is not applicable.

    Note:
        If a cache hit occurs, the cached response is immediately returned without contacting the external server.
    """
    if not (CACHE_OPENAI and valid_payload):
        return None, None

    cache_key = construct_cache_key(payload_info)

    if payload_info['caching'] and cache_key in db_dict:
        return (
            get_response_from_key(cache_key, payload_info, request, **kwargs),
            cache_key,
        )

    return None, cache_key


@async_token_rate_limit(token_interval_conf)
async def stream_generate(buffer_list: List, request):
    for buffer in buffer_list:
        yield buffer


def gen_response(buffer_list, request):
    if len(buffer_list) > 1:
        return StreamingResponse(
            stream_generate(buffer_list, request),
            status_code=200,
            media_type="application/octet-stream",
        )
    else:
        return Response(
            buffer_list[0],
            status_code=200,
            media_type="application/octet-stream",
        )
