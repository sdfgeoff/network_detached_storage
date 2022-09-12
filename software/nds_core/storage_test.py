import sqlite3
from .storage import Storage, _get_db_version, _create_v1_db, _upgrade_v1_to_v2, _ensure_db_up_to_date, UserData

def test_create_storage():
    s = Storage(":memory:")


def test_empty_db_is_v_neg1():
    db = sqlite3.connect(":memory:")
    assert _get_db_version(db) == 0

def test_init_db_makes_version_v0():
    db = sqlite3.connect(":memory:")
    # assert _get_db_version(db) == -1
    _create_v1_db(db)
    assert _get_db_version(db) == 1

def test_can_upgrade_to_v1():
    db = sqlite3.connect(":memory:")
    # assert _get_db_version(db) == -1
    _create_v1_db(db)
    assert _get_db_version(db) == 1
    _upgrade_v1_to_v2(db)
    assert _get_db_version(db) == 2


def test_upgrades_all():
    db = sqlite3.connect(":memory:")
    _ensure_db_up_to_date(db)
    assert _get_db_version(db) == 2


def test_can_create_user():
    storage = Storage(":memory:")
    assert storage.create_user("testUser", "testSecret") == 1
    assert storage.create_user("testUser2", "testSecret2") == 2

    assert storage.query_users_by_ids((1,))[0].user_name == "testUser"
    assert storage.query_users_by_ids((2,))[0].user_id == 2
    assert storage.query_users_by_ids((2,))[0].secret == "testSecret2"

    assert len(storage.query_users_by_ids((1,))) == 1
    assert len(storage.query_users_by_ids((1,2))) == 2
    assert len(storage.query_users_by_ids((5,))) == 0

def test_can_update_user():
    storage = Storage(":memory:")
    user_id = storage.create_user("testUser", "testSecret")
    user_id2 = storage.create_user("testUser2", "testSecret2")
    assert storage.query_users_by_ids((user_id,))[0].secret == "testSecret"
    storage.update_user(UserData(
        user_id=user_id,
        user_name="testUser",
        secret="newSecret"
    ))
    assert storage.query_users_by_ids((user_id,))[0].secret == "newSecret"
    assert storage.query_users_by_ids((2,))[0].secret == "testSecret2"



