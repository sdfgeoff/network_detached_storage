import os
from .webserver import HTTPRequest, HTTPResponse

from . import log

STATIC_DIR = "nds_core/static"

def handle_route_request(page_request: HTTPRequest) -> HTTPResponse:
    '''Converts the HTTP page request into a page string'''
    page_request_str = page_request.url

    if page_request_str == "/":
        return HTTPResponse(
            status_code=302,
            headers=[
                (b"Location", b"/index.html")
            ]
        )
    

    # Look in static directory
    if page_request_str[1:] in os.listdir(STATIC_DIR):
        return HTTPResponse(
            status_code=200,
            headers=[],
            data=open(os.path.join(STATIC_DIR, page_request_str[1:]), 'rb').read()
        )


    print(page_request_str)
    return HTTPResponse(
        status_code=200,
        data=b"HELLO!"
    )