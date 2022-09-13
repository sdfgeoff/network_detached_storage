import os
import urllib.parse
from .webserver import HTTPRequest, HTTPResponse
from typing import Tuple

from . import log
from .storage import Thread, User, Post, Storage
from .auth import encode_password, validate_password_v1

NAME = "NDS Core 12"
FRAGMENT_DIR = "nds_core/fragments"
STATIC_DIR = "nds_core/static"


def openStatic(path: str) -> bytes:
    return open(os.path.join(STATIC_DIR, path), "rb").read()


def openFragment(path: str) -> str:
    return open(os.path.join(FRAGMENT_DIR, path), "r", encoding="utf-8").read()


def wrapContent(request: HTTPRequest, title: str, content: str) -> bytes:
    template = openFragment("ROOT.html")
    settings_button = openFragment("signInButton.html")
    return template.format(
        CONTENT=content, TITLE=NAME + ": " + title, SETTINGS_BUTTON=settings_button
    ).encode("utf-8")


def format_thread(request: HTTPRequest, thread: Thread) -> bytes:
    post = openFragment("post.html")
    posts = "\n".join([post.format(POST=d) for d in thread.posts])

    thread_template = openFragment("thread.html")
    thread_str = thread_template.format(POSTS=posts)

    return wrapContent(request, thread.name, thread_str)


def create_user(storage: Storage, page_request: HTTPRequest) -> HTTPResponse:
    user_data = urllib.parse.parse_qs(page_request.content)
    user_name = next(iter(user_data.get(b"user_name", [])), None)
    password = next(iter(user_data.get(b"password", [])), None)
    if user_name is None or password is None or len(password) < 1:
        return HTTPResponse(status_code=400, data=b"missing username or password")

    secret_bundle = encode_password(password)
    user_id = storage.create_user(
        user_name=user_name.decode("utf-8"), secret=secret_bundle
    )

    return HTTPResponse(status_code=200, data=f"Created User {user_id}".encode("utf-8"))


def login_user(storage: Storage, page_request: HTTPRequest) -> HTTPResponse:
    user_data_str = urllib.parse.parse_qs(page_request.content)
    user_name = next(iter(user_data_str.get(b"user_name", [])), None)
    password = next(iter(user_data_str.get(b"password", [])), None)
    if user_name is None or password is None or len(password) < 1:
        return HTTPResponse(status_code=400, data=b"missing username or password")

    user_data = storage.query_user_by_user_name(user_name.decode("utf-8"))
    if user_data is None:
        # No User with that name: 403
        return HTTPResponse(status_code=302, headers=[(b"Location", b"/403.html")])

    else:
        password_is_valid = validate_password_v1(password, user_data.secret)
        if not password_is_valid:
            return HTTPResponse(status_code=302, headers=[(b"Location", b"/403.html")])

        return HTTPResponse(
            status_code=200, data=b"SUCCESS! You typed your password right!"
        )


def handle_route_request(storage: Storage, page_request: HTTPRequest) -> HTTPResponse:
    """Converts the HTTP page request into a page string"""
    page_request_str = page_request.url

    if page_request_str == "/":
        return HTTPResponse(status_code=302, headers=[(b"Location", b"/index.html")])

    # Status Pages
    if page_request_str == "/404.html":
        return HTTPResponse(
            status_code=404,
            data=wrapContent(
                page_request, "RESOURCE MISSING", openFragment("404.html")
            ),
        )
    if page_request_str == "/403.html":
        return HTTPResponse(
            status_code=404,
            data=wrapContent(page_request, "ACCESS DENITED", openFragment("403.html")),
        )
    if page_request_str == "/500.html":
        return HTTPResponse(
            status_code=500,
            data=wrapContent(page_request, "INTERNAL FAULT", openFragment("500.html")),
        )

    # Dynamic Routes
    if page_request_str == "/index.html":
        return HTTPResponse(
            status_code=200,
            data=wrapContent(page_request, "Home", "Construction in progress"),
        )
    if page_request_str.startswith("/threads/"):
        thread = storage.thread_by_id(0)  # TODO: parse thread ID
        return HTTPResponse(status_code=200, data=format_thread(page_request, thread))
    if page_request_str == "/login.html":
        return HTTPResponse(
            status_code=200,
            data=wrapContent(page_request, "LOG IN", openFragment("loginDialog.html")),
        )
    if page_request.method == "POST" and page_request_str == "/user/create.html":
        return create_user(storage, page_request)
    if page_request.method == "POST" and page_request_str == "/user/login.html":
        return login_user(storage, page_request)

    if page_request_str == "/debug":
        a = 1 / 0

    # Look in static directory last
    if page_request_str[1:] in os.listdir(STATIC_DIR):
        return HTTPResponse(
            status_code=200,
            headers=[(b"Cache-Control", b"max-age=3600")],
            data=openStatic(page_request_str[1:]),
        )

    return HTTPResponse(status_code=302, headers=[(b"Location", b"/404.html")])
