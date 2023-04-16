from .openai import Openai
from .routers.openai_v1 import router as router_v1
from sparrow.api import create_app
import httpx

app = create_app(title="openai_forward", version="1.0")
openai = Openai()
use_http2 = False


@app.on_event('startup')
async def startup_event():
    app.state.client = httpx.AsyncClient(base_url=Openai.base_url, http2=use_http2)


@app.on_event('shutdown')
async def shutdown_event():
    await app.state.client.aclose()


app.add_route('/{api_path:path}', openai.reverse_proxy,
              ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'PATCH', 'TRACE'])
app.include_router(router_v1)
