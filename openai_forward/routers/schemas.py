from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union


class OpenAIV1ChatCompletion(BaseModel):
    """Creates a completion for the chat message"""
    model: str = Field(..., description="The model to use for the completion", example="gpt-3.5-turbo")
    messages: List[Dict[str, str]] = Field(..., description="The message to complete",
                                           example=[{"role": "user", "content": "hi"}])
    temperature: float = Field(default=1, description="The temperature to use for the completion")
    top_p: float = Field(default=1, description="""An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.\nWe generally recommend altering this or temperature but not both.""")
    n: int = Field(default=1, description="How many chat completion choices to generate for each input message.")
    stream: bool = Field(default=False)
    stop: Union[List[str], str, None] = Field(default=None,
                                              description="Up to 4 sequences where the API will stop generating further tokens.")
    max_tokens: Union[int, None] = Field(default=None, description="The maximum number of tokens to generate in the chat completion. The total length of input tokens and generated tokens is limited by the model's context length.")
    presence_penalty: float = Field(default=0, description="Number between -2.0 and 2.0. ")
    frequency_penalty: float = Field(default=0, description="Number between -2.0 and 2.0. ")
    logit_bias: Optional[Dict[str, float]] = Field(default=None, description="A dictionary of token to bias. ")
    user: Optional[str] = Field(default=None,
                                description="A unique identifier representing your end-user, which can help OpenAI to monitor and detect abuse. ",
                                )

    class Config:
        schema_extra = {
            "example": {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": False
            }
        }
