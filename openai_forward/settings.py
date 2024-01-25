import itertools
import os

import limits
from fastapi import Request

from .console import print_rate_limit_info, print_startup_info
from .content.config import setting_log
from .helper import env2dict, env2list, format_route_prefix, get_client_ip

additional_start_info = {}

TIMEOUT = float(os.environ.get("TIMEOUT", "").strip() or "10")

ITER_CHUNK_TYPE = (
    os.environ.get("ITER_CHUNK_TYPE", "").strip() or "efficiency"
)  # Options: efficiency, precision

CHAT_COMPLETION_ROUTE = (
    os.environ.get("CHAT_COMPLETION_ROUTE", "").strip() or "/v1/chat/completions"
)

COMPLETION_ROUTE = os.environ.get("COMPLETION_ROUTE", "").strip() or "/v1/completions"
EMBEDDING_ROUTE = os.environ.get("EMBEDDING_ROUTE", "").strip() or "/v1/embeddings"

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

BENCHMARK_MODE = os.environ.get("BENCHMARK_MODE", "false").strip().lower() == "true"
if BENCHMARK_MODE:
    additional_start_info["benchmark_mode"] = BENCHMARK_MODE

LOG_CHAT = os.environ.get("LOG_CHAT", "False").strip().lower() == "true"
PRINT_CHAT = os.environ.get("PRINT_CHAT", "False").strip().lower() == "true"
if LOG_CHAT:
    setting_log(openai_route_prefix=OPENAI_ROUTE_PREFIX, print_chat=PRINT_CHAT)
    additional_start_info["log_chat"] = LOG_CHAT

if PRINT_CHAT:
    additional_start_info["print_chat"] = True

CACHE_EMBEDDING = os.environ.get("CACHE_EMBEDDING", "false").strip().lower() == "true"
CACHE_CHAT_COMPLETION = (
    os.environ.get("CACHE_CHAT_COMPLETION", "false").strip().lower() == "true"
)
LOG_CACHE_DB_INFO = (
    os.environ.get("LOG_CACHE_DB_INFO", "false").strip().lower() == "true"
)
CACHE_BACKEND = os.environ.get("CACHE_BACKEND", "MEMORY").strip()
CACHE_ROOT_PATH_OR_URL = os.environ.get("CACHE_ROOT_PATH_OR_URL", ".").strip()

DEFAULT_REQUEST_CACHING_VALUE = False
if CACHE_CHAT_COMPLETION:
    additional_start_info["cache_backend"] = CACHE_BACKEND
    additional_start_info["cache_root_path_or_url"] = CACHE_ROOT_PATH_OR_URL
    DEFAULT_REQUEST_CACHING_VALUE = (
        os.environ.get("DEFAULT_REQUEST_CACHING_VALUE", "false").strip().lower()
        == "true"
    )

IP_WHITELIST = env2list("IP_WHITELIST", sep=ENV_VAR_SEP)
IP_BLACKLIST = env2list("IP_BLACKLIST", sep=ENV_VAR_SEP)

# TODO: API KEY permission system
OPENAI_API_KEY = list(env2dict("OPENAI_API_KEY").keys())
FWD_KEY = list(env2dict("FORWARD_KEY").keys())

PROXY = os.environ.get("PROXY", "").strip() or None

if PROXY:
    additional_start_info["proxy"] = PROXY

GLOBAL_RATE_LIMIT = os.environ.get("GLOBAL_RATE_LIMIT", "").strip() or "inf"
RATE_LIMIT_BACKEND = os.environ.get("REQ_RATE_LIMIT_BACKEND", "").strip() or None
RATE_LIMIT_STRATEGY = (
    os.environ.get("RATE_LIMIT_STRATEGY", "fixed-window").strip() or "fixed-window"
)
req_rate_limit_dict = env2dict('REQ_RATE_LIMIT')


def get_limiter_key(request: Request):
    limiter_prefix = f"{request.scope.get('root_path')}{request.scope.get('path')}"
    key = f"{limiter_prefix}-{get_client_ip(request)}"
    return key


def dynamic_request_rate_limit(key: str):
    for route in req_rate_limit_dict:
        if key.startswith(route):
            return req_rate_limit_dict[route]
    return GLOBAL_RATE_LIMIT


def cvt_token_rate_to_interval(token_rate_limit: str):
    if token_rate_limit:
        rate_limit_item = limits.parse(token_rate_limit)
        token_interval = (
            rate_limit_item.multiples * rate_limit_item.GRANULARITY.seconds
        ) / rate_limit_item.amount
    else:
        token_interval = 0
    return token_interval


token_rate_limit_conf = env2dict("TOKEN_RATE_LIMIT")
token_interval_conf = {}
for route, rate_limit in token_rate_limit_conf.items():
    token_interval_conf[route] = cvt_token_rate_to_interval(rate_limit)

styles = itertools.cycle(
    ["#7CD9FF", "#BDADFF", "#9EFFE3", "#f1b8e4", "#F5A88E", "#BBCA89"]
)


def show_startup():
    for base_url, route_prefix in zip(OPENAI_BASE_URL, OPENAI_ROUTE_PREFIX):
        print_startup_info(
            base_url,
            route_prefix,
            OPENAI_API_KEY,
            FWD_KEY,
            style=next(styles),
            **additional_start_info,
        )
    for base_url, route_prefix in zip(EXTRA_BASE_URL, EXTRA_ROUTE_PREFIX):
        extra_additional_start_info = {}
        print_startup_info(
            base_url,
            route_prefix,
            "",
            "",
            style=next(styles),
            **extra_additional_start_info,
        )

    print_rate_limit_info(
        RATE_LIMIT_BACKEND,
        RATE_LIMIT_STRATEGY,
        GLOBAL_RATE_LIMIT,
        req_rate_limit_dict,
        token_rate_limit_conf,
    )
