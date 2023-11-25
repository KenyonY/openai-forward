from fastapi import APIRouter, Request

from ..nai import NovelAI
from ..anthropic import Anthropic
from ..openai import Openai
from .schemas import OpenAIV1ChatCompletion, AnthropicChatCompletion, NAICompletion

openai = Openai()
anthropic = Anthropic()
novelai = NovelAI()
router = APIRouter(prefix=openai.ROUTE_PREFIX, tags=["v1"])


@router.post("/v1/chat/completions")
async def chat_completions(params: OpenAIV1ChatCompletion, request: Request):
    """该接口只是为了document, 将此路由接口放在openai.reverse_proxy接口后面, 实际不会执行该接口。"""
    return await openai.reverse_proxy(request)

@router.get("/v1/models")
async def models_list(request: Request):
    """该接口只是为了document, 将此路由接口放在openai.reverse_proxy接口后面, 实际不会执行该接口。"""
    return await openai.reverse_proxy(request)

@router.get("/user/subscription")
async def subscription_status(request: Request):
    return await novelai.reverse_proxy(request)
    
# NovelAI has separate URLs for streaming and non-streaming
@router.post("/ai/generate")
@router.post("/ai/generate-stream")
async def novelai_completions(params: NAICompletion, request: Request):
    return await novelai.reverse_proxy(request)