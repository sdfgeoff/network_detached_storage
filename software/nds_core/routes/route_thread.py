from .registry import register_route, RouteDict, RequestContext
from ..webserver import HTTPResponse
from ..storage import Thread

from .file_utils import openFragment, wrapContent

routes: RouteDict = {}


def format_thread(context: RequestContext, thread: Thread) -> bytes:
    post = openFragment("post.html")
    posts = "\n".join([post.format(POST=d) for d in thread.posts])

    thread_template = openFragment("thread.html")
    thread_str = thread_template.format(POSTS=posts)

    return wrapContent(context.session, context.request, thread.name, thread_str)


@register_route(routes, r"/threads/\d/")
def request_thread(context: RequestContext) -> HTTPResponse:
    thread = context.storage.thread_by_id(0)  # TODO: parse thread ID
    return HTTPResponse(status_code=200, data=format_thread(context, thread))
