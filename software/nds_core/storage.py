import sqlite3
import os
from typing import Tuple, List

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


# Actual Classes
class UserData:
    user_name: str
    user_id: int
    secret: str
    def __init__(self, user_name: str, user_id: int, secret: str):
        self.user_name = user_name
        self.user_id = user_id
        self.secret = secret


class UserNameAlreadyExists(Exception):
    user_name: str
    def __init__(self, user_name: str):
        self.user_name = user_name


class Storage:
    connection: sqlite3.Connection

    def __init__(self, path: str):
        log.info("opening_db", {"path": path})
        
        self.connection = sqlite3.connect(path)
        _ensure_db_up_to_date(self.connection)
        

    def create_user(self, user_name: str, secret: str) -> int:
        cur = self.connection.cursor()
        try:
            cur.execute(
                """
                INSERT INTO 
                    user (user_name, secret) 
                VALUES 
                    (:user_name, :secret)
                RETURNING user_id
                """,
                {"user_name": user_name, "secret": secret}
            )
        except sqlite3.IntegrityError as err:
            if err.args[0] == 'UNIQUE constraint failed: user.user_name':
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
                user_name, user_id, secret
            FROM 
                user
            WHERE
                user_id IN ({})
            """.format(("?,"*len(user_ids))[:-1]),
            user_ids
        )
        rows = cur.fetchall()

        return [
            UserData(
                user_name=r[0],
                user_id=r[1],
                secret=r[2],
            ) for r in rows
        ]

    def update_user(self, user_data: UserData) -> None:
        cur = self.connection.cursor()
        try:
            cur.execute(
                """
                UPDATE 
                    user
                SET
                    user_name=:user_name,
                    secret=:secret
                WHERE 
                    user_id=:user_id
                """,
                {"user_name": user_data.user_name, "secret": user_data.secret, "user_id": user_data.user_id}
            )
        except sqlite3.IntegrityError as err:
            if err.args[0] == 'UNIQUE constraint failed: user.user_name':
                raise UserNameAlreadyExists(user_name=user_data.user_name) from err
            raise err from err
            

        self.connection.commit()
            

    def thread_by_id(self, thead_id: int) -> Thread:
        # TODO
        return Thread(
            posts=[
                Post(
                    user=User(name="sdfgeoff", color=(0,255,0)),
                    post_date="2022-09-12 07:25:22",
                    content="<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur feugiat ex augue, at mattis arcu placerat non. Quisque vel volutpat tortor, convallis convallis est. Fusce consequat velit eget volutpat sodales. Maecenas vitae est sit amet orci pharetra dignissim eu varius dui. Curabitur finibus tortor et neque pellentesque, vel elementum felis pellentesque. Integer eu nisl lobortis nulla scelerisque blandit vitae vitae felis. Vivamus lobortis feugiat ultrices. Nullam orci nisl, gravida dapibus est in, egestas finibus nunc. Sed vulputate elementum diam, et finibus metus vestibulum commodo. Cras ipsum nisl, semper eu consectetur eget, tincidunt vel dolor.</p>"
                ),
                Post(
                    user=User(name="Arg", color=(255,255,0)),
                    post_date="2022-09-12 07:34:55",
                    content="<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur feugiat ex augue, at mattis arcu placerat non. Quisque vel volutpat tortor, convallis convallis est. Fusce consequat velit eget volutpat sodales. Maecenas vitae est sit amet orci pharetra dignissim eu varius dui. Curabitur finibus tortor et neque pellentesque, vel elementum felis pellentesque. Integer eu nisl lobortis nulla scelerisque blandit vitae vitae felis. Vivamus lobortis feugiat ultrices. Nullam orci nisl, gravida dapibus est in, egestas finibus nunc. Sed vulputate elementum diam, et finibus metus vestibulum commodo. Cras ipsum nisl, semper eu consectetur eget, tincidunt vel dolor.</p>"
                )
            ],
            name="Test Thread"
        )



def _get_db_version(connection: sqlite3.Connection) -> int:
    """ Check what version the DB is """
    cur = connection.cursor()
    try:
        cur.execute("""
            SELECT 
                value
            FROM
                metadata
            WHERE 
                setting='db_version'
        """)
    except sqlite3.OperationalError:
        return 0

    res = cur.fetchone()
    return int(res[0])


def _create_v1_db(connection: sqlite3.Connection) -> None:
    cur = connection.cursor()

    cur.execute(
        "CREATE TABLE metadata (setting TEXT, value TEXT)"
    )
    cur.execute("""
        INSERT INTO 
            metadata 
        VALUES 
            ('db_version', :version)
    """, {"version": 1}
    )
    connection.commit()


def _upgrade_v1_to_v2(connection: sqlite3.Connection) -> None:
    cur = connection.cursor()
    cur.executescript("""
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
    """)

    cur.execute("""
        UPDATE
            metadata 
        SET 
            value=:db_version 
        WHERE 
            setting='db_version'
    """, {"db_version": 2})
    connection.commit()



def _ensure_db_up_to_date(connection: sqlite3.Connection) -> None:
    current_version = _get_db_version(connection)
        
    versions = [
        _create_v1_db,
        _upgrade_v1_to_v2
    ]

    while current_version < len(versions):
        upgrade_function = versions[current_version]
        log.info("upgrading_db", {"existing_version": current_version, "function":upgrade_function.__name__})

        upgrade_function(connection)
        current_version = _get_db_version(connection)

    log.info("db_up_to_date", {"current_version": current_version})
