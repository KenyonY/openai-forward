import json
import os
from typing import Dict, List, Literal, Optional, Tuple, Union

from attrs import asdict, define, field, filters


class Base:
    def to_dict(self, drop_none=True):
        if drop_none:
            return asdict(self, filter=filters.exclude(type(None)))
        return asdict(self)


@define(slots=True)
class ForwardItem(Base):
    base_url: str
    route: str
    type: Literal["openai", "general"] = field(default="general")


@define(slots=True)
class Forward(Base):
    forward: List[ForwardItem] = [
        ForwardItem(base_url="https://api.openai.com", route="/", type="openai"),
        ForwardItem(
            base_url="https://generativelanguage.googleapis.com",
            route="/gemini",
            type="general",
        ),
    ]

    # CHAT_COMPLETION_ROUTE: str = '/v1/chat/completions'
    # COMPLETION_ROUTE: str = '/v1/completions'
    # EMBEDDING_ROUTE: str = '/v1/embeddings'

    def convert_to_env(self, set_env=False):
        env_dict = {'FORWARD_CONFIG': json.dumps([i.to_dict() for i in self.forward])}

        if set_env:
            for key, value in env_dict.items():
                os.environ[key] = value
        return env_dict


@define(slots=True)
class CacheConfig(Base):
    backend: str = 'LevelDB'
    root_path_or_url: str = './FLAXKV_DB'
    default_request_caching_value: bool = False
    cache_openai: bool = False
    cache_general: bool = False
    cache_routes: List = ['/v1/chat/completions']

    def convert_to_env(self, set_env=False):

        env_dict = {}

        env_dict['CACHE_OPENAI'] = str(self.cache_openai)
        env_dict['CACHE_GENERAL'] = str(self.cache_general)

        env_dict['CACHE_BACKEND'] = self.backend
        env_dict['CACHE_ROOT_PATH_OR_URL'] = self.root_path_or_url
        env_dict['DEFAULT_REQUEST_CACHING_VALUE'] = str(
            self.default_request_caching_value
        )
        env_dict['CACHE_ROUTES'] = json.dumps(self.cache_routes)

        if set_env:
            for key, value in env_dict.items():
                os.environ[key] = value
        return env_dict


@define(slots=True)
class RateLimitType(Base):
    route: str
    value: str


@define(slots=True)
class RateLimit(Base):
    global_rate_limit: str = 'inf'
    token_rate_limit: List[RateLimitType] = [
        RateLimitType(route="/v1/chat/completions", value="60/second"),
        RateLimitType(route="/v1/completions", value="60/second"),
    ]
    req_rate_limit: List[RateLimitType] = [
        RateLimitType(route="/v1/chat/completions", value="100/2minutes"),
        RateLimitType(route="/v1/completions", value="60/minute"),
        RateLimitType(route="/v1/embeddings", value="100/2minutes"),
    ]
    iter_chunk: Literal['one-by-one', 'efficiency'] = 'one-by-one'
    strategy: Literal[
        'fixed_window', 'moving-window', 'fixed-window-elastic-expiry'
    ] = 'moving-window'

    def convert_to_env(self, set_env=False):
        env_dict = {}
        env_dict['GLOBAL_RATE_LIMIT'] = self.global_rate_limit
        env_dict['RATE_LIMIT_STRATEGY'] = self.strategy
        env_dict['TOKEN_RATE_LIMIT'] = json.dumps(
            {i.route: i.value for i in self.token_rate_limit if i.route and i.value}
        )
        env_dict['REQ_RATE_LIMIT'] = json.dumps(
            {i.route: i.value for i in self.req_rate_limit if i.route and i.value}
        )
        env_dict['ITER_CHUNK_TYPE'] = self.iter_chunk
        if set_env:
            for key, value in env_dict.items():
                os.environ[key] = value
        return env_dict


@define(slots=True)
class ApiKeyItem(Base):
    api_key: Optional[str] = None
    level: Optional[int] = None


@define(slots=True)
class ApiKeyLevel(Base):
    level: int = 0
    models: str = '*'


@define(slots=True)
class ApiKey(Base):
    openai_key: List[ApiKeyItem] = [ApiKeyItem("", 0)]
    forward_key: List[ApiKeyItem] = [ApiKeyItem("", 0)]
    level: List[ApiKeyLevel] = [
        ApiKeyLevel(),
        ApiKeyLevel(level=1, models="gpt-3.5-turbo"),
    ]

    @staticmethod
    def format(keys: List[ApiKeyItem]):
        target_dict = {}
        for i in keys:
            try:
                if i.api_key is None or i.level is None:
                    continue
                if not i.api_key.strip():
                    continue
                target_dict[i.api_key.strip()] = int(i.level)
            except Exception:
                continue
        return target_dict

    def convert_to_env(self, set_env=False):
        env_dict = {}
        env_dict['OPENAI_API_KEY'] = json.dumps(self.format(self.openai_key))
        env_dict['FORWARD_KEY'] = json.dumps(self.format(self.forward_key))
        if set_env:
            for key, value in env_dict.items():
                os.environ[key] = value
        return env_dict


@define(slots=True)
class Log(Base):
    LOG_GENERAL: bool = True
    LOG_OPENAI: bool = True

    # chat: bool = True
    # completion: bool = True
    # embedding: bool = False

    # CHAT_COMPLETION_ROUTE: str = '/v1/chat/completions'
    # COMPLETION_ROUTE: str = '/v1/completions'
    # EMBEDDING_ROUTE: str = '/v1/embeddings'

    def convert_to_env(self):
        env_dict = {}
        env_dict['LOG_GENERAL'] = str(self.LOG_GENERAL)
        env_dict['LOG_OPENAI'] = str(self.LOG_OPENAI)

        # env_dict['CHAT_COMPLETION_ROUTE'] = str(self.CHAT_COMPLETION_ROUTE)
        # env_dict['COMPLETION_ROUTE'] = str(self.COMPLETION_ROUTE)
        # env_dict['EMBEDDING_ROUTE'] = str(self.EMBEDDING_ROUTE)
        for key, value in env_dict.items():
            os.environ[key] = value
        return env_dict


@define(slots=True)
class Config(Base):
    forward: Forward = Forward()

    api_key: ApiKey = ApiKey()

    cache: CacheConfig = CacheConfig()

    rate_limit: RateLimit = RateLimit()

    log: Log = Log()

    timezone: str = 'Asia/Shanghai'
    timeout: int = 6
    benchmark_mode: bool = False
    proxy: str = ''

    def convert_to_env(self, set_env=False):
        env_dict = {}
        env_dict.update(self.forward.convert_to_env())
        env_dict.update(self.api_key.convert_to_env())
        env_dict.update(self.cache.convert_to_env())
        env_dict.update(self.rate_limit.convert_to_env())
        env_dict.update(self.log.convert_to_env())

        env_dict['TZ'] = self.timezone
        env_dict['TIMEOUT'] = str(self.timeout)
        env_dict['BENCHMARK_MODE'] = str(self.benchmark_mode)
        env_dict['PROXY'] = self.proxy

        if set_env:
            for key, value in env_dict.items():
                os.environ[key] = value
        return env_dict
