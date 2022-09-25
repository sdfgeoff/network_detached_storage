import urllib.parse
import random
from ..webserver import HTTPResponse
from ..auth import encode_password, validate_password_v1
from ..session import create_session_header
from .registry import RouteDict, register_route, RequestContext
from .file_utils import wrapContent, openFragment
from ..storage import ColorData, UserData


routes: RouteDict = {}


@register_route(routes, r"/user/create.html")
def create_user(context: RequestContext) -> HTTPResponse:
    user_data = urllib.parse.parse_qs(context.request.content)
    user_name = next(iter(user_data.get(b"user_name", [])), None)
    password = next(iter(user_data.get(b"password", [])), None)
    if user_name is None or password is None or len(password) < 1:
        return HTTPResponse(status_code=400, data=b"missing username or password")

    color = ColorData(
        r=random.randint(0, 255), g=random.randint(0, 255), b=random.randint(0, 255)
    )

    secret_bundle = encode_password(password)
    user_id = context.storage.create_user(
        user_name=user_name.decode("utf-8"), secret=secret_bundle, color=color
    )

    return HTTPResponse(
        status_code=200,
        data=f"Created User {user_id}".encode("utf-8"),
        headers=[create_session_header(context.storage, user_id)],
    )


@register_route(routes, r"/user/update.html")
def update_user(context: RequestContext) -> HTTPResponse:
    if context.session is None or context.session.user_id is None:
        return HTTPResponse(
            status_code=400,
            data=b"Not signed in!",
        )

    user_id = context.session.user_id
    current_userdata = context.storage.query_users_by_ids([user_id])[0]

    user_data = urllib.parse.parse_qs(context.request.content)
    print(user_data)
    user_name = next(iter(user_data.get(b"user_name", [])), None)
    password = next(iter(user_data.get(b"password", [])), None)
    color = next(iter(user_data.get(b"color", [])), None)

    if user_name is None or user_name == b"":
        # Don't change username
        user_name = current_userdata.user_name.encode("utf-8")

    if password is None or password == b"":
        # Don't change username
        secret_bundle = current_userdata.secret
    else:
        print("Changing Password")
        secret_bundle = encode_password(password)

    if color is None or color == b"":
        colorData = current_userdata.color
    else:
        colorData = ColorData.from_hex(color.decode("utf-8"))

    new_userdata = UserData(
        user_id=user_id,
        user_name=user_name.decode("utf-8"),
        secret=secret_bundle,
        color=colorData,
    )

    context.storage.update_user(new_userdata)

    return HTTPResponse(
        status_code=302,
        data=f"Updated User {user_id}".encode("utf-8"),
        headers=[(b"Location", b"/profile.html")],
    )


@register_route(routes, r"/user/login.html")
def login_user(context: RequestContext) -> HTTPResponse:
    user_data_str = urllib.parse.parse_qs(context.request.content)
    user_name = next(iter(user_data_str.get(b"user_name", [])), None)
    password = next(iter(user_data_str.get(b"password", [])), None)
    if user_name is None or password is None or len(password) < 1:
        return HTTPResponse(status_code=400, data=b"missing username or password")

    user_data = context.storage.query_user_by_user_name(user_name.decode("utf-8"))
    if user_data is None:
        # No User with that name: 403
        return HTTPResponse(status_code=302, headers=[(b"Location", b"/403.html")])

    password_is_valid = validate_password_v1(password, user_data.secret)
    if not password_is_valid:
        return HTTPResponse(status_code=302, headers=[(b"Location", b"/403.html")])

    return HTTPResponse(
        status_code=302,
        data=b"SUCCESS! You typed your password right!",
        headers=[
            create_session_header(context.storage, user_data.user_id),
            (b"Location", b"/index.html"),
        ],
    )


@register_route(routes, r"/user/logout.html")
def logout_user(context: RequestContext) -> HTTPResponse:
    if context.session is not None:
        context.storage.delete_session_by_key(context.session.session_key)

        return HTTPResponse(
            status_code=302,
            data=b"Signed Out",
            headers=[(b"Location", b"/index.html")],
        )
    else:
        return HTTPResponse(
            status_code=400,
            data=b"Not signed in!",
        )


@register_route(routes, r"/login.html")
def login_page(context: RequestContext) -> HTTPResponse:
    return HTTPResponse(
        status_code=200,
        data=wrapContent(
            context.session, context.request, "LOG IN", openFragment("loginDialog.html")
        ),
    )


@register_route(routes, r"/profile.html")
def profile_page(context: RequestContext) -> HTTPResponse:
    if context.session is None:
        return HTTPResponse(
            status_code=302,
            data=b"Not signed in!",
            headers=[(b"Location", b"/403.html")],
        )
    userData = context.storage.query_users_by_ids([context.session.user_id])[0]

    profile = openFragment("profile.html")
    profile = profile.format(SESSION=context.session, USER=userData)

    return HTTPResponse(
        status_code=200,
        data=wrapContent(context.session, context.request, "Profile", profile),
    )
