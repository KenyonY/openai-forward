from .openai import Openai
from .routers.openai_v1 import router as router_v1
from sparrow.api import create_app
from fastapi import Request, APIRouter
import pretty_errors

openai = Openai()
app = create_app(title="openai_forward", version="1.0")
app.include_router(router_v1)


@app.get("/dashboard/billing/credit_grants", tags=['public'])
async def credit_grants(request: Request):
    return await openai.credit_grants(request)
