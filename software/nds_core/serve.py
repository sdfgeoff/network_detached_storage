from .config import config, _Config
import time

from .webserver import HttpSocket, serve_page, HTTPRequest, HTTPResponse
from .routes import handle_route_request
from .storage import Storage


def run(server_config: _Config) -> None:
    with HttpSocket(server_config) as http_socket:
        storage = Storage("testdb.db")

        def route_handler(request: HTTPRequest) -> HTTPResponse:
            return handle_route_request(storage, request)

        while 1:
            served_client = serve_page(server_config, http_socket, route_handler)
            if not served_client:
                time.sleep(0.1)  # TODO: base this on if a request was served or not


if __name__ == "__main__":
    run(config)
