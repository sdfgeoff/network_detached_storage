import os
from .webserver import HTTPRequest, HTTPResponse
from typing import Tuple

from . import log
from .storage import Thread, User, Post, Storage

NAME = "NDS Core 12"
FRAGMENT_DIR = "nds_core/fragments"
STATIC_DIR = "nds_core/static"


def openStatic(path: str) -> bytes:
    return open(
        os.path.join(STATIC_DIR, path), 'rb'
    ).read()

def openFragment(path: str) -> str:
    return open(
        os.path.join(FRAGMENT_DIR, path), 'r', encoding='utf-8'
    ).read()


def wrapContent(title: str, content: str) -> bytes:
    template = openFragment('ROOT.html')
    return template.format(CONTENT=content, TITLE=NAME + ": " + title).encode('utf-8')


def format_thread(thread: Thread) -> bytes:
    post = openFragment('post.html')
    posts = '\n'.join([post.format(POST=d) for d in thread.posts])

    thread_template = openFragment('thread.html')
    thread_str = thread_template.format(POSTS=posts)

    return wrapContent(thread.name, thread_str)



def handle_route_request(storage: Storage, page_request: HTTPRequest) -> HTTPResponse:
    '''Converts the HTTP page request into a page string'''
    page_request_str = page_request.url

    if page_request_str == "/":
        return HTTPResponse(
            status_code=302,
            headers=[
                (b"Location", b"/index.html")
            ]
        )
    if page_request_str == "/404.html":
        return HTTPResponse(
            status_code=404,
            data=wrapContent("RESOURCE MISSING", openFragment('404.html'))
        )
    if page_request_str == "/403.html":
        return HTTPResponse(
            status_code=404,
            data=wrapContent("ACCESS DENITED", openFragment('403.html'))
        )
    if page_request_str == "/500.html":
        return HTTPResponse(
            status_code=500,
            data=wrapContent("INTERNAL FAULT", openFragment('500.html'))
        )
    if page_request_str.startswith("/threads/"):
        thread = storage.thread_by_id(0) # TODO: parse thread ID
        return HTTPResponse(
            status_code=200,
            data=format_thread(thread)  
        )


    if page_request_str == "/debug":
        a = 1 / 0
    

    # Look in static directory last
    if page_request_str[1:] in os.listdir(STATIC_DIR):
        return HTTPResponse(
            status_code=200,
            headers=[],
            data=openStatic(page_request_str[1:])
        )

    return HTTPResponse(
        status_code=302,
        headers=[
                (b"Location", b"/404.html")
            ]
    )