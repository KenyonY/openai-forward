from sparrow.api import create_app

from .forwarding import Openai, get_extra_fwd_objs

app = create_app(title="openai_forward", version="1.0")


add_route = lambda obj: app.add_route(
    obj.ROUTE_PREFIX + "/{api_path:path}",
    obj.reverse_proxy,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"],
)


add_route(Openai())
[add_route(obj) for obj in get_extra_fwd_objs()]
