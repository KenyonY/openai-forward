from fastapi import FastAPI, status

from .forwarding import get_fwd_anything_objs, get_fwd_openai_style_objs

app = FastAPI(title="openai_forward", version="0.4")


@app.get(
    "/healthz",
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
)
def healthz():
    return "OK"


add_route = lambda obj: app.add_route(
    obj.ROUTE_PREFIX + "{api_path:path}",
    obj.reverse_proxy,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"],
)

[add_route(obj) for obj in get_fwd_openai_style_objs()]
[add_route(obj) for obj in get_fwd_anything_objs()]
