import itertools
import os

import limits
from fastapi import Request

from .console import print_rate_limit_info, print_startup_info
from .content.config import setting_log
from .helper import env2dict, env2list, format_route_prefix, get_client_ip

openai_additional_start_info = {}
general_additional_start_info = {}

TIMEOUT = float(os.environ.get("TIMEOUT", "").strip() or "10")

ITER_CHUNK_TYPE = (
    os.environ.get("ITER_CHUNK_TYPE", "").strip() or "efficiency"
)  # Options: efficiency, one-by-one

CHAT_COMPLETION_ROUTE = "/v1/chat/completions"
COMPLETION_ROUTE = "/v1/completions"
EMBEDDING_ROUTE = "/v1/embeddings"


CACHE_ROUTE_SET = set(env2dict("CACHE_ROUTES", []))

openai_additional_start_info['cache_routes'] = CACHE_ROUTE_SET
general_additional_start_info['cache_routes'] = CACHE_ROUTE_SET

FORWARD_CONFIG = env2dict(
    "FORWARD_CONFIG",
    [{"base_url": "https://api.openai.com", "route": "/", "type": "openai"}],
)

ENV_VAR_SEP = ","

OPENAI_BASE_URL = [
    i['base_url'] for i in FORWARD_CONFIG if i and i.get('type') == 'openai'
]
OPENAI_ROUTE_PREFIX = [
    format_route_prefix(i['route'])
    for i in FORWARD_CONFIG
    if i and i.get('type') == 'openai'
]

GENERAL_BASE_URL = [
    i['base_url'] for i in FORWARD_CONFIG if i and i.get('type') == 'general'
]
GENERAL_ROUTE_PREFIX = [
    format_route_prefix(i['route'])
    for i in FORWARD_CONFIG
    if i and i.get('type') == 'general'
]

for openai_route, general_route in zip(OPENAI_ROUTE_PREFIX, GENERAL_ROUTE_PREFIX):
    assert openai_route not in GENERAL_ROUTE_PREFIX
    assert general_route not in OPENAI_ROUTE_PREFIX

BENCHMARK_MODE = os.environ.get("BENCHMARK_MODE", "false").strip().lower() == "true"
if BENCHMARK_MODE:
    openai_additional_start_info["benchmark_mode"] = BENCHMARK_MODE

PRINT_CHAT = os.environ.get("PRINT_CHAT", "False").strip().lower() == "true"

LOG_OPENAI = os.environ.get("LOG_OPENAI", "False").strip().lower() == "true"
LOG_GENERAL = os.environ.get("LOG_GENERAL", "False").strip().lower() == "true"

CACHE_OPENAI = os.environ.get("CACHE_OPENAI", "False").strip().lower() == "true"
CACHE_GENERAL = os.environ.get("CACHE_GENERAL", "False").strip().lower() == "true"

openai_additional_start_info["LOG_OPENAI"] = LOG_OPENAI
general_additional_start_info["LOG_GENERAL"] = LOG_GENERAL


if LOG_OPENAI:
    setting_log(openai_route_prefix=OPENAI_ROUTE_PREFIX, print_chat=PRINT_CHAT)


if PRINT_CHAT:
    openai_additional_start_info["print_chat"] = True


LOG_CACHE_DB_INFO = (
    os.environ.get("LOG_CACHE_DB_INFO", "false").strip().lower() == "true"
)
CACHE_BACKEND = os.environ.get("CACHE_BACKEND", "MEMORY").strip()
CACHE_ROOT_PATH_OR_URL = os.environ.get("CACHE_ROOT_PATH_OR_URL", ".").strip()

DEFAULT_REQUEST_CACHING_VALUE = False
if CACHE_OPENAI:
    openai_additional_start_info["cache_backend"] = CACHE_BACKEND
    if not CACHE_BACKEND.lower() == 'memory':
        openai_additional_start_info["cache_root_path_or_url"] = CACHE_ROOT_PATH_OR_URL
    DEFAULT_REQUEST_CACHING_VALUE = (
        os.environ.get("DEFAULT_REQUEST_CACHING_VALUE", "false").strip().lower()
        == "true"
    )
    openai_additional_start_info[
        "default_request_caching_value"
    ] = DEFAULT_REQUEST_CACHING_VALUE

if CACHE_GENERAL:
    general_additional_start_info["cache_backend"] = CACHE_BACKEND
    if not CACHE_BACKEND.lower() == 'memory':
        general_additional_start_info["cache_root_path_or_url"] = CACHE_ROOT_PATH_OR_URL
    DEFAULT_REQUEST_CACHING_VALUE = (
        os.environ.get("DEFAULT_REQUEST_CACHING_VALUE", "false").strip().lower()
        == "true"
    )
    general_additional_start_info[
        "default_request_caching_value"
    ] = DEFAULT_REQUEST_CACHING_VALUE

IP_WHITELIST = env2list("IP_WHITELIST", sep=ENV_VAR_SEP)
IP_BLACKLIST = env2list("IP_BLACKLIST", sep=ENV_VAR_SEP)

OPENAI_API_KEY = env2dict("OPENAI_API_KEY")
FWD_KEY = env2dict("FORWARD_KEY")
LEVEL_MODELS = {int(key): value for key, value in env2dict("LEVEL_MODELS").items()}

PROXY = os.environ.get("PROXY", "").strip() or None

if PROXY:
    openai_additional_start_info["proxy"] = PROXY

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
            **openai_additional_start_info,
        )
    for base_url, route_prefix in zip(GENERAL_BASE_URL, GENERAL_ROUTE_PREFIX):
        print_startup_info(
            base_url,
            route_prefix,
            "",
            "",
            style=next(styles),
            **general_additional_start_info,
        )

    print_rate_limit_info(
        RATE_LIMIT_BACKEND,
        RATE_LIMIT_STRATEGY,
        GLOBAL_RATE_LIMIT,
        req_rate_limit_dict,
        token_rate_limit_conf,
    )
