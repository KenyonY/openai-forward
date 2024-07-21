import itertools
import os
from pathlib import Path
from typing import Any, Dict, List, Set

import limits
import yaml
from fastapi import Request

from openai_forward.console import print_rate_limit_info, print_startup_info
from openai_forward.content.config import setting_log
from openai_forward.helper import format_route_prefix

config_file_path = Path("openai-forward-config.yaml")
if config_file_path.exists():
    with open(config_file_path) as file:
        config = yaml.safe_load(file)
else:
    config = {}

if not config:
    # 从环境变量中获取配置将被弃用
    from openai_forward.helper import (
        env2dict,
        env2list,
        format_route_prefix,
        get_client_ip,
    )

    TIMEOUT = float(os.environ.get("TIMEOUT", "").strip() or "10")
    DEFAULT_STREAM_RESPONSE = (
        os.environ.get("DEFAULT_STREAM_RESPONSE", "True").strip().lower() == "true"
    )

    ITER_CHUNK_TYPE = (
        os.environ.get("ITER_CHUNK_TYPE", "").strip() or "efficiency"
    )  # Options: efficiency, one-by-one

    CHAT_COMPLETION_ROUTE = (
        os.environ.get("CHAT_COMPLETION_ROUTE", "/v1/chat/completions").strip().lower()
    )
    COMPLETION_ROUTE = (
        os.environ.get("COMPLETION_ROUTE", "/v1/completions").strip().lower()
    )
    EMBEDDING_ROUTE = (
        os.environ.get("EMBEDDING_ROUTE", "/v1/embeddings").strip().lower()
    )
    CUSTOM_GENERAL_ROUTE = os.environ.get("CUSTOM_GENERAL_ROUTE", "").strip().lower()

    CACHE_ROUTE_SET = set(env2dict("CACHE_ROUTES", []))

    FORWARD_CONFIG = env2dict(
        "FORWARD_CONFIG",
        [{"base_url": "https://api.openai.com", "route": "/", "type": "openai"}],
    )

    CUSTOM_MODEL_CONFIG = env2dict("CUSTOM_MODEL_CONFIG", {})

    token_rate_limit_conf = env2dict("TOKEN_RATE_LIMIT")
    PRINT_CHAT = os.environ.get("PRINT_CHAT", "False").strip().lower() == "true"

    LOG_OPENAI = os.environ.get("LOG_OPENAI", "False").strip().lower() == "true"
    LOG_GENERAL = os.environ.get("LOG_GENERAL", "False").strip().lower() == "true"

    CACHE_OPENAI = os.environ.get("CACHE_OPENAI", "False").strip().lower() == "true"
    CACHE_GENERAL = os.environ.get("CACHE_GENERAL", "False").strip().lower() == "true"

    BENCHMARK_MODE = os.environ.get("BENCHMARK_MODE", "false").strip().lower() == "true"

    LOG_CACHE_DB_INFO = (
        os.environ.get("LOG_CACHE_DB_INFO", "false").strip().lower() == "true"
    )
    CACHE_BACKEND = os.environ.get("CACHE_BACKEND", "MEMORY").strip()
    CACHE_ROOT_PATH_OR_URL = os.environ.get("CACHE_ROOT_PATH_OR_URL", "..").strip()

    PROXY = os.environ.get("PROXY", "").strip() or None
    GLOBAL_RATE_LIMIT = os.environ.get("GLOBAL_RATE_LIMIT", "").strip() or "inf"
    RATE_LIMIT_BACKEND = os.environ.get("REQ_RATE_LIMIT_BACKEND", "").strip() or None
    RATE_LIMIT_STRATEGY = (
        os.environ.get("RATE_LIMIT_STRATEGY", "fixed-window").strip() or "fixed-window"
    )
    req_rate_limit_dict = env2dict('REQ_RATE_LIMIT')

    DEFAULT_REQUEST_CACHING_VALUE = (
        os.environ.get("DEFAULT_REQUEST_CACHING_VALUE", "false").strip().lower()
        == "true"
    )

    OPENAI_API_KEY = env2dict("OPENAI_API_KEY_CONFIG")

    LEVEL_TO_FWD_KEY = env2dict("FORWARD_KEY_CONFIG")
    LEVEL_MODELS = {int(key): value for key, value in env2dict("LEVEL_MODELS").items()}

    ENV_VAR_SEP = ","

    IP_WHITELIST = env2list("IP_WHITELIST", sep=ENV_VAR_SEP)
    IP_BLACKLIST = env2list("IP_BLACKLIST", sep=ENV_VAR_SEP)
