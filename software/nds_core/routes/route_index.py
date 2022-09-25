from .registry import register_route, RouteDict, RequestContext
from ..webserver import HTTPResponse

from .file_utils import openFragment, wrapContent

routes: RouteDict = {}


@register_route(routes, r"/index.html")
def request_thread_index(context: RequestContext) -> HTTPResponse:
    new_thread_button = (
        openFragment("newThreadButton.html") if context.session is not None else ""
    )

    thread_index_fragment = openFragment("threadIndex.html")
    thread_index_fragment = thread_index_fragment.format(
        THREAD_OVERVIEW="Construction in Progress",
        NEW_THREAD_AREA=new_thread_button,
    )

    return HTTPResponse(
        status_code=200,
        data=wrapContent(
            context.session, context.request, "Home", thread_index_fragment
        ),
    )
