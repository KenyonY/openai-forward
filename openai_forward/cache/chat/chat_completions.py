from __future__ import annotations

import time
from itertools import cycle
from typing import List, Literal, Optional, Union

import attrs
import orjson
from fastapi import Request
from fastapi.responses import Response, StreamingResponse

from ...decorators import async_random_sleep, async_token_rate_limit
from ...helper import get_unique_id
from ...settings import token_interval_conf
from .tokenizer import TIKTOKEN_VALID, count_tokens, encode_as_pieces


@attrs.define(slots=True)
class ChatMessage:
    role: Literal["user", "assistant", "system"]
    content: Optional[str] = None


@attrs.define(slots=True)
class ChatCompletionMessage:
    role: Literal["user", "assistant", "system"]
    content: Optional[str] = None
    tool_calls: Optional[list] = None


@attrs.define(slots=True)
class Function:
    name: str
    arguments: dict


@attrs.define(slots=True)
class ChoiceToolCall:
    id: str
    function: Function
    type: str = 'function'


@attrs.define(slots=True)
class DeltaFunction:
    name: str
    arguments: str


@attrs.define(slots=True)
class ChoiceDeltaToolCall:
    index: int = 0
    id: Optional[str] = None
    type: Optional[str] = None
    function: Optional[dict] = None


@attrs.define(slots=True)
class DeltaMessage:
    role: Optional[Literal["user", "assistant", "system"]] = None
    content: Optional[str] = None
    tool_calls: Optional[ChoiceDeltaToolCall] = None


@attrs.define(slots=True)
class ChatCompletionRequest:
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_length: Optional[int] = None
    stream: Optional[bool] = False


@attrs.define(slots=True)
class ChatCompletionChoice:
    index: int
    message: ChatCompletionMessage
    finish_reason: str


@attrs.define(slots=True)
class ChatCompletionResponseStreamChoice:
    index: int
    delta: DeltaMessage
    finish_reason: Optional[Literal["stop", "length"]]


@attrs.define(slots=True)
class ChatCompletionsResponse:
    id: str
    object: Literal["chat.completion", "chat.completion.chunk"]
    created: Optional[int]
    model: Optional[str]
    choices: List[Union[ChatCompletionChoice, ChatCompletionResponseStreamChoice]]
    usage: Optional[dict] = None
    system_fingerprint: str = "fp_0123456789"


corpus = [
    """他还太年轻，尚不知道回忆总是会抹去坏的，夸大好的，也正是由于这种玄妙，我们才得以承担过去的重负。
"He was still too young to know that the heart's memory eliminates the bad and magnifies the good, and that thanks to this artifice we manage to endure the burden of the past."
""",
    """当他年轻的时候，他认为时间是个不会耗尽的海洋。现在他已经成了一个老人，而他每天都更加清楚，时间是个窄窄的峡谷。
"When he was young, he thought time was a boundless ocean; now as an old man, he knew more each day that time was a narrow strait."
""",
    """我们的身体认识彼此，就像两本同样的书：书里的内容，书的纸张，书的形状和包装，我都爱得不能自拔。
"Our bodies knew each other as if they were two volumes of the same book: the text, the paper, the shape and cover of the book, I loved them all without reserve."
""",
    """多少人爱你青春欢畅的时辰，爱慕你的美丽，假意或者真心，只有一个人爱你那朝圣者的灵魂，爱你衰老了的脸上痛苦的皱纹
"Many people love you during your youthful and cheerful moments, admiring your beauty, either pretentiously or sincerely. Only one person loves the soul of a pilgrim within you, and the painful wrinkles on your aged face."
""",
    """他离她那么近，甚至能听到她每一次的呼吸，闻到她身上散发的馨香，在此生余下的岁月中，他正是靠着这种馨香来辨认她。
"He is so close to her that he can even hear each of her breaths and smell the fragrance that emanates from her. For the remaining years of his life, it is this fragrance by which he identifies her."
 """,
]

sentences = cycle(corpus)


