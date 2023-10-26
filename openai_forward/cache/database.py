import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass

import orjson
from loguru import logger

from ..settings import CACHE_BACKEND


class DBContextManager:
    def __init__(self, use_db: str, path: str, **kwargs):
        self.use_db = use_db
        if use_db == "lmdb":
            import lmdb

            self._db = lmdb.open(
                path,
                max_dbs=kwargs.get('max_dbs', 1),
                map_size=kwargs.get('map_size', 1024**3),
            )

        elif use_db == "leveldb":
            import plyvel

            self._db = plyvel.DB(path, create_if_missing=True)
        else:
            raise ValueError(f"Unsupported DB type {use_db}.")

    def get_db(self):
        return self._db

    def static_view(self):
        if self.use_db == "lmdb":
            return self._db.begin()
        elif self.use_db == "leveldb":
            return self._db.snapshot()
        else:
            raise ValueError(f"Unsupported DB type {self.use_db}.")

    def close_view(self, static_view):
        if self.use_db == "lmdb":
            return static_view.abort()
        elif self.use_db == "leveldb":
            return static_view.close()
        else:
            raise ValueError(f"Unsupported DB type {self.use_db}.")

    def write(self):
        if self.use_db == "lmdb":
            return self._db.begin(write=True)
        elif self.use_db == "leveldb":
            return self._db.write_batch()
        else:
            raise ValueError(f"Unsupported DB type {self.use_db}.")

    def close(self):
        if self.use_db == "lmdb":
            return self._db.close()
        elif self.use_db == "leveldb":
            return self._db.close()
        else:
            raise ValueError(f"Unsupported DB type {self.use_db}.")


