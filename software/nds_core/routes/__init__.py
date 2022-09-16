import os
from ..webserver import HTTPRequest, HTTPResponse
from typing import Optional

import re

from .file_utils import wrapContent, openFragment, openStatic, STATIC_DIR
from ..storage import Thread, Storage, SessionData
from ..session import get_session_data
from . import route_simple
from . import route_user
from .registry import RouteDict, RequestContext


def format_thread(
    session_data: Optional[SessionData], request: HTTPRequest, thread: Thread
) -> bytes:
    post = openFragment("post.html")
    posts = "\n".join([post.format(POST=d) for d in thread.posts])

    thread_template = openFragment("thread.html")
    thread_str = thread_template.format(POSTS=posts)

    return wrapContent(session_data, request, thread.name, thread_str)


ROUTES: RouteDict = {**route_simple.routes, **route_user.routes}


def handle_route_request(storage: Storage, page_request: HTTPRequest) -> HTTPResponse:
    """Converts the HTTP page request into a page string"""

    page_request_str = page_request.url

    session_data = get_session_data(storage, page_request)
    context = RequestContext(storage, page_request, session_data)

    for route in ROUTES:
        if re.fullmatch(route, page_request.url):
            return ROUTES[route](context)

    # Dynamic Routes
    if page_request_str == "/index.html":
        return HTTPResponse(
            status_code=200,
            data=wrapContent(
                session_data, page_request, "Home", "Construction in progress"
            ),
        )
    if page_request_str.startswith("/threads/"):
        thread = storage.thread_by_id(0)  # TODO: parse thread ID
        return HTTPResponse(
            status_code=200, data=format_thread(session_data, page_request, thread)
        )

    if page_request_str == "/debug":
        _a = 1 / 0

    # Look in static directory last
    if page_request_str[1:] in os.listdir(STATIC_DIR):
        return HTTPResponse(
            status_code=200,
            headers=[(b"Cache-Control", b"max-age=3600")],
            data=openStatic(page_request_str[1:]),
        )

    return HTTPResponse(status_code=302, headers=[(b"Location", b"/404.html")])
