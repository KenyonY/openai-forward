import queue
import threading
from abc import ABC, abstractmethod

# import numpy as np
import orjson
from loguru import logger

from ..settings import CACHE_BACKEND


class BaseDBDict(ABC):
    MAX_BUFFER_SIZE = 1000
    COMMIT_TIME_INTERVAL = 60

    def __init__(self):
        self.buffered_queue = queue.Queue()
        self.buffer_dict = {}
        self.lock = threading.RLock()

        # Start the background worker
        self.thread_running = True
        self._write_event = threading.Event()
        self.thread = threading.Thread(target=self.background_worker)
        self.thread.daemon = True
        self.thread.start()

    @staticmethod
    def _encode(value):
        if isinstance(value, int):
            return b'i:' + str(value).encode()
        elif isinstance(value, float):
            return b'f:' + str(value).encode()
        elif isinstance(value, bool):
            return b'b:' + str(value).encode()
        elif isinstance(value, str):
            return b's:' + value.encode()
        # elif isinstance(value, np.ndarray):
        #     return b'a:' + value.tobytes()
        elif isinstance(value, list):
            # return b'l:' + np.array(value).tobytes()
            return b'd:' + orjson.dumps(value)
        elif isinstance(value, tuple):
            # return b't:' + np.array(value).tobytes()
            return b'd:' + orjson.dumps(value)
        elif isinstance(value, dict):
            # why use orjson to serialize? Because it's faster than pickle, MessagePack, etc.
            return b'd:' + orjson.dumps(value)
        else:
            raise ValueError(f"Unsupported type {type(value)}")

    @staticmethod
    def _decode(value):
        type_prefix, b_data = value[:2], value[2:]

        if type_prefix == b'i:':
            return int(b_data.decode())
        elif type_prefix == b'f:':
            return float(b_data.decode())
        elif type_prefix == b'b:':
            return b_data.decode() == 'True'
        elif type_prefix == b's:':
            return b_data.decode()
        # elif type_prefix == b'a:':
        #     return np.frombuffer(b_data)
        elif type_prefix == b'l:':
            # return np.frombuffer(b_data).tolist()
            return orjson.loads(b_data)
        elif type_prefix == b't:':
            # return tuple(np.frombuffer(b_data).tolist())
            return tuple(orjson.loads(b_data))
        elif type_prefix == b'd:':
            return orjson.loads(b_data)
        else:
            raise ValueError(f"Unsupported type prefix {type_prefix}")

    def background_worker(self):
        while self.thread_running:
            self._write_event.wait(timeout=self.COMMIT_TIME_INTERVAL)
            self._write_buffer_to_db()

    def close_background_worker(self):
        self._write_buffer_to_db()  # Ensure all buffered items are written to DB
        self.thread_running = False
        self._write_event.set()
        self.thread.join(timeout=30)
        if self.thread.is_alive():
            logger.warning(
                "Warning: Background thread did not finish in time. Some data might not be saved."
            )

    @abstractmethod
    def get(self, key: str):
        pass

    @abstractmethod
    def set(self, key: str, value):
        pass

    @abstractmethod
    def _write_buffer_to_db(self):
        pass

    @abstractmethod
    def keys(self):
        pass

    @abstractmethod
    def values(self):
        pass

    @abstractmethod
    def items(self):
        pass

    @abstractmethod
    def close(self):
        pass