class BaseDBDict(ABC):
    MAX_BUFFER_SIZE = 1000
    COMMIT_TIME_INTERVAL = 60 * 60

    @dataclass(frozen=True)
    class enc_prefix:
        str: bytes = b's'
        int: bytes = b'i'
        float: bytes = b'f'
        bool: bytes = b'b'
        list: bytes = b'l'
        tuple: bytes = b't'
        dict: bytes = b'd'
        array: bytes = b'a'

    def __init__(self, db, path, **kwargs):
        self.db = DBContextManager(use_db=db, path=path, **kwargs)
        self.static_view = self.db.static_view()

        self.buffered_count = 0
        self.buffer_dict = {}
        self.delete_buffer_set = set()
        self.buffer_lock = threading.Lock()
        self.db_lock = threading.Lock()

        self._write_event = threading.Event()
        self._latest_write_num = 0
        self.thread_running = True
        self._thread = threading.Thread(target=self.background_worker)
        self._thread.daemon = True

        # Start the background worker
        self.start()

    def start(self):
        self.thread_running = True
        self._thread.start()

    @staticmethod
    def diff_buffer(a: dict, b: dict):
        return {
            key: value for key, value in a.items() if key not in b or b[key] != value
        }

    @classmethod
    def _encode(cls, value):
        if isinstance(value, int):
            return cls.enc_prefix.int + str(value).encode()
        elif isinstance(value, float):
            return cls.enc_prefix.float + str(value).encode()
        elif isinstance(value, bool):
            return cls.enc_prefix.bool + str(value).encode()
        elif isinstance(value, str):
            return cls.enc_prefix.str + value.encode()
        elif isinstance(value, list):
            return cls.enc_prefix.list + orjson.dumps(value)
        elif isinstance(value, tuple):
            return cls.enc_prefix.tuple + orjson.dumps(value)
        elif isinstance(value, dict):
            return cls.enc_prefix.dict + orjson.dumps(value)
        else:
            raise ValueError(f"Unsupported type {type(value)}")

    @classmethod
    def _decode(cls, value):

        type_prefix, b_data = value[:1], value[1:]

        if type_prefix == cls.enc_prefix.int:
            return int(b_data.decode())
        elif type_prefix == cls.enc_prefix.float:
            return float(b_data.decode())
        elif type_prefix == cls.enc_prefix.bool:
            return b_data.decode() == 'True'
        elif type_prefix == cls.enc_prefix.str:
            return b_data.decode()
        elif type_prefix == cls.enc_prefix.list:
            return orjson.loads(b_data)
        elif type_prefix == cls.enc_prefix.tuple:
            return tuple(orjson.loads(b_data))
        elif type_prefix == cls.enc_prefix.dict:
            return orjson.loads(b_data)
        else:
            raise ValueError(f"Unsupported type prefix {type_prefix}")

    def background_worker(self):
        while self.thread_running:
            self._write_event.wait(timeout=self.COMMIT_TIME_INTERVAL)
            self._write_event.clear()
            self._write_buffer_to_db(current_write_num=self._latest_write_num)

    def write_db_immediately(self):
        self._write_event.set()

    def close_background_worker(self):
        self._latest_write_num += 1
        self.write_db_immediately()
        self.thread_running = False
        self._thread.join(timeout=10)
        if self._thread.is_alive():
            logger.warning(
                "Warning: Background thread did not finish in time. Some data might not be saved."
            )

    def get(self, key: str):
        with self.buffer_lock:
            if key in self.delete_buffer_set:
                return None

            if key in self.buffer_dict:
                return self.buffer_dict[key]

            value = self.static_view.get(key.encode())
            if value is None:
                return None
            return self._decode(value)

    def get_db_value(self, key: str):
        return self.static_view.get(key.encode())

    def get_batch(self, keys):
        values = []
        for key in keys:
            if self.delete_buffer_set and key in self.delete_buffer_set:
                values.append(None)
                continue
            if key in self.buffer_dict:
                values.append(self.buffer_dict[key])
                continue
            value = self.static_view.get(key.encode())
            if value is not None:
                value = self._decode(value)
            values.append(value)
        return values

    def set(self, key, value):
        with self.buffer_lock:
            self.buffer_dict[key] = value
            self.delete_buffer_set.discard(key)

            self.buffered_count += 1
            # Trigger immediate write if buffer size exceeds MAX_BUFFER_SIZE
            if self.buffered_count >= self.MAX_BUFFER_SIZE:
                print("Trigger immediate write")
                self._latest_write_num += 1
                self.buffered_count = 0
                self.write_db_immediately()

    def _write_buffer_to_db(self, current_write_num: int):
        with self.buffer_lock:
            logger.debug(f"Trigger write")
            logger.debug(f"{current_write_num=}")
            if not self.buffer_dict or self.delete_buffer_set:
                logger.debug(f"buffer为空{self._latest_write_num=} {current_write_num=}")
                return
            else:
                buffer_dict_snapshot = self.buffer_dict.copy()
                delete_buffer_set_snapshot = self.delete_buffer_set.copy()
        try:
            # enforce atomicity
            with self.db.write() as wb:
                for key, value in buffer_dict_snapshot.items():
                    wb.put(key.encode(), self._encode(value))
                for key in delete_buffer_set_snapshot:
                    wb.delete(key.encode())

            with self.buffer_lock:
                logger.info("reset buffer")
                self.delete_buffer_set = (
                    self.delete_buffer_set - delete_buffer_set_snapshot
                )
                self.buffer_dict = self.diff_buffer(
                    self.buffer_dict, buffer_dict_snapshot
                )

                self.db.close_view(self.static_view)
                self.static_view = self.db.static_view()

        except Exception as e:
            logger.error(f"Error writing to {self.db.use_db}: {e}")

    @abstractmethod
    def keys(self):
        pass

    @abstractmethod
    def values(self):
        pass

    @abstractmethod
    def items(self):
        pass

    def __getitem__(self, key: str):
        value = self.get(key)
        if value is None:
            raise KeyError(f"Key {key} not found in the database.")
        return value

    def __setitem__(self, key: str, value):
        self.set(key, value)

    def __delitem__(self, key: str):
        if key in self:
            with self.buffer_lock:
                self.delete_buffer_set.add(key)
                self.buffered_count += 1
                if key in self.buffer_dict:
                    del self.buffer_dict[key]
                    return
        else:
            raise KeyError(f"Key {key} not found in the database.")

    def __contains__(self, key: str):
        with self.buffer_lock:
            if key in self.buffer_dict:
                return True

            return self.static_view.get(key.encode()) is not None

    def close(self):
        self.close_background_worker()
        self.db.close()
        logger.info(f"Closed ({self.db.use_db.upper()}) successfully")