else:
    TIMEOUT = float(config.get('timeout', 10))
    DEFAULT_STREAM_RESPONSE = config.get('default_stream_response', True)

    CHAT_COMPLETION_ROUTE = config.get(
        'chat_completion_route', '/v1/chat/completions'
    ).lower()
    COMPLETION_ROUTE = config.get('completion_route', '/v1/completions').lower()
    EMBEDDING_ROUTE = config.get('embedding_route', '/v1/embeddings').lower()
    CUSTOM_GENERAL_ROUTE = config.get('custom_general_route', '').lower()

    CACHE_ROUTE_SET: Set[str] = set(config.get('cache', {}).get('routes', []))

    openai_additional_start_info = {'cache_routes': CACHE_ROUTE_SET}
    general_additional_start_info = {'cache_routes': CACHE_ROUTE_SET}

    FORWARD_CONFIG = config.get(
        'forward',
        [{"base_url": "https://api.openai.com", "route": "/", "type": "openai"}],
    )

    CUSTOM_MODEL_CONFIG = config.get('custom_model_config', {})

    PRINT_CHAT = config.get('print_chat', False)

    LOG_OPENAI = config.get('log', {}).get('openai', False)
    LOG_GENERAL = config.get('log', {}).get('general', False)

    CACHE_OPENAI = config.get('cache', {}).get('openai', False)
    CACHE_GENERAL = config.get('cache', {}).get('general', False)
    DEFAULT_REQUEST_CACHING_VALUE = config.get('cache', {}).get(
        'default_request_caching_value', False
    )

    BENCHMARK_MODE = config.get('benchmark_mode', False)

    LOG_CACHE_DB_INFO = config.get('log_cache_db_info', False)
    CACHE_BACKEND = config.get('cache', {}).get('backend', 'MEMORY')
    CACHE_ROOT_PATH_OR_URL = config.get('cache', {}).get('root_path_or_url', '.')

    PROXY = config.get('proxy')

    IP_WHITELIST = config.get("ip_whitelist", [])
    IP_BLACKLIST = config.get("ip_blacklist", [])

    _api_key = config.get("api_key", {})
    OPENAI_API_KEY = _api_key.get("openai_key", {})
    LEVEL_TO_FWD_KEY = _api_key.get("forward_key", {})
    LEVEL_MODELS = _api_key.get("level", {})

    _rate_limit = config.get("rate_limit", {})
    _token_rate_limit_list = _rate_limit.get('token_rate_limit', [])
    token_rate_limit_conf = {
        item['route']: item['value'] for item in _token_rate_limit_list
    }
    GLOBAL_RATE_LIMIT = _rate_limit.get('global_rate_limit', 'inf')
    RATE_LIMIT_STRATEGY = _rate_limit.get('strategy', 'fixed-window')
    _req_rate_limit_list = config.get('req_rate_limit', [])
    RATE_LIMIT_BACKEND = config.get('req_rate_limit_backend', None)
    req_rate_limit_dict = {
        item['route']: item['value'] for item in _req_rate_limit_list
    }

    ITER_CHUNK_TYPE = _rate_limit.get('iter_chunk', 'efficiency')

openai_additional_start_info = {}
general_additional_start_info = {}

openai_additional_start_info['cache_routes'] = CACHE_ROUTE_SET
general_additional_start_info['cache_routes'] = CACHE_ROUTE_SET

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

if BENCHMARK_MODE:
    openai_additional_start_info["benchmark_mode"] = BENCHMARK_MODE

openai_additional_start_info["LOG_OPENAI"] = LOG_OPENAI
general_additional_start_info["LOG_GENERAL"] = LOG_GENERAL

if LOG_OPENAI:
    setting_log(openai_route_prefix=OPENAI_ROUTE_PREFIX, print_chat=PRINT_CHAT)

if PRINT_CHAT:
    openai_additional_start_info["print_chat"] = True

DEFAULT_REQUEST_CACHING_VALUE = (DEFAULT_REQUEST_CACHING_VALUE and CACHE_OPENAI) or (
    DEFAULT_REQUEST_CACHING_VALUE and CACHE_GENERAL
)
if CACHE_OPENAI:
    openai_additional_start_info["cache_backend"] = CACHE_BACKEND
    if not CACHE_BACKEND.lower() == 'memory':
        openai_additional_start_info["cache_root_path_or_url"] = CACHE_ROOT_PATH_OR_URL
    openai_additional_start_info[
        "default_request_caching_value"
    ] = DEFAULT_REQUEST_CACHING_VALUE

if CACHE_GENERAL:
    general_additional_start_info["cache_backend"] = CACHE_BACKEND
    if not CACHE_BACKEND.lower() == 'memory':
        general_additional_start_info["cache_root_path_or_url"] = CACHE_ROOT_PATH_OR_URL
    general_additional_start_info[
        "default_request_caching_value"
    ] = DEFAULT_REQUEST_CACHING_VALUE

FWD_KEY = {}
for level, fk_list in LEVEL_TO_FWD_KEY.items():
    for _fk in fk_list:
        FWD_KEY[_fk] = int(level)

if PROXY:
    openai_additional_start_info["proxy"] = PROXY


def get_limiter_key(request: Request):
    limiter_prefix = f"{request.scope.get('root_path')}{request.scope.get('path')}"
    fk_or_sk = request.headers.get("Authorization", "default")
    key = f"{limiter_prefix},{fk_or_sk}"
    return key


def dynamic_request_rate_limit(key: str):
    limite_prefix, fk_or_sk = key.split(',')
    key_level = FWD_KEY.get(fk_or_sk, 0)
    for route in req_rate_limit_dict:
        if key.startswith(route):
            for level_dict in req_rate_limit_dict[route]:
                if level_dict['level'] == key_level:
                    return level_dict['limit']

            break
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


token_interval_conf = {}
for route, rate_limit_list in token_rate_limit_conf.items():
    token_interval_conf.setdefault(route, {})
    for level_dict in rate_limit_list:
        token_interval_conf[route][level_dict['level']] = cvt_token_rate_to_interval(
            level_dict['limit']
        )

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
