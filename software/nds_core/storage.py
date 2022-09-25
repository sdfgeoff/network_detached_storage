import sqlite3
import json
from typing import Tuple, List, Optional
from datetime import datetime
from dataclasses import dataclass


from . import log


# Temporary Classes
class User:
    name: str
    color: Tuple[int, int, int]

    def __init__(self, name: str, color: Tuple[int, int, int]):
        self.name = name
        self.color = color


class Post:
    content: str
    user: User
    post_date: str

    def __init__(self, user: User, post_date: str, content: str):
        self.user = user
        self.post_date = post_date
        self.content = content


class Thread:
    posts: List[Post]
    name: str

    def __init__(self, posts: List[Post], name: str):
        self.posts = posts
        self.name = name


@dataclass
class ColorData:
    r: int
    g: int
    b: int

    @classmethod
    def from_hex(cls, hex: str) -> "ColorData":
        """Converts a HEX code into RGB or HSL.
        Args:
            hx (str): Takes both short as well as long HEX codes.
            hsl (bool): Converts the given HEX code into HSL value if True.
        Return:
            Tuple of length 3 consisting of either int or float values.
        Raise:
            ValueError: If given value is not a valid HEX code."""
        return cls(r=int(hex[1:3], 16), g=int(hex[3:5], 16), b=int(hex[5:7], 16))

    @property
    def hex(self) -> str:
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"


@dataclass
class UserData:
    user_name: str
    user_id: int
    secret: bytes
    color: ColorData


@dataclass
class SessionData:
    user_id: int
    session_key: str
    creation_date: datetime
    expiry_date: datetime


class UserNameAlreadyExists(Exception):
    user_name: str

    def __init__(self, user_name: str):
        self.user_name = user_name


class UserIDDoesNotExist(Exception):
    user_id: int

    def __init__(self, user_id: int):
        self.user_id = user_id


