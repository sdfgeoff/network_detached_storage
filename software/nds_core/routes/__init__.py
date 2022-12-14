import os
from ..webserver import HTTPRequest, HTTPResponse

import re

from .file_utils import openStatic, STATIC_DIR
from ..storage import Storage
from ..session import get_session_data
from . import route_simple
from . import route_user
from . import route_thread
from . import route_index
from .registry import RouteDict, RequestContext


ROUTES: RouteDict = {
    **route_simple.routes,
    **route_user.routes,
    **route_thread.routes,
    **route_index.routes,
}


def handle_route_request(storage: Storage, page_request: HTTPRequest) -> HTTPResponse:
    """Converts the HTTP page request into a page string"""

    session_data = get_session_data(storage, page_request)

    page_request_str = page_request.url
    for route in ROUTES:
        reg_match = re.fullmatch(route, page_request.url)
        if reg_match is not None:
            context = RequestContext(storage, page_request, session_data, reg_match)

            return ROUTES[route](context)

    if page_request_str == "/debug":
        a = 1 / 0  # noqa

    # Look in static directory last
    if page_request_str[1:] in os.listdir(STATIC_DIR):
        return HTTPResponse(
            status_code=200,
            headers=[(b"Cache-Control", b"max-age=3600")],
            data=openStatic(page_request_str[1:]),
        )

    return HTTPResponse(status_code=302, headers=[(b"Location", b"/404.html")])
