import itertools
import os

import limits
from fastapi import Request

from ..config import print_rate_limit_info, print_startup_info, setting_log
from ..helper import env2dict, env2list, format_route_prefix

TIMEOUT = 600

ENV_VAR_SEP = ","
OPENAI_BASE_URL = env2list("OPENAI_BASE_URL", sep=ENV_VAR_SEP) or [
    "https://api.openai.com"
]

OPENAI_ROUTE_PREFIX = [
    format_route_prefix(i) for i in env2list("OPENAI_ROUTE_PREFIX", sep=ENV_VAR_SEP)
] or ['/']

EXTRA_BASE_URL = env2list("EXTRA_BASE_URL", sep=ENV_VAR_SEP)
EXTRA_ROUTE_PREFIX = [
    format_route_prefix(i) for i in env2list("EXTRA_ROUTE_PREFIX", sep=ENV_VAR_SEP)
]

LOG_CHAT = os.environ.get("LOG_CHAT", "False").strip().lower() == "true"
if LOG_CHAT:
    setting_log(openai_route_prefix=OPENAI_ROUTE_PREFIX)

IP_WHITELIST = env2list("IP_WHITELIST", sep=ENV_VAR_SEP)
IP_BLACKLIST = env2list("IP_BLACKLIST", sep=ENV_VAR_SEP)

OPENAI_API_KEY = env2list("OPENAI_API_KEY", sep=ENV_VAR_SEP)
FWD_KEY = env2list("FORWARD_KEY", sep=ENV_VAR_SEP)

PROXY = os.environ.get("PROXY", "").strip()
PROXY = PROXY if PROXY else None

GLOBAL_RATE_LIMIT = os.environ.get("GLOBAL_RATE_LIMIT", "fixed-window").strip() or None
RATE_LIMIT_STRATEGY = os.environ.get("RATE_LIMIT_STRATEGY", "").strip() or None
route_rate_limit_conf = env2dict('ROUTE_RATE_LIMIT')


def get_limiter_key(request: Request):
    limiter_prefix = f"{request.scope.get('root_path')}{request.scope.get('path')}"
    key = f"{limiter_prefix}"  # -{get_client_ip(request)}"
    return key


def dynamic_rate_limit(key: str):
    for route in route_rate_limit_conf:
        if key.startswith(route):
            return route_rate_limit_conf[route]
    return GLOBAL_RATE_LIMIT


TOKEN_RATE_LIMIT = os.environ.get("TOKEN_RATE_LIMIT", "").strip()
if TOKEN_RATE_LIMIT:
    rate_limit_item = limits.parse(TOKEN_RATE_LIMIT)
    TOKEN_INTERVAL = (
        rate_limit_item.multiples * rate_limit_item.GRANULARITY.seconds
    ) / rate_limit_item.amount
else:
    TOKEN_INTERVAL = 0

styles = itertools.cycle(
    ["#7CD9FF", "#BDADFF", "#9EFFE3", "#f1b8e4", "#F5A88E", "#BBCA89"]
)
for base_url, route_prefix in zip(OPENAI_BASE_URL, OPENAI_ROUTE_PREFIX):
    print_startup_info(
        base_url, route_prefix, OPENAI_API_KEY, FWD_KEY, LOG_CHAT, style=next(styles)
    )
for base_url, route_prefix in zip(EXTRA_BASE_URL, EXTRA_ROUTE_PREFIX):
    print_startup_info(base_url, route_prefix, "\\", "\\", LOG_CHAT, style=next(styles))

print_rate_limit_info(
    route_rate_limit_conf,
    strategy=RATE_LIMIT_STRATEGY,
    global_rate_limit=GLOBAL_RATE_LIMIT if GLOBAL_RATE_LIMIT else 'inf',
    token_rate_limit=TOKEN_RATE_LIMIT if TOKEN_RATE_LIMIT else 'inf',
    token_interval_time=f"{TOKEN_INTERVAL:.4f}s",
)
