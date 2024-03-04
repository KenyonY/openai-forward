from __future__ import annotations

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class OpenAIV1ChatCompletion(BaseModel):
    """Creates a completion for the chat message"""

    model: str = Field(
        ..., description="The model to use for the completion", example="gpt-3.5-turbo"
    )
    messages: List[Dict[str, Any]] = Field(
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

class AnthropicChatCompletion(BaseModel):
    """Creates a completion for the chat message"""

    model: str = Field(
        ..., description="The model to use for the completion", example="claude-v1"
    )
    messages: List[Dict[str, Any]] = Field(
        ...,
        description="The message to complete",
        example=[{"role": "user", "content": "hi"}],
    )
    prompt: str = Field(
        ...,
        description="The prompt to complete",
        example="Hi! How are you?",
    )
    system: str = Field(
        ..., description="System prompt.", example="Respond only in Spanish."
    )
    temperature: float = Field(default=1, description="0会导致更确定的结果，1会导致更随机的结果")
    top_p: float = Field(default=1, description="0会导致更确定的结果，1会导致更随机的结果")
    top_k: float = Field(default=50, description="0会导致更确定的结果，1会导致更随机的结果")
    max_tokens_to_sample: Optional[int] = Field(
        default=None,
        description="max_tokens_to_sample.",
    )
    stream: bool = Field(default=False)

class NAICompletion(BaseModel):
    """Creates a completion for the input"""

    model: str = Field(
        ..., 
        description="The model to use for the completion",
        example="clio-v1"
    )
    input: str = Field(
        ...,
        description="The input to complete",
        example="Human: Hi! How are you?\n\nAssistant:"
    )
    parameters: Dict[str, Any] = Field(
        ...,
        description="Generation parameters to be sent to the model",
        example={"max_length": 150, "min_length": 1}
    )