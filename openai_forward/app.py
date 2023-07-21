from sparrow.api import create_app

from .anthropic import Anthropic
from .openai import Openai
from .routers.v1 import router as router_v1

app = create_app(title="openai_forward", version="1.0")
app.openapi_version = "3.0.0"

openai = Openai()
anthropic = Anthropic()

app.include_router(router_v1)
