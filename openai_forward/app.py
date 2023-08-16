from fastapi import FastAPI, Request, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .forwarding import get_fwd_anything_objs, get_fwd_openai_style_objs
from .forwarding.settings import (
    RATE_LIMIT_STRATEGY,
    dynamic_rate_limit,
    get_limiter_key,
)

limiter = Limiter(key_func=get_limiter_key, strategy=RATE_LIMIT_STRATEGY)

app = FastAPI(title="openai_forward", version="0.5")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get(
    "/healthz",
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
)
@limiter.limit(dynamic_rate_limit)
def healthz(request: Request):
    print(request.scope.get("client"))
    return "OK"


add_route = lambda obj: app.add_route(
    obj.ROUTE_PREFIX + "{api_path:path}",
    limiter.limit(dynamic_rate_limit)(obj.reverse_proxy),
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"],
)

[add_route(obj) for obj in get_fwd_openai_style_objs()]
[add_route(obj) for obj in get_fwd_anything_objs()]
