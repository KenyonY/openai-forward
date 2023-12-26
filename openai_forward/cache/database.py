from flaxkv import FlaxKV

from ..settings import CACHE_BACKEND, CACHE_ROOT_PATH_OR_URL, LOG_CACHE_DB_INFO

cache = True

if CACHE_BACKEND.upper() == "LMDB":
    try:
        import lmdb
    except ImportError:
        raise ImportError("Please install LMDB: pip install lmdb")

    if LOG_CACHE_DB_INFO:
        db_dict = FlaxKV(
            "CACHE_LMDB",
            root_path_or_url=CACHE_ROOT_PATH_OR_URL,
            backend='lmdb',
            cache=cache,
            log="INFO",
            save_log=True,
        )
    else:
        db_dict = FlaxKV(
            "CACHE_LMDB",
            root_path_or_url=CACHE_ROOT_PATH_OR_URL,
            backend='lmdb',
            cache=cache,
        )

elif CACHE_BACKEND.upper() == "LEVELDB":
    try:
        import plyvel
    except ImportError:
        raise ImportError("Please install LevelDB: pip install plyvel")

    if LOG_CACHE_DB_INFO:
        db_dict = FlaxKV(
            "CACHE_LEVELDB",
            root_path_or_url=CACHE_ROOT_PATH_OR_URL,
            backend='leveldb',
            cache=cache,
            log="INFO",
            save_log=True,
        )
    else:
        db_dict = FlaxKV(
            "CACHE_LEVELDB",
            root_path_or_url=CACHE_ROOT_PATH_OR_URL,
            backend='leveldb',
            cache=cache,
        )

elif CACHE_BACKEND.upper() == "REMOTE":
    if LOG_CACHE_DB_INFO:
        db_dict = FlaxKV(
            "REMOTE_DB",
            root_path_or_url=CACHE_ROOT_PATH_OR_URL,
            backend="leveldb",
            cache=cache,
            log="INFO",
            save_log=True,
        )
    else:
        db_dict = FlaxKV(
            "REMOTE_DB",
            root_path_or_url=CACHE_ROOT_PATH_OR_URL,
            backend="leveldb",
            cache=cache,
        )

elif CACHE_BACKEND.upper() == "MEMORY":
    db_dict = {}

else:
    raise ValueError(f"Unknown cache backend: {CACHE_BACKEND}")
