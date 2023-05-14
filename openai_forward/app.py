import chardet
import httpx
from sparrow.api import create_app

from .openai import Openai
from .routers.openai_v1 import router as router_v1

app = create_app(title="openai_forward", version="1.0")
openai = Openai()
use_http2 = False


def autodetect(content):
    return chardet.detect(content).get("encoding")


@app.on_event('startup')
async def startup_event():
    app.state.client = httpx.AsyncClient(
        base_url=Openai.BASE_URL, http2=use_http2, default_encoding=autodetect
    )


@app.on_event('shutdown')
async def shutdown_event():
    await app.state.client.aclose()


app.add_route(
    openai.ROUTE_PREFIX + '/{api_path:path}',
    openai.reverse_proxy,
    methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'PATCH', 'TRACE'],
)
app.include_router(router_v1)
