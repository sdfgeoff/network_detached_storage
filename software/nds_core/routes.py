from .webserver import HTTPRequest, HTTPResponse
from . import log

def handle_route_request(page_request: HTTPRequest) -> HTTPResponse:
    '''Converts the HTTP page request into a page string'''
    page_request_str = page_request.url
    return HTTPResponse(
        status_code=200,
        data=b"HELLO!"
    )