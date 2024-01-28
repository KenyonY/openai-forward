from __future__ import annotations

from fastapi.responses import Response
from flaxkv.pack import encode
from loguru import logger

from ...settings import CACHE_OPENAI
from ..database import db_dict


def construct_cache_key(payload_info):
    elements = [
        payload_info['model'],
        payload_info['input'],
        payload_info['encoding_format'],
    ]
    return encode(elements)


def get_cached_embedding_response(payload_info, valid_payload, request, **kwargs):
    """
    Attempts to retrieve a cached response based on the current request's payload information.

    Note:
        If a cache hit occurs, the cached response is immediately returned without contacting the external server.
    """
    if not (CACHE_OPENAI and valid_payload):
        return None, None

    cache_key = construct_cache_key(payload_info)

    if payload_info['caching'] and cache_key in db_dict:
        logger.info(f'embedding uid: {payload_info["uid"]} >>>>> [cache hit]')
        cache_data = db_dict[cache_key]
        content = cache_data['data']

        return Response(content=content, media_type="application/json"), cache_key

    return None, cache_key
