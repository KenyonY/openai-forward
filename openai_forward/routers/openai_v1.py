from ..openai import Openai
from .schemas import OpenAIV1ChatCompletion
from fastapi import Request, APIRouter

openai = Openai()
router = APIRouter(prefix=openai._ROUTE_PREFIX, tags=["v1"])


@router.post("/v1/chat/completions")
async def chat_completions(params: OpenAIV1ChatCompletion, request: Request):
    print("该接口只是为了document, 将此路由接口放在openai.reverse_proxy接口后面, 不要执行该接口。")
    return await openai.v1_chat_completions(params, request)
