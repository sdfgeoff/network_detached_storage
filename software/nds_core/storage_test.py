import sqlite3
import pytest
import datetime
from .storage import (
    Storage,
    _get_db_version,
    _create_v1_db,
    _upgrade_v1_to_v2,
    _ensure_db_up_to_date,
    UserData,
    UserNameAlreadyExists,
    UserIDDoesNotExist,
    ColorData,
)


def test_create_storage() -> None:
    Storage(":memory:")


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
    assert _get_db_version(db) == 4


def test_can_create_user() -> None:
    storage = Storage(":memory:")
    assert storage.create_user("testUser", b"testSecret", ColorData(0, 0, 0)) == 1
    assert storage.create_user("testUser2", b"testSecret2", ColorData(0, 0, 0)) == 2

    assert storage.query_users_by_ids([1])[0].user_name == "testUser"
    assert storage.query_users_by_ids([2])[0].user_id == 2
    assert storage.query_users_by_ids([2])[0].secret == b"testSecret2"

    assert len(storage.query_users_by_ids([1])) == 1
    assert len(storage.query_users_by_ids([1, 2])) == 2
    assert len(storage.query_users_by_ids([5])) == 0


def test_can_update_user() -> None:
    storage = Storage(":memory:")
    user_id = storage.create_user("testUser", b"testSecret", ColorData(0, 1, 0))
    user_id2 = storage.create_user("testUser2", b"testSecret2", ColorData(0, 2, 0))
    assert storage.query_users_by_ids([user_id])[0].secret == b"testSecret"
    storage.update_user(
        UserData(
            user_id=user_id,
            user_name="testUser",
            secret=b"newSecret",
            color=ColorData(0, 0, 3),
        )
    )
    assert storage.query_users_by_ids([user_id])[0].secret == b"newSecret"
    assert storage.query_users_by_ids([user_id])[0].color == ColorData(0, 0, 3)

    assert storage.query_users_by_ids([user_id2])[0].secret == b"testSecret2"


def test_cannot_create_duplicate_username() -> None:
    storage = Storage(":memory:")
    storage.create_user("testUser", b"testSecret", ColorData(0, 0, 0))

    # By Creating
    with pytest.raises(UserNameAlreadyExists):
        storage.create_user("testUser", b"testSecret2", ColorData(0, 0, 0))

    # By Renaming
    user_id2 = storage.create_user("testUser2", b"testSecret", ColorData(0, 0, 0))

    with pytest.raises(UserNameAlreadyExists):
        storage.update_user(
            UserData(
                user_id=user_id2,
                user_name="testUser",
                secret=b"newSecret",
                color=ColorData(0, 0, 0),
            )
        )


def test_query_user_by_name() -> None:
    storage = Storage(":memory:")
    user_1 = storage.create_user("testUser", b"testSecret", ColorData(0, 0, 0))
    user_2 = storage.create_user("testUser2", b"testSecret2", ColorData(0, 0, 0))

    u1 = storage.query_user_by_user_name("testUser")
    assert u1 is not None
    assert u1.user_id == user_1

    u2 = storage.query_user_by_user_name("testUser2")
    assert u2 is not None
    assert u2.user_id == user_2

    assert storage.query_user_by_user_name("asoiuqwer") is None


def test_create_session_for_user() -> None:
    storage = Storage(":memory:")

    # Create for nonexistant user fails
    with pytest.raises(UserIDDoesNotExist):
        storage.create_session_for_user(
            user_id=123,
            session_key="asdfwargle",
            creation_date=datetime.datetime.now(),
            expiry_date=datetime.datetime.now(),
        )

    d1 = datetime.datetime.now()
    d2 = d1 + datetime.timedelta(hours=1)

    user_1 = storage.create_user("testUser", b"testSecret", ColorData(0, 0, 0))
    storage.create_session_for_user(
        user_id=user_1,
        session_key="asdfwargle",
        creation_date=d1,
        expiry_date=d2,
    )

    session_data = storage.get_session_by_key("asdfwargle")
    assert session_data is not None
    assert session_data.user_id == user_1
    assert session_data.creation_date == d1
    assert session_data.expiry_date == d2

    # Fetch non-existant fails
    session_data = storage.get_session_by_key("asdfwargle5")
    assert session_data is None


def test_delete_session_by_date() -> None:
    storage = Storage(":memory:")

    d1 = datetime.datetime.now()
    d2 = d1 + datetime.timedelta(hours=1)
    d3 = d1 + datetime.timedelta(hours=2)

    user_1 = storage.create_user("testUser", b"testSecret", ColorData(0, 0, 0))
    storage.create_session_for_user(
        user_id=user_1,
        session_key="asdfwargle1",
        creation_date=d1,
        expiry_date=d1,
    )
    storage.create_session_for_user(
        user_id=user_1,
        session_key="asdfwargle2",
        creation_date=d1,
        expiry_date=d3,
    )

    storage.clear_sessions_by_date(d2)
    # Should delete d1 but not d3

    assert storage.get_session_by_key("asdfwargle1") is None
    assert storage.get_session_by_key("asdfwargle2") is not None

    storage.delete_session_by_key("asdfwargle2")
    assert storage.get_session_by_key("asdfwargle2") is None


def test_parse_hex() -> None:
    assert ColorData.from_hex("#010203") == ColorData(r=1, g=2, b=3)
    assert ColorData.from_hex("#111213") == ColorData(r=17, g=18, b=19)
    assert ColorData(r=17, g=18, b=19).hex == "#111213"
    assert ColorData(r=1, g=2, b=3).hex == "#010203"
