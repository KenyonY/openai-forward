from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from . import custom_slowapi
from .cache.chat import chat_completions_benchmark
from .forward import create_generic_proxies, create_openai_proxies
from .helper import normalize_route as normalize_route_path
from .settings import (
    BENCHMARK_MODE,
    RATE_LIMIT_STRATEGY,
    dynamic_request_rate_limit,
    get_limiter_key,
    show_startup,
)

limiter = Limiter(key_func=get_limiter_key, strategy=RATE_LIMIT_STRATEGY)

app = FastAPI(title="openai_forward", version="0.5")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def normalize_route(request: Request, call_next):
    path = request.url.path
    request.scope["path"] = normalize_route_path(path)
    response = await call_next(request)
    return response


@app.get(
    "/healthz",
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
)
@limiter.limit(dynamic_request_rate_limit, exempt_when=lambda: True)
def healthz(request: Request):
    return "OK"


if BENCHMARK_MODE:
    app.add_route(
        "/benchmark/v1/chat/completions",
        route=limiter.limit(dynamic_request_rate_limit)(chat_completions_benchmark),
        methods=["POST"],
    )

add_route = lambda obj: app.add_route(
    obj.ROUTE_PREFIX + "{api_path:path}",
    route=limiter.limit(dynamic_request_rate_limit)(obj.reverse_proxy),
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"],
)

[add_route(obj) for obj in create_openai_proxies()]
[add_route(obj) for obj in create_generic_proxies()]

show_startup()