class LMDBDict(BaseDBDict):
    """
    A dictionary-like class that stores key-value pairs in an LMDB database.
    Type:
        key: str
        value: int, float, bool, str, np.ndarray, list, tuple, dict
    """

    def __init__(self, path, map_size=1024**3):
        super().__init__()
        import lmdb

        self.env = lmdb.open(path, max_dbs=1, map_size=map_size)

    def get(self, key: str):
        with self.lock:
            if key in self.buffer_dict:
                return self.buffer_dict[key]

        with self.env.begin() as txn:
            value = txn.get(key.encode())

            if value is None:
                return None
            return self._decode(value)

    def set(self, key, value):
        b_value = self._encode(value)
        with self.lock:
            self.buffer_dict[key] = value
            self.buffered_queue.put((key, b_value))
            # Trigger immediate write if buffer size exceeds MAX_BUFFER_SIZE
            if self.buffered_queue.qsize() >= self.MAX_BUFFER_SIZE:
                self._write_buffer_to_db()

    def _write_buffer_to_db(self):
        items = []
        with self.lock:
            while not self.buffered_queue.empty():
                key, value = self.buffered_queue.get()
                items.append((key, value))

        if items:
            try:
                # print(f"{items=}")
                with self.env.begin(write=True) as txn:
                    for key, value in items:
                        txn.put(key.encode(), value)
                        # print("key", key, "value", value)
                        with self.lock:
                            if key in self.buffer_dict:
                                del self.buffer_dict[key]
            except Exception as e:
                logger.error(f"Error writing to LMDB: {e}")

    def keys(self):
        with self.env.begin() as txn:
            cursor = txn.cursor()
            lmdb_keys = set(
                key.decode() for key in cursor.iternext(keys=True, values=False)
            )

        with self.lock:
            buffer_keys = set(self.buffer_dict.keys())

        return list(lmdb_keys.union(buffer_keys))

    def values(self):
        with self.env.begin() as txn:
            cursor = txn.cursor()
            lmdb_values = [
                self._decode(value)
                for _, value in cursor.iternext(keys=False, values=True)
            ]

        with self.lock:
            buffer_values = list(self.buffer_dict.values())

        return lmdb_values + buffer_values

    def items(self):
        with self.env.begin() as txn:
            cursor = txn.cursor()
            lmdb_items = [
                (key.decode(), self._decode(value))
                for key, value in cursor.iternext(keys=True, values=True)
            ]

        with self.lock:
            buffer_items = list(self.buffer_dict.items())

        return lmdb_items + buffer_items

    def __getitem__(self, key: str):
        value = self.get(key)
        if value is None:
            raise KeyError(f"Key {key} not found in the database.")
        return value

    def __setitem__(self, key: str, value):
        self.set(key, value)

    def __contains__(self, key: str):
        with self.lock:
            if key in self.buffer_dict:
                return True

        with self.env.begin() as txn:
            return txn.get(key.encode()) is not None

    def __delitem__(self, key: str):
        if key in self:
            with self.lock:
                if key in self.buffer_dict:
                    del self.buffer_dict[key]
                    return

            with self.env.begin(write=True) as txn:
                txn.delete(key.encode())
        else:
            raise KeyError(f"Key {key} not found in the database.")

    def close(self):
        self.close_background_worker()
        self.env.close()
        logger.info("Closed LMDB successfully.")

    def set_mapsize(self, map_size):
        """Change the maximum size of the map file.
        This function will fail if any transactions are active in the current process.
        """
        try:
            self.env.set_mapsize(map_size)
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
        super().__init__()
        import plyvel

        self.db = plyvel.DB(path, create_if_missing=True)

    def get(self, key: str):
        with self.lock:
            if key in self.buffer_dict:
                return self.buffer_dict[key]

        value = self.db.get(key.encode())
        if value is None:
            return None
        return self._decode(value)

    def set(self, key, value):
        b_value = self._encode(value)
        with self.lock:
            self.buffer_dict[key] = value
            self.buffered_queue.put((key, b_value))
            if self.buffered_queue.qsize() >= self.MAX_BUFFER_SIZE:
                self._write_buffer_to_db()

    def _write_buffer_to_db(self):
        items = []
        with self.lock:
            while not self.buffered_queue.empty():
                key, value = self.buffered_queue.get()
                items.append((key, value))

        if items:
            try:
                with self.db.write_batch() as wb:
                    for key, value in items:
                        wb.put(key.encode(), value)
                        with self.lock:
                            if key in self.buffer_dict:
                                del self.buffer_dict[key]
            except Exception as e:
                logger.error(f"Error writing to LevelDB: {e}")

    def keys(self):
        with self.db.snapshot() as snapshot:
            db_keys = set(key.decode() for key, _ in snapshot.iterator())

        with self.lock:
            buffer_keys = set(self.buffer_dict.keys())

        return list(db_keys.union(buffer_keys))

    def values(self):
        with self.db.snapshot() as snapshot:
            db_values = [self._decode(value) for _, value in snapshot.iterator()]

        with self.lock:
            buffer_values = list(self.buffer_dict.values())

        return db_values + buffer_values

    def items(self):
        with self.db.snapshot() as snapshot:
            db_items = [
                (key.decode(), self._decode(value))
                for key, value in snapshot.iterator()
            ]

        with self.lock:
            buffer_items = list(self.buffer_dict.items())

        return db_items + buffer_items

    def __getitem__(self, key: str):
        value = self.get(key)
        if value is None:
            raise KeyError(f"Key {key} not found in the database.")
        return value

    def __setitem__(self, key: str, value):
        self.set(key, value)

    # def __contains__(self, key: str):
    #     with self.lock:
    #         if key in self.buffer_dict:
    #             return True
    #     return self.db.get(key.encode()) is not None

    def __contains__(self, key: str):
        with self.lock:
            if key in self.buffer_dict:
                return True
        with self.db.snapshot() as snapshot:
            return snapshot.get(key.encode()) is not None

    def __delitem__(self, key: str):
        if key in self:
            with self.lock:
                if key in self.buffer_dict:
                    del self.buffer_dict[key]
                    return
            self.db.delete(key.encode())
        else:
            raise KeyError(f"Key {key} not found in the database.")

    def close(self):
        self.close_background_worker()
        self.db.close()
        logger.info("Closed LevelDB successfully.")


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
