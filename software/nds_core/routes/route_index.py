from .registry import register_route, RouteDict, RequestContext
from ..webserver import HTTPResponse

from .file_utils import openFragment, wrapContent

routes: RouteDict = {}


@register_route(routes, r"/index.html")
def request_thread_index(context: RequestContext) -> HTTPResponse:
    new_thread_button = (
        openFragment("newThreadButton.html") if context.session is not None else ""
    )

    threads = context.storage.query_threads(10, 0)
    user_ids = [t.user_id for t in threads]
    user_data = context.storage.query_users_by_ids(user_ids)

    thread_summary_fragment = openFragment("threadSummary.html")
    thread_summary_str = "\n".join(
        [
            thread_summary_fragment.format(
                THREAD=t, USER=next(u for u in user_data if u.user_id == t.user_id)
            )
            for t in threads
        ]
    )

    thread_index_fragment = openFragment("threadIndex.html")
    thread_index_fragment = thread_index_fragment.format(
        THREAD_OVERVIEW=thread_summary_str,
        NEW_THREAD_AREA=new_thread_button,
    )

    return HTTPResponse(
        status_code=200,
        data=wrapContent(
            context.session, context.request, "Home", thread_index_fragment
        ),
    )
