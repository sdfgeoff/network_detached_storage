import os
from typing import Optional
from nds_core.webserver import HTTPRequest
from ..storage import SessionData

NAME = "NDS Core 12"
FRAGMENT_DIR = "nds_core/routes/fragments"
STATIC_DIR = "nds_core/routes/static"


def openStatic(path: str) -> bytes:
    return open(os.path.join(STATIC_DIR, path), "rb").read()


def openFragment(path: str) -> str:
    return open(os.path.join(FRAGMENT_DIR, path), "r", encoding="utf-8").read()


def wrapContent(
    session_data: Optional[SessionData], request: HTTPRequest, title: str, content: str
) -> bytes:
    template = openFragment("ROOT.html")
    settings_button = (
        openFragment("signInButton.html")
        if session_data is None
        else openFragment("userProfileButton.html")
    )

    return template.format(
        CONTENT=content, TITLE=NAME + ": " + title, SETTINGS_BUTTON=settings_button
    ).encode("utf-8")
