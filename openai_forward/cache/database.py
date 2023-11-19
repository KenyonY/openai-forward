from flaxkv import dbdict

from ..settings import CACHE_BACKEND, LOG_CACHE_DB_INFO

if CACHE_BACKEND.upper() == "LMDB":
    try:
        import lmdb
    except ImportError:
        raise ImportError("Please install LMDB: pip install lmdb")

    if LOG_CACHE_DB_INFO:
        db_dict = dbdict("./CACHE_LMDB", backend='lmdb', log="INFO", save_log=True)
    else:
        db_dict = dbdict("./CACHE_LMDB", backend='lmdb')

elif CACHE_BACKEND.upper() == "LEVELDB":
    try:
        import plyvel
    except ImportError:
        raise ImportError("Please install LevelDB: pip install plyvel")

    if LOG_CACHE_DB_INFO:
        db_dict = dbdict(
            "./CACHE_LEVELDB", backend='leveldb', log="INFO", save_log=True
        )
    else:
        db_dict = dbdict("./CACHE_LEVELDB", backend='leveldb')

elif CACHE_BACKEND.upper() == "MEMORY":
    db_dict = {}

else:
    raise ValueError(f"Unknown cache backend: {CACHE_BACKEND}")
