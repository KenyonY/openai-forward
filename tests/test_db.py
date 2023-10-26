import os
import shutil
import tempfile

import pytest

try:
    import lmdb

    from openai_forward.cache.database import LMDBDict
except ImportError:
    LMDBDict = None

try:
    import plyvel

    from openai_forward.cache.database import LevelDBDict
except ImportError:
    LevelDBDict = None

try:
    from rocksdict import Rdict
except ImportError:
    Rdict = None

DB_DICTS = [db for db in (LMDBDict, LevelDBDict, Rdict) if db is not None]

# If DB_DICTS is empty，skip the test
if not DB_DICTS:
    pytestmark = pytest.mark.skip(reason="No database modules available")


@pytest.fixture(params=DB_DICTS)
def temp_db(request):
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_db")
    db = request.param(db_path)
    yield db
    db.close()
    shutil.rmtree(temp_dir)


def test_set_get_items(temp_db):
    if isinstance(temp_db, (Rdict, type(None))):
        pytest.skip("Skipping")
    temp_db.set("test_key", "test_value")
    assert temp_db.get("test_key") == "test_value"
    temp_db["another_key"] = "another_value"
    assert temp_db["another_key"] == "another_value"


def test_data_types(temp_db):
    data_types = {
        "int_key": 123,
        "float_key": 123.456,
        "bool_key": True,
        "str_key": "hello",
        # "ndarray_key": np.array([1, 2, 3]),
        "list_key": [1, 2, 3],
        "tuple_key": (1, 2, 3),
        "dict_key": {"a": 1, "b": 2},
    }

    for key, value in data_types.items():
        temp_db[key] = value
        assert temp_db[key] == value


def test_buffered_writing(temp_db):
    if isinstance(temp_db, (Rdict, type(None))):
        pytest.skip("Skipping")
    for i in range(temp_db.MAX_BUFFER_SIZE + 10):
        temp_db[f"key_{i}"] = f"value_{i}"

    assert len(temp_db.buffer_dict) == temp_db.MAX_BUFFER_SIZE + 10


def test_key_checks_and_deletion(temp_db):
    temp_db["key_to_delete"] = "value"
    assert "key_to_delete" in temp_db
    del temp_db["key_to_delete"]
    assert "key_to_delete" not in temp_db


def test_list_keys_values_items(temp_db):
    data = {"key1": "value1", "key2": "value2", "key3": "value3"}

    for key, value in data.items():
        temp_db[key] = value
    assert set(temp_db.keys()) == set(data.keys())
    assert set(temp_db.values()) == set(data.values())
    assert set(temp_db.items()) == set(data.items())


def test_error_scenarios(temp_db):
    if isinstance(temp_db, (Rdict, type(None))):
        pytest.skip("Skipping")

    # Get non-existent key
    with pytest.raises(KeyError):
        _ = temp_db["non_existent_key"]

    # Delete non-existent key
    with pytest.raises(KeyError):
        del temp_db["non_existent_key"]
