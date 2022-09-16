from .registry import RequestContext, register_route, RouteDict
from .file_utils import wrapContent, openFragment
from nds_core.webserver import HTTPResponse


routes: RouteDict = {}


@register_route(routes, r"/")
def handler_root(context: RequestContext) -> HTTPResponse:
    return HTTPResponse(status_code=302, headers=[(b"Location", b"/index.html")])


@register_route(routes, r"/404.html")
def handler_404(context: RequestContext) -> HTTPResponse:
    return HTTPResponse(
        status_code=404,
        data=wrapContent(
            context.session,
            context.request,
            "RESOURCE MISSING",
            openFragment("404.html"),
        ),
    )


@register_route(routes, r"/403.html")
def handler_403(context: RequestContext) -> HTTPResponse:
    return HTTPResponse(
        status_code=403,
        data=wrapContent(
            context.session, context.request, "ACCESS DENITED", openFragment("403.html")
        ),
    )


@register_route(routes, r"/500.html")
def handler_500(context: RequestContext) -> HTTPResponse:
    return HTTPResponse(
        status_code=500,
        data=wrapContent(
            context.session, context.request, "INTERNAL FAULT", openFragment("500.html")
        ),
    )
