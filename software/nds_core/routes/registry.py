import re
from typing import Dict, Optional, Callable, Pattern
from ..storage import Storage, SessionData
from ..webserver import HTTPRequest, HTTPResponse
from .. import log


class RequestContext:
    storage: Storage
    request: HTTPRequest
    session: Optional[SessionData]

    def __init__(
        self, storage: Storage, request: HTTPRequest, session: Optional[SessionData]
    ):
        self.storage = storage
        self.request = request
        self.session = session


RouteHandler = Callable[[RequestContext], HTTPResponse]
RouteDict = Dict[Pattern[str], RouteHandler]


def register_route(
    route_dict: RouteDict, regex: str
) -> Callable[[RouteHandler], RouteHandler]:
    def register(function: RouteHandler) -> RouteHandler:
        log.debug("registering_route", {"route": regex, "handler": function.__name__})
        route_dict[re.compile(regex)] = function
        return function

    return register
