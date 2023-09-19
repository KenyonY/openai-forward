import time
from itertools import cycle
from typing import List, Literal, Optional, Union

import orjson
from fastapi import Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from ..decorators import async_random_sleep, async_token_rate_limit
from ..helper import get_unique_id
from ..settings import token_interval_conf
from .tokenizer import TIKTOKEN_VALID, count_tokens, encode_as_pieces


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class DeltaMessage(BaseModel):
    role: Optional[Literal["user", "assistant", "system"]] = None
    content: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_length: Optional[int] = None
    stream: Optional[bool] = False


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Literal["stop", "length"]


class ChatCompletionResponseStreamChoice(BaseModel):
    index: int
    delta: DeltaMessage
    finish_reason: Optional[Literal["stop", "length"]]


class ChatCompletionsResponse(BaseModel):
    id: str
    object: Literal["chat.completion", "chat.completion.chunk"]
    created: Optional[int] = Field(default_factory=lambda: int(time.time()))
    model: Optional[str] = Field(default="gpt-3.5-turbo")
    choices: List[
        Union[ChatCompletionResponseChoice, ChatCompletionResponseStreamChoice]
    ]
    usage: Optional[dict] = None


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
async def stream_generate(model: str, texts, request: Request):
    created = int(time.time())
    id = f"chatcmpl-{get_unique_id()}"

    def serilize_delta(role=None, content=None, finish_reason=None):
        delta = DeltaMessage()
        if role:
            delta.role = role
        if content:
            delta.content = content
        choice_data = ChatCompletionResponseStreamChoice(
            index=0, delta=delta, finish_reason=finish_reason
        )
        chunk = ChatCompletionsResponse(
            id=id,
            model=model,
            choices=[choice_data],
            object="chat.completion.chunk",
            created=created,
        )
        return b'data: ' + orjson.dumps(
            chunk.dict(exclude_unset=True), option=orjson.OPT_APPEND_NEWLINE
        )

    yield serilize_delta(role="assistant")

    for text in texts:
        yield serilize_delta(content=text)

    yield serilize_delta(finish_reason="stop")

    yield b'data: [DONE]\n\n'


def generate(model: str, sentence, messages):
    created = int(time.time())
    id = f"chatcmpl-{get_unique_id()}"

    choice_data = ChatCompletionResponseChoice(
        index=0,
        message=ChatMessage(role="assistant", content=sentence),
        finish_reason="stop",
    )
    if TIKTOKEN_VALID:
        usage = count_tokens(messages, sentence, 'gpt-3.5-turbo')
    else:
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": -1}
    data = ChatCompletionsResponse(
        id=id,
        created=created,
        model=model,
        choices=[choice_data],
        object="chat.completion",
        usage=usage,
    )

    return orjson.dumps(data.dict(exclude_unset=True))


@async_random_sleep(min_time=0, max_time=0)
async def chat_completions_benchmark(request: Request):
    sentence = next(sentences)

    payload = await request.json()
    model = payload.get("model", 'robot')
    stream = payload.get("stream", False)
    messages = payload.get("messages", [])

    if stream:
        texts = encode_as_pieces(sentence)
        return StreamingResponse(
            stream_generate(model, texts, request), media_type="text/event-stream"
        )
    else:
        return Response(
            content=generate(model, sentence, messages), media_type="application/json"
        )
