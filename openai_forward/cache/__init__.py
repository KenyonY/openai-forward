from ..settings import CHAT_COMPLETION_ROUTE, EMBEDDING_ROUTE
from .chat.response import get_cached_chat_response
from .embedding.response import get_cached_embedding_response


def get_cached_response(payload_info, valid_payload, route_path, request):
    if route_path == EMBEDDING_ROUTE:
        return get_cached_embedding_response(payload_info, valid_payload, request)
    elif route_path == CHAT_COMPLETION_ROUTE:
        return get_cached_chat_response(payload_info, valid_payload, request)
    else:
        return None, None
