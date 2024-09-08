from __future__ import annotations

import os
import time

import attrs
import orjson

from openai_forward.cache.chat.chat_completions import (
    ChatCompletionChoice,
    ChatCompletionMessage,
    ChatCompletionsResponse,
    token_interval_conf,
)
from openai_forward.config.settings import CACHE_OPENAI, FWD_KEY

from ..cache.chat.tokenizer import TIKTOKEN_VALID, count_tokens, encode_as_pieces
from ..decorators import async_token_rate_limit_auth_level, random_sleep
from ..helper import get_unique_id

def generate(model, content: str, history_messages=None, tool_calls: list = None):
    messages = [] if history_messages is None else history_messages
    usage = count_tokens(messages, content, model)
    created = int(time.time())
    id = f"chatcmpl-{get_unique_id()}"

    choice_data = ChatCompletionChoice(
        index=0,
        message=ChatCompletionMessage(
            role="assistant", content=content, tool_calls=tool_calls
        ),
        finish_reason="tool_calls" if tool_calls else "stop",
    )

    data = ChatCompletionsResponse(
        id=id,
        created=created,
        model=model,
        choices=[choice_data],
        object="chat.completion",
        usage=usage,
    )

    return orjson.dumps(
        attrs.asdict(data),
        option=orjson.OPT_APPEND_NEWLINE,  # not necessary
    )


@async_token_rate_limit_auth_level(token_interval_conf, FWD_KEY)
async def stream_generate_efficient(request, model, model_infer, **kwargs):
    """More efficient (use dict) version of stream_generate
    Args:
        model (str): The model to use.
        content (str): content.
    """
    created = int(time.time())
    id = f"chatcmpl-{get_unique_id()}"

    delta = {}
    choice_data = {"index": 0, "delta": delta, "finish_reason": None}
    chunk = {
        "id": id,
        "model": model,
        "choices": [choice_data],
        "object": "chat.completion.chunk",
        "created": created,
        "system_fingerprint": "fp_0123456789",
    }

    def serialize_delta(
        role=None, content=None, delta_tool_calls=None, finish_reason=None
    ):
        if role:
            delta['role'] = role
        if content:
            delta['content'] = content
        if delta_tool_calls:
            delta['tool_calls'] = delta_tool_calls
            delta['content'] = content

        choice_data['finish_reason'] = finish_reason
        choice_data['delta'] = delta

        chunk['choices'] = [choice_data]

        return b'data: ' + orjson.dumps(chunk) + b'\n\n'

    yield serialize_delta(role="assistant", content="")

    delta = {}
    for content in model_infer(**kwargs):
        if not content:
            continue
        yield serialize_delta(content=content)

    delta = {}
    yield serialize_delta(finish_reason="stop")

    yield b'data: [DONE]\n\n'
