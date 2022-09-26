import urllib
import datetime
from typing import List
from .registry import register_route, RouteDict, RequestContext
from ..webserver import HTTPResponse
from ..storage import ThreadData, PostData, UserData

from .file_utils import openFragment, wrapContent

routes: RouteDict = {}


def format_thread(
    context: RequestContext,
    thread: ThreadData,
    posts: List[PostData],
    users: List[UserData],
) -> bytes:
    post = openFragment("post.html")
    post_str = "\n".join(
        [
            post.format(POST=d, USER=next(u for u in users if u.user_id == d.user_id))
            for d in posts
        ]
    )

    thread_template = openFragment("thread.html")

    if context.session is None:
        reply = openFragment("signInButton.html")
    else:
        reply = openFragment("newPost.html").format(
            THREAD=thread,
            USER=context.storage.query_users_by_ids([context.session.user_id])[0],
        )

    thread_str = thread_template.format(POSTS=post_str, REPLY=reply)

    return wrapContent(context.session, context.request, thread.title, thread_str)


@register_route(routes, r"/threads/(?P<thread_id>\d+)/")
def request_thread(context: RequestContext) -> HTTPResponse:
    thread_id = int(context.url_match.groupdict()["thread_id"])

    thread_data = context.storage.query_thread_by_id(thread_id)
    if thread_data is None:
        return HTTPResponse(
            status_code=302,
            headers=[(b"Location", b"404.html")],
        )

    posts = context.storage.query_posts_by_thread_id(thread_id, 100, 0)
    user_ids = [p.user_id for p in posts]
    users = context.storage.query_users_by_ids(user_ids)

    return HTTPResponse(
        status_code=200, data=format_thread(context, thread_data, posts, users)
    )


@register_route(routes, r"/threads/(?P<thread_id>\d+)/reply.html")
def reply_to_thread(context: RequestContext) -> HTTPResponse:
    if context.session is None:
        return HTTPResponse(status_code=403)

    thread_id = int(context.url_match.groupdict()["thread_id"])
    reply_data = urllib.parse.parse_qs(context.request.content)
    reply_content = next(iter(reply_data.get(b"reply_content", [])), None)

    if reply_content is None:
        return HTTPResponse(status_code=400, data=b"Missing content")

    context.storage.create_post_in_thread(
        thread_id=thread_id,
        user_id=context.session.user_id,
        post_date=datetime.datetime.now(),
        post_content=reply_content.decode("utf-8"),
    )

    return HTTPResponse(
        status_code=302,
        data=b"Created Thread",
        headers=[(b"Location", f"/threads/{thread_id}/".encode("utf-8"))],
    )


@register_route(routes, r"/threads/new.html")
def new_thread_editor(context: RequestContext) -> HTTPResponse:
    if context.session is None:
        return HTTPResponse(status_code=403)

    user_data = context.storage.query_users_by_ids([context.session.user_id])[0]
    return HTTPResponse(
        status_code=200,
        data=wrapContent(
            context.session,
            context.request,
            "CREATE THREAD",
            openFragment("newThread.html").format(USER=user_data),
        ),
    )


@register_route(routes, r"/threads/create.html")
def create_thread(context: RequestContext) -> HTTPResponse:
    if context.session is None:
        return HTTPResponse(status_code=403)
    thread_data = urllib.parse.parse_qs(context.request.content)

    thread_name = next(iter(thread_data.get(b"thread_name", [])), None)
    thread_content = next(iter(thread_data.get(b"thread_content", [])), None)

    if thread_name is None or thread_content is None:
        return HTTPResponse(status_code=400, data=b"Missing thread title or content")

    thread_id = context.storage.create_thread(
        post_date=datetime.datetime.now(),
        user_id=context.session.user_id,
        title=thread_name.decode("utf-8"),
        initial_post_content=thread_content.decode("utf-8"),
    )

    return HTTPResponse(
        status_code=302,
        data=b"Created Thread",
        headers=[(b"Location", f"/threads/{thread_id}/".encode("utf-8"))],
    )
