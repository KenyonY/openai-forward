from ..settings import (
    CACHE_CHAT_COMPLETION,
    CACHE_EMBEDDING,
    CHAT_COMPLETION_ROUTE,
    EMBEDDING_ROUTE,
)
from .chat.response import get_cached_chat_response
from .database import db_dict
from .embedding.response import get_cached_embedding_response


def get_cached_response(payload_info, valid_payload, route_path, request):
    if route_path == EMBEDDING_ROUTE:
        return get_cached_embedding_response(payload_info, valid_payload, request)
    elif route_path == CHAT_COMPLETION_ROUTE:
        return get_cached_chat_response(payload_info, valid_payload, request)
    else:
        return None, None


def cache_response(cache_key, target_info, route_path):
    if (
        target_info
        and CACHE_CHAT_COMPLETION
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
        and CACHE_EMBEDDING
        and route_path == EMBEDDING_ROUTE
        and cache_key is not None
    ):
        cached_value = bytes(target_info["buffer"])
        db_dict[cache_key] = {
            "data": cached_value,
            "route_path": route_path,
        }
