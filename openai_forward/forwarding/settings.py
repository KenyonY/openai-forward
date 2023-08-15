import os

import limits
from fastapi import Request

from ..config import setting_log
from ..helper import env2dict, env2list, format_route_prefix, get_client_ip

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

GLOBAL_RATE_LIMIT = os.environ.get("GLOBAL_RATE_LIMIT", "").strip() or None
RATE_LIMIT_STRATEGY = os.environ.get("RATE_LIMIT_STRATEGY", "").strip() or None
rate_limit_conf = env2dict('RATE_LIMIT')
print(f"{rate_limit_conf=}")


def get_limiter_key(request: Request):
    limiter_prefix = f"{request.scope.get('root_path')}{request.scope.get('path')}"
    key = f"{limiter_prefix}"  # -{get_client_ip(request)}"
    return key


def dynamic_rate_limit(key: str):
    for route in rate_limit_conf:
        if key.startswith(route):
            return rate_limit_conf[route]
    return GLOBAL_RATE_LIMIT


TOKEN_RATE_LIMIT = os.environ.get("TOKEN_RATE_LIMIT", "").strip()
if TOKEN_RATE_LIMIT:
    rate_limit_item = limits.parse(TOKEN_RATE_LIMIT)
    print(
        f"{rate_limit_item.amount=} {rate_limit_item=} {rate_limit_item.GRANULARITY} {rate_limit_item.multiples=}"
    )
    TOKEN_INTERVAL = (
        rate_limit_item.multiples * rate_limit_item.GRANULARITY.seconds
    ) / rate_limit_item.amount
    print(f"{TOKEN_INTERVAL=}")
else:
    TOKEN_INTERVAL = 0