@async_token_rate_limit(token_interval_conf)
async def stream_generate(
    model: str, content: str | None, tool_calls: list | None, request: Request
):
    created = int(time.time())
    id = f"chatcmpl-{get_unique_id()}"

    if tool_calls:
        function_name = tool_calls[0]['function']['name']
        function_arguments = tool_calls[0]['function']['arguments']
        texts = encode_as_pieces(function_arguments)
    else:
        texts = encode_as_pieces(content)

    delta = DeltaMessage()

    choice_data = ChatCompletionResponseStreamChoice(
        index=0, delta=delta, finish_reason=None
    )
    chunk = ChatCompletionsResponse(
        id=id,
        model=model,
        choices=[choice_data],
        object="chat.completion.chunk",
        created=created,
        system_fingerprint="fp_0123456789",
    )

    def serialize_delta(
        role=None, content=None, delta_tool_calls=None, finish_reason=None
    ):
        if role:
            delta.role = role
        if content:
            delta.content = content
        if tool_calls:
            delta.tool_calls = delta_tool_calls

        choice_data.finish_reason = finish_reason
        choice_data.delta = delta

        chunk.choices = [choice_data]

        return (
            b'data: '
            + orjson.dumps(
                attrs.asdict(chunk, filter=attrs.filters.exclude(type(None)))
            )
            + b'\n\n'
        )

    if tool_calls:
        yield serialize_delta(
            role="assistant",
            delta_tool_calls=[
                {
                    'index': 0,
                    'id': f"call_{get_unique_id()}",
                    'function': {"name": function_name, "arguments": ""},
                    'type': 'function',
                }
            ],
        )
    else:
        yield serialize_delta(role="assistant", content="")

    delta = DeltaMessage()
    for content in texts:
        if tool_calls:
            yield serialize_delta(
                delta_tool_calls=[
                    {
                        'index': 0,
                        'id': None,
                        'function': {"name": None, "arguments": content},
                        'type': None,
                    }
                ],
            )
        else:
            yield serialize_delta(content=content)

    delta = DeltaMessage()
    yield serialize_delta(finish_reason="tool_calls" if tool_calls else "stop")

    yield b'data: [DONE]\n\n'


@async_token_rate_limit(token_interval_conf)
async def stream_generate_efficient(
    model: str, content: str | None, tool_calls: list | None, request: Request
):
    """More efficient (use dict) version of stream_generate
    Args:
        model (str): The model to use.
        content (str): content.
        tool_calls (list | None): tool_calls list.
        request (Request): A FastAPI request object. For rate limit.
    """
    created = int(time.time())
    id = f"chatcmpl-{get_unique_id()}"
    if tool_calls:
        function_name = tool_calls[0]['function']['name']
        function_arguments = tool_calls[0]['function']['arguments']
        texts = encode_as_pieces(function_arguments)
    else:
        texts = encode_as_pieces(content)

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

    if tool_calls:
        yield serialize_delta(
            role="assistant",
            delta_tool_calls=[
                {
                    'index': 0,
                    'id': f"call_{get_unique_id()}",
                    'function': {"name": function_name, "arguments": ""},
                    'type': 'function',
                }
            ],
        )
    else:
        yield serialize_delta(role="assistant", content="")

    delta = {}
    for content in texts:
        if tool_calls:
            yield serialize_delta(
                delta_tool_calls=[
                    {
                        'index': 0,
                        'id': None,
                        'function': {"name": None, "arguments": content},
                        'type': None,
                    }
                ],
            )
        else:
            yield serialize_delta(content=content)

    delta = {}
    yield serialize_delta(finish_reason="tool_calls" if tool_calls else "stop")

    yield b'data: [DONE]\n\n'


def generate(model: str, content: str | None, tool_calls: list | None, usage: dict):
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


@attrs.define(slots=True)
class ModelInferResult:
    content: str
    usage: dict


def model_inference(model: str, messages: List):
    sentence = next(sentences)

    if TIKTOKEN_VALID:
        usage = count_tokens(messages, sentence, 'gpt-3.5-turbo')
    else:
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    return ModelInferResult(content=sentence, usage=usage)


@async_random_sleep(min_time=0, max_time=1)
async def chat_completions_benchmark(request: Request):
    payload = await request.json()
    model = payload.get("model", 'robot')
    stream = payload.get("stream", False)
    messages = payload.get("messages", [])

    model_result = model_inference(model, messages)

    if stream:
        return StreamingResponse(
            stream_generate_efficient(model, model_result.content, None, request),
            media_type="text/event-stream",
        )
    else:
        return Response(
            content=generate(model, model_result.content, None, model_result.usage),
            media_type="application/json",
        )
