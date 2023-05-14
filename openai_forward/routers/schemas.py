from __future__ import annotations

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class OpenAIV1ChatCompletion(BaseModel):
    """Creates a completion for the chat message"""

    model: str = Field(
        ..., description="The model to use for the completion", example="gpt-3.5-turbo"
    )
    messages: List[Dict[str, str]] = Field(
        ...,
        description="The message to complete",
        example=[{"role": "user", "content": "hi"}],
    )
    temperature: float = Field(default=1, description="0会导致更确定的结果，1会导致更随机的结果")
    top_p: float = Field(default=1, description="0会导致更确定的结果，1会导致更随机的结果")
    n: int = Field(
        default=1,
        description="How many chat completion choices to generate for each input message.",
    )
    stream: bool = Field(default=False)
    stop: Union[List[str], str, None] = Field(
        default=None,
        description="Up to 4 sequences where the API will stop generating further tokens.",
    )
    max_tokens: Union[int, None] = Field(
        default=None,
        description="The maximum number of tokens to generate in the chat completion. The total length of input tokens and generated tokens is limited by the model's context length.",
    )
    presence_penalty: float = Field(
        default=0, description="Number between -2.0 and 2.0. "
    )
    frequency_penalty: float = Field(
        default=0, description="Number between -2.0 and 2.0. "
    )
    logit_bias: Optional[Dict[str, float]] = Field(
        default=None,
        description="取值[-100, 100]， 取值越大，生成的结果越偏向于该token。 取-100表示完全不考虑该token。",
    )
    user: Optional[str] = Field(
        default=None,
        description="A unique identifier representing your end-user, which can help OpenAI to monitor and detect abuse. ",
    )

    class Config:
        schema_extra = {
            "example": {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": False,
                "temperature": 1,
                "top_p": 1,
                "logit_bias": None,
            }
        }
