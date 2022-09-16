import datetime
import base64
import os

from typing import Tuple, Optional
from .storage import Storage, SessionData
from .webserver import HTTPRequest


def create_session_header(storage: Storage, user_id: int) -> Tuple[bytes, bytes]:
    session_key = base64.b64encode(os.urandom(32)).decode("utf-8")
    storage.create_session_for_user(
        user_id=user_id,
        session_key=session_key,
        creation_date=datetime.datetime.now(),
        expiry_date=datetime.datetime.now() + datetime.timedelta(days=1),
    )
    header = (
        b"Set-Cookie",
        f"nds_core_auth={session_key}; SameSite=strict; Path=/;".encode("utf-8"),
    )
    return header


def get_session_data(
    storage: Storage, page_request: HTTPRequest
) -> Optional[SessionData]:
    cookie_headers = [h[1] for h in page_request.headers if h[0] == b"Cookie"]
    for cookie_str in cookie_headers:
        cookies = cookie_str.split(b";")
        for cookie in cookies:
            key, val = cookie.split(b"=", maxsplit=1)
            if key.strip() == b"nds_core_auth":
                session = storage.get_session_by_key(val.decode("utf-8").strip())
                if session is None or datetime.datetime.now() > session.expiry_date:
                    storage.clear_sessions_by_date(datetime.datetime.now())
                    continue
                else:
                    return session
    return None