class Storage:
    connection: sqlite3.Connection

    def __init__(self, path: str):
        log.info("opening_db", {"path": path})

        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA foreign_keys = ON;")
        _ensure_db_up_to_date(self.connection)

    def create_user(self, user_name: str, secret: bytes, color: ColorData) -> int:
        cur = self.connection.cursor()
        try:
            cur.execute(
                """
                INSERT INTO
                    user (user_name, secret, color)
                VALUES
                    (:user_name, :secret, :color)
                RETURNING user_id
                """,
                {
                    "user_name": user_name,
                    "secret": secret,
                    "color": serialize_color(color),
                },
            )
        except sqlite3.IntegrityError as err:
            if err.args[0] == "UNIQUE constraint failed: user.user_name":
                raise UserNameAlreadyExists(user_name=user_name)
            raise err from err
        user_id = int(cur.fetchone()[0])
        self.connection.commit()
        return user_id

    def query_users_by_ids(self, user_ids: List[int]) -> List[UserData]:
        cur = self.connection.cursor()
        cur.execute(
            """
            SELECT
                user_name, user_id, secret, color
            FROM
                user
            WHERE
                user_id IN ({})
            """.format(
                ("?," * len(user_ids))[:-1]
            ),
            user_ids,
        )
        rows = cur.fetchall()

        return [
            UserData(
                user_name=row[0],
                user_id=row[1],
                secret=row[2],
                color=parse_color(row[3]),
            )
            for row in rows
        ]

    def query_user_by_user_name(self, user_name: str) -> Optional[UserData]:
        cur = self.connection.cursor()
        cur.execute(
            """
            SELECT
                user_name, user_id, secret, color
            FROM
                user
            WHERE
                user_name IS :user_name
            """,
            {"user_name": user_name},
        )
        row = cur.fetchone()

        if row is None:
            return None

        return UserData(
            user_name=row[0], user_id=row[1], secret=row[2], color=parse_color(row[3])
        )

    def update_user(self, user_data: UserData) -> None:
        cur = self.connection.cursor()
        try:
            cur.execute(
                """
                UPDATE
                    user
                SET
                    user_name=:user_name,
                    secret=:secret,
                    color=:color
                WHERE
                    user_id=:user_id
                """,
                {
                    "user_name": user_data.user_name,
                    "secret": user_data.secret,
                    "user_id": user_data.user_id,
                    "color": serialize_color(user_data.color),
                },
            )
        except sqlite3.IntegrityError as err:
            if err.args[0] == "UNIQUE constraint failed: user.user_name":
                raise UserNameAlreadyExists(user_name=user_data.user_name) from err
            raise err from err

        self.connection.commit()

    def create_session_for_user(
        self,
        user_id: int,
        session_key: str,
        creation_date: datetime,
        expiry_date: datetime,
    ) -> None:
        cur = self.connection.cursor()
        try:
            cur.execute(
                """
                INSERT INTO
                    session (user_id, session_key, creation_date, expiry_date)
                VALUES
                    (:user_id, :session_key, :creation_date, :expiry_date)
                """,
                {
                    "user_id": user_id,
                    "session_key": session_key,
                    "creation_date": creation_date.isoformat(),
                    "expiry_date": expiry_date.isoformat(),
                },
            )
            self.connection.commit()
        except sqlite3.IntegrityError as err:
            if err.args[0] == "FOREIGN KEY constraint failed":
                raise UserIDDoesNotExist(user_id=user_id)
            raise err from err

    def get_session_by_key(self, session_key: str) -> Optional[SessionData]:
        cur = self.connection.cursor()
        cur.execute(
            """
            SELECT
                user_id, creation_date, expiry_date
            FROM
                session
            WHERE
                session_key=:session_key;
            """,
            {"session_key": session_key},
        )
        data = cur.fetchone()
        if data is None:
            return None
        return SessionData(
            user_id=data[0],
            session_key=session_key,
            creation_date=datetime.fromisoformat(data[1]),
            expiry_date=datetime.fromisoformat(data[2]),
        )

    def delete_session_by_key(self, session_key: str) -> None:
        cur = self.connection.cursor()
        cur.execute(
            """
            DELETE
            FROM
                session
            WHERE
                session_key=:session_key;
            """,
            {"session_key": session_key},
        )
        self.connection.commit()

    def clear_sessions_by_date(self, expire_before: datetime) -> None:
        cur = self.connection.cursor()
        # ISO format dates string sort nicely....
        cur.execute(
            """
            DELETE
            FROM
                session
            WHERE
                expiry_date < :expire_before;
            """,
            {"expire_before": expire_before.isoformat()},
        )
        self.connection.commit()

    def thread_by_id(self, thead_id: int) -> Thread:
        # TODO
        return Thread(
            posts=[
                Post(
                    user=User(name="sdfgeoff", color=(0, 255, 0)),
                    post_date="2022-09-12 07:25:22",
                    content="<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur feugiat ex augue, at mattis arcu placerat non. Quisque vel volutpat tortor, convallis convallis est. Fusce consequat velit eget volutpat sodales. Maecenas vitae est sit amet orci pharetra dignissim eu varius dui. Curabitur finibus tortor et neque pellentesque, vel elementum felis pellentesque. Integer eu nisl lobortis nulla scelerisque blandit vitae vitae felis. Vivamus lobortis feugiat ultrices. Nullam orci nisl, gravida dapibus est in, egestas finibus nunc. Sed vulputate elementum diam, et finibus metus vestibulum commodo. Cras ipsum nisl, semper eu consectetur eget, tincidunt vel dolor.</p>",  # noqa
                ),
                Post(
                    user=User(name="Arg", color=(255, 255, 0)),
                    post_date="2022-09-12 07:34:55",
                    content="<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur feugiat ex augue, at mattis arcu placerat non. Quisque vel volutpat tortor, convallis convallis est. Fusce consequat velit eget volutpat sodales. Maecenas vitae est sit amet orci pharetra dignissim eu varius dui. Curabitur finibus tortor et neque pellentesque, vel elementum felis pellentesque. Integer eu nisl lobortis nulla scelerisque blandit vitae vitae felis. Vivamus lobortis feugiat ultrices. Nullam orci nisl, gravida dapibus est in, egestas finibus nunc. Sed vulputate elementum diam, et finibus metus vestibulum commodo. Cras ipsum nisl, semper eu consectetur eget, tincidunt vel dolor.</p>",  # noqa
                ),
            ],
            name="Test Thread",
        )


def parse_color(color: Optional[str]) -> ColorData:
    if color is not None:
        raw = json.loads(color)
        return ColorData(r=raw.get("r", 0), g=raw.get("g", 0), b=raw.get("b", 0))
    return ColorData(r=0, g=0, b=0)


