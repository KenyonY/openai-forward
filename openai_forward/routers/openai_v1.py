from fastapi import APIRouter, Request

from ..openai import Openai
from .schemas import OpenAIV1ChatCompletion

openai = Openai()
router = APIRouter(prefix=openai.ROUTE_PREFIX, tags=["v1"])


@router.post("/v1/chat/completions")
async def chat_completions(params: OpenAIV1ChatCompletion, request: Request):
    """该接口只是为了document, 将此路由接口放在openai.reverse_proxy接口后面, 实际不会执行该接口。"""
    return await openai.v1_chat_completions(params, request)
