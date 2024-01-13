from flaxkv import FlaxKV

from ..settings import CACHE_BACKEND, CACHE_ROOT_PATH_OR_URL, LOG_CACHE_DB_INFO

if CACHE_BACKEND.upper() == "MEMORY":
    db_dict = {}

elif CACHE_BACKEND.lower() in ("leveldb", "lmdb"):

    log, save_log = ("INFO", True) if LOG_CACHE_DB_INFO else (None, False)

    db_dict = FlaxKV(
        "CACHE_DB",
        root_path_or_url=CACHE_ROOT_PATH_OR_URL,
        backend=CACHE_BACKEND.lower(),
        cache=True,
        log=log,
        save_log=save_log,
    )

else:
    raise ValueError(
        f"Unknown cache backend: {CACHE_BACKEND}. The valid backends are: 'leveldb', 'lmdb', 'memory'"
    )
