from flaxkv import FlaxKV

from ..settings import CACHE_BACKEND, CACHE_ROOT_PATH_OR_URL, LOG_CACHE_DB_INFO

if CACHE_BACKEND.upper() == "MEMORY":
    db_dict = {}

elif CACHE_BACKEND.lower() in ("leveldb", "lmdb"):

    if LOG_CACHE_DB_INFO:
        db_dict = FlaxKV(
            "CACHE_DB",
            root_path_or_url=CACHE_ROOT_PATH_OR_URL,
            backend=CACHE_BACKEND.lower(),
            cache=True,
            log="INFO",
            save_log=True,
        )
    else:
        db_dict = FlaxKV(
            "CACHE_DB",
            root_path_or_url=CACHE_ROOT_PATH_OR_URL,
            backend=CACHE_BACKEND.lower(),
            cache=True,
        )

else:
    raise ValueError(
        f"Unknown cache backend: {CACHE_BACKEND}. The valid backends are: 'leveldb', 'lmdb', 'memory'"
    )
