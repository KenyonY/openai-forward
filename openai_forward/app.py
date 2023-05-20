import httpx
from sparrow.api import create_app

from .openai import Openai
from .routers.openai_v1 import router as router_v1

app = create_app(title="openai_forward", version="1.0")
openai = Openai()

app.add_route(
    openai.ROUTE_PREFIX + '/{api_path:path}',
    openai.reverse_proxy,
    methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'PATCH', 'TRACE'],
)

app.include_router(router_v1)