def serialize_color(color: ColorData) -> str:
    return json.dumps(
        {
            "r": color.r,
            "g": color.g,
            "b": color.b,
        }
    )


def _get_db_version(connection: sqlite3.Connection) -> int:
    """Check what version the DB is"""
    cur = connection.cursor()
    try:
        cur.execute(
            """
            SELECT
                value
            FROM
                metadata
            WHERE
                setting='db_version'
        """
        )
    except sqlite3.OperationalError:
        return 0

    res = cur.fetchone()
    return int(res[0])


def _create_v1_db(connection: sqlite3.Connection) -> None:
    cur = connection.cursor()

    cur.execute("CREATE TABLE metadata (setting TEXT, value TEXT)")
    cur.execute(
        """
        INSERT INTO
            metadata
        VALUES
            ('db_version', :version)
    """,
        {"version": 1},
    )
    connection.commit()


def _upgrade_v1_to_v2(connection: sqlite3.Connection) -> None:
    cur = connection.cursor()
    cur.executescript(
        """
        BEGIN;
        CREATE TABLE user (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL UNIQUE,
            secret BLOB
        );
        CREATE TABLE post (
            post_id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            post_date TEXT,
            edit_date TEXT
        );
        CREATE TABLE post_user (
            user_id INTEGER KEY,
            post_id INTEGER KEY,
            FOREIGN KEY(user_id) REFERENCES user(user_id),
            FOREIGN KEY(post_id) REFERENCES post(post_id)
        );
        CREATE TABLE thread (
            thread_id INTEGER PRIMARY KEY,
            title TEXT NOTE NULL
        );
        CREATE TABLE post_thread (
            post_id INTEGER KEY,
            thread_id INTEGER KEY,
            ordering INTEGER KEY,
            FOREIGN KEY(post_id) REFERENCES post(post_id),
            FOREIGN KEY(thread_id) REFERENCES thread(thread_id)
        );
        CREATE TABLE file (
            file_id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT,
            upload_date TEXT
        );
        CREATE TABLE file_user (
            user_id INTEGER KEY,
            file_id INTEGER KEY,
            FOREIGN KEY(user_id) REFERENCES user(user_id),
            FOREIGN KEY(file_id) REFERENCES file(file_id)
        );
        COMMIT;
    """
    )

    cur.execute(
        """
        UPDATE
            metadata
        SET
            value=:db_version
        WHERE
            setting='db_version'
    """,
        {"db_version": 2},
    )
    connection.commit()


def _upgrade_v2_to_v3(connection: sqlite3.Connection) -> None:
    cur = connection.cursor()
    cur.executescript(
        """
        BEGIN;
        CREATE TABLE session (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_key TEXT NOT NULL,
            creation_date TEXT,
            expiry_date TEXT,
            FOREIGN KEY(user_id) REFERENCES user(user_id)
        );

        CREATE INDEX
            session_key_index
        ON
            session(session_key);

        CREATE INDEX
            user_name_index
        ON
            user(user_name);

        COMMIT;
    """
    )

    cur.execute(
        """
        UPDATE
            metadata
        SET
            value=:db_version
        WHERE
            setting='db_version'
    """,
        {"db_version": 3},
    )
    connection.commit()


def _upgrade_v3_to_v4(connection: sqlite3.Connection) -> None:
    cur = connection.cursor()
    cur.executescript(
        """
        BEGIN;
        ALTER TABLE
            user
        ADD
            color TEXT;
        COMMIT;
    """
    )

    cur.execute(
        """
        UPDATE
            metadata
        SET
            value=:db_version
        WHERE
            setting='db_version'
    """,
        {"db_version": 4},
    )
    connection.commit()


def _ensure_db_up_to_date(connection: sqlite3.Connection) -> None:
    current_version = _get_db_version(connection)

    versions = [_create_v1_db, _upgrade_v1_to_v2, _upgrade_v2_to_v3, _upgrade_v3_to_v4]

    while current_version < len(versions):
        upgrade_function = versions[current_version]
        log.info(
            "upgrading_db",
            {
                "existing_version": current_version,
                "function": upgrade_function.__name__,
            },
        )

        upgrade_function(connection)
        current_version = _get_db_version(connection)

    log.info("db_up_to_date", {"current_version": current_version})
