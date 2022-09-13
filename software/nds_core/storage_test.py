import sqlite3
import pytest
from .storage import (
    Storage,
    _get_db_version,
    _create_v1_db,
    _upgrade_v1_to_v2,
    _ensure_db_up_to_date,
    UserData,
    UserNameAlreadyExists,
)


def test_create_storage() -> None:
    s = Storage(":memory:")


def test_empty_db_is_v_neg1() -> None:
    db = sqlite3.connect(":memory:")
    assert _get_db_version(db) == 0


def test_init_db_makes_version_v0() -> None:
    db = sqlite3.connect(":memory:")
    # assert _get_db_version(db) == -1
    _create_v1_db(db)
    assert _get_db_version(db) == 1


def test_can_upgrade_to_v1() -> None:
    db = sqlite3.connect(":memory:")
    # assert _get_db_version(db) == -1
    _create_v1_db(db)
    assert _get_db_version(db) == 1
    _upgrade_v1_to_v2(db)
    assert _get_db_version(db) == 2


def test_upgrades_all() -> None:
    db = sqlite3.connect(":memory:")
    _ensure_db_up_to_date(db)
    assert _get_db_version(db) == 2


def test_can_create_user() -> None:
    storage = Storage(":memory:")
    assert storage.create_user("testUser", b"testSecret") == 1
    assert storage.create_user("testUser2", b"testSecret2") == 2

    assert storage.query_users_by_ids([1])[0].user_name == "testUser"
    assert storage.query_users_by_ids([2])[0].user_id == 2
    assert storage.query_users_by_ids([2])[0].secret == b"testSecret2"

    assert len(storage.query_users_by_ids([1])) == 1
    assert len(storage.query_users_by_ids([1, 2])) == 2
    assert len(storage.query_users_by_ids([5])) == 0


def test_can_update_user() -> None:
    storage = Storage(":memory:")
    user_id = storage.create_user("testUser", b"testSecret")
    user_id2 = storage.create_user("testUser2", b"testSecret2")
    assert storage.query_users_by_ids([user_id])[0].secret == b"testSecret"
    storage.update_user(
        UserData(user_id=user_id, user_name="testUser", secret=b"newSecret")
    )
    assert storage.query_users_by_ids([user_id])[0].secret == b"newSecret"
    assert storage.query_users_by_ids([2])[0].secret == b"testSecret2"


def test_cannot_create_duplicate_username() -> None:
    storage = Storage(":memory:")
    user_id = storage.create_user("testUser", b"testSecret")

    # By Creating
    with pytest.raises(UserNameAlreadyExists):
        storage.create_user("testUser", b"testSecret2")

    # By Renaming
    user_id2 = storage.create_user("testUser2", b"testSecret")

    with pytest.raises(UserNameAlreadyExists):
        storage.update_user(
            UserData(user_id=user_id2, user_name="testUser", secret=b"newSecret")
        )


def test_query_user_by_name() -> None:
    storage = Storage(":memory:")
    user_1 = storage.create_user("testUser", b"testSecret")
    user_2 = storage.create_user("testUser2", b"testSecret2")

    u1 = storage.query_user_by_user_name("testUser")
    assert u1 is not None
    assert u1.user_id == user_1

    u2 = storage.query_user_by_user_name("testUser2")
    assert u2 is not None
    assert u2.user_id == user_2

    assert storage.query_user_by_user_name("asoiuqwer") == None
