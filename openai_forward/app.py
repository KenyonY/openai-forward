from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .forwarding import fwd_anything_objs, fwd_openai_objs
from .forwarding.settings import (
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

@app.get(
    "/healthz",
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
)
@limiter.limit(dynamic_request_rate_limit)
def healthz(request: Request):
    return "OK"


add_route = lambda obj: app.add_route(
    obj.ROUTE_PREFIX + "{api_path:path}",
    limiter.limit(dynamic_request_rate_limit)(obj.reverse_proxy),
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"],
)

[add_route(obj) for obj in fwd_openai_objs()]
[add_route(obj) for obj in fwd_anything_objs()]

show_startup()
