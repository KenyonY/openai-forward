from fastapi import APIRouter, Request

from ..anthropic import Anthropic
from ..openai import Openai
from .schemas import OpenAIV1ChatCompletion, AnthropicChatCompletion

openai = Openai()
anthropic = Anthropic()
router = APIRouter(prefix=openai.ROUTE_PREFIX, tags=["v1"])


@router.post("/v1/chat/completions")
async def chat_completions(params: OpenAIV1ChatCompletion, request: Request):
    """该接口只是为了document, 将此路由接口放在openai.reverse_proxy接口后面, 实际不会执行该接口。"""
    return await openai.reverse_proxy(request)

@router.get("/v1/models")
async def models_list(request: Request):
    """该接口只是为了document, 将此路由接口放在openai.reverse_proxy接口后面, 实际不会执行该接口。"""
    return await openai.reverse_proxy(request)

@router.post("/v1/complete")
async def anthropic_completions(params: AnthropicChatCompletion, request: Request):
    return await anthropic.reverse_proxy(request)
