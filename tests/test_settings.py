from openai_forward.settings import (
    CACHE_ROUTE_SET,
    FORWARD_CONFIG,
    FWD_KEY,
    ITER_CHUNK_TYPE,
    LEVEL_MODELS,
    OPENAI_API_KEY,
    TIMEOUT,
)


def test_timeout():
    assert isinstance(TIMEOUT, float)


def test_iter_chunk_type():
    assert ITER_CHUNK_TYPE in ["efficiency", "one-by-one"]


def test_cache_route_set():
    assert isinstance(CACHE_ROUTE_SET, set)


def test_forward_config():
    assert isinstance(FORWARD_CONFIG, list)
    for config in FORWARD_CONFIG:
        assert 'base_url' in config
        assert 'route' in config
        assert 'type' in config


def test_openai_api_key():
    assert isinstance(OPENAI_API_KEY, dict)


def test_fwd_key():
    assert isinstance(FWD_KEY, dict)


def test_level_models():
    assert isinstance(LEVEL_MODELS, dict)
    for key, value in LEVEL_MODELS.items():
        assert isinstance(key, int)
        assert isinstance(value, list)
