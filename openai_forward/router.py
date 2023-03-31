from .openai import Openai
from sparrow.api import create_app
from fastapi import Request, APIRouter

router = APIRouter()
openai = Openai()


@router.get("/dashboard/billing/credit_grants")
async def credit_grants(request: Request):
    return await openai.credit_grants(request)


@router.route("/v1/chat/completions", methods=["GET", "POST"])
async def completions_(request: Request):
    return await openai.completions(request)


@router.post("/v1/chat/completions")
async def completions(request: Request):
    return await openai.completions(request)


app = create_app(title="openai_forward", version="1.0")
app.include_router(router, tags=["public"])
