from flaxkv.pack import decode, encode
from loguru import logger

from ..settings import (
    CACHE_OPENAI,
    CACHE_ROUTE_SET,
    CHAT_COMPLETION_ROUTE,
    EMBEDDING_ROUTE,
)
from .chat.response import gen_response, get_cached_chat_response
from .database import db_dict
from .embedding.response import get_cached_embedding_response


def get_cached_response(
    payload, payload_info, valid_payload, route_path, request, **kwargs
):
    if route_path == EMBEDDING_ROUTE:
        # todo: use general cache replace may be better?
        return get_cached_embedding_response(
            payload_info, valid_payload, request, **kwargs
        )
    elif route_path == CHAT_COMPLETION_ROUTE:
        return get_cached_chat_response(payload_info, valid_payload, request, **kwargs)

    elif route_path in CACHE_ROUTE_SET:
        return get_cached_generic_response(payload, request, route_path)
    else:
        return None, None


def cache_response(cache_key, target_info, route_path, chunk_list):
    if (
        target_info
        and CACHE_OPENAI
        and route_path == CHAT_COMPLETION_ROUTE
        and cache_key is not None
    ):
        cached_value = db_dict.get(cache_key, {"data": []})["data"]
        if len(cached_value) < 10:
            cached_value.append(target_info["assistant"])
            db_dict[cache_key] = {
                "data": cached_value,
                "route_path": route_path,
            }
    elif (
        target_info
        and CACHE_OPENAI
        and route_path == EMBEDDING_ROUTE
        and cache_key is not None
    ):
        cached_value = bytes(target_info["buffer"])
        db_dict[cache_key] = {
            "data": cached_value,
            "route_path": route_path,
        }
    else:
        cache_generic_response(cache_key, route_path, chunk_list)


def cache_generic_response(cache_key, buffer_list, route_path, max_cache=3):
    if cache_key and route_path in CACHE_ROUTE_SET:
        value_list = db_dict.get(cache_key, [])

        if len(value_list) < max_cache:
            value_list.append({"data": buffer_list})
            db_dict[cache_key] = value_list


def get_cached_generic_response(payload: bytes, request, route_path):

    if route_path not in CACHE_ROUTE_SET:
        return None, None

    try:
        cache_key = encode(payload)
        value_list = db_dict.get(cache_key)
        if value_list is None:
            return None, cache_key

        idx = -1
        buffer_list = value_list[idx]["data"]
        if len(buffer_list) == 1:
            logger.info(f'generic cache >>>>>>>> [cache hit]')
            logger.debug(f"cache result: {buffer_list[0]}")
        elif len(buffer_list) > 1:
            logger.info(f'generic cache >>>>>>>> [stream cache hit]')
        else:
            raise ValueError(f"Invalid buffer list: {buffer_list}")
        return gen_response(buffer_list, request), cache_key

    except:
        return None, None
