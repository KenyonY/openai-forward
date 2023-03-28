from .openai import Openai
from sparrow.api import create_app
from fastapi import Request

app = create_app(title="openai_forward", version="1.0")
openai = Openai()


@app.get("/dashboard/billing/credit_grants")
async def credit_grants(request: Request):
    return await openai.credit_grants(request)


@app.route("/v1/chat/completions", methods=["GET", "POST"])
async def completions(request: Request):
    return await openai.completions(request)