class LMDBDict(BaseDBDict):
    """
    A dictionary-like class that stores key-value pairs in an LMDB database.
    Type:
        key: str
        value: int, float, bool, str, list, tuple, dict, and np.ndarray,
    """

    def __init__(self, path, map_size=1024**3):
        super().__init__("lmdb", path, max_dbs=1, map_size=map_size)

    def get_db_value(self, key: str):
        value = self.static_view.get(key.encode())
        return value

    def keys(self):
        with self.buffer_lock:
            session = self.db.static_view()
            cursor = session.cursor()
            delete_buffer_set = self.delete_buffer_set.copy()
            buffer_keys = set(self.buffer_dict.keys())

        lmdb_keys = set(
            key.decode() for key in cursor.iternext(keys=True, values=False)
        )
        self.db.close_view(session)

        return list(lmdb_keys.union(buffer_keys) - delete_buffer_set)

    def values(self):

        with self.buffer_lock:
            session = self.db.static_view()
            cursor = session.cursor()
            delete_buffer_set = self.delete_buffer_set.copy()
            buffer_values = list(self.buffer_dict.values())

        lmdb_values = [
            self._decode(value)
            for key, value in cursor.iternext(keys=True, values=True)
            if key.decode() not in delete_buffer_set
        ]

        session.abort()
        return lmdb_values + buffer_values

    def items(self):
        with self.buffer_lock:
            session = self.db.static_view()
            cursor = session.cursor()
            buffer_dict = self.buffer_dict.copy()
            delete_buffer_set = self.delete_buffer_set.copy()

        db_dict = {
            key.decode(): self._decode(value)
            for key, value in cursor.iternext(keys=True, values=True)
            if key not in delete_buffer_set
        }
        db_dict.update(buffer_dict)

        session.abort()

        return db_dict.items()

    def set_mapsize(self, map_size):
        """Change the maximum size of the map file.
        This function will fail if any transactions are active in the current process.
        """
        try:
            self.db.get_db().set_mapsize(map_size)
        except Exception as e:
            logger.error(f"Error setting map size: {e}")


class LevelDBDict(BaseDBDict):
    """
    A dictionary-like class that stores key-value pairs in a LevelDB database.
    Type:
        key: str
        value: int, float, bool, str, np.ndarray, list, tuple, dict
    """

    def __init__(self, path):
        super().__init__("leveldb", path=path)

    def keys(self):
        with self.buffer_lock:
            session = self.db.static_view()
            delete_buffer_set = self.delete_buffer_set.copy()
            buffer_keys = set(self.buffer_dict.keys())
            snapshot = self.db.static_view()

        db_keys = set(key.decode() for key, _ in snapshot.iterator())
        self.db.close_view(session)

        return list(db_keys.union(buffer_keys) - delete_buffer_set)

    def values(self):
        with self.buffer_lock:
            snapshot = self.db.static_view()
            delete_buffer_set = self.delete_buffer_set.copy()
            buffer_values = list(self.buffer_dict.values())

        db_values = [
            self._decode(value)
            for key, value in snapshot.iterator()
            if key not in delete_buffer_set
        ]

        snapshot.close()

        return db_values + buffer_values

    def items(self):
        with self.buffer_lock:
            snapshot = self.db.static_view()
            delete_buffer_set = self.delete_buffer_set.copy()
            buffer_dict = self.buffer_dict.copy()

        _db_dict = {}
        for key, value in snapshot.iterator():
            dk = self._decode(key)
            if dk not in delete_buffer_set:
                _db_dict[dk] = self._decode(value)

        _db_dict.update(buffer_dict)

        snapshot.close()
        return _db_dict.items()


if CACHE_BACKEND.upper() == "LMDB":
    db_dict = LMDBDict("./CACHE_LMDB")

elif CACHE_BACKEND.upper() == "ROCKSDB":
    from rocksdict import Rdict

    db_dict = Rdict("./CACHE_ROCKSDB")

elif CACHE_BACKEND.upper() == "LEVELDB":
    db_dict = LevelDBDict("./CACHE_LEVELDB")

elif CACHE_BACKEND.upper() == "MEMORY":
    db_dict = {}
else:
    raise ValueError(f"Unknown cache backend: {CACHE_BACKEND}")
