from . import routes
from .config import config, _Config

from .webserver import create_http_socket, serve_page
from .routes import handle_route_request




def run(server_config: _Config) -> None:
    http_socket = create_http_socket(server_config)

    while 1:
        serve_page(server_config, http_socket, handle_route_request)


if __name__ == "__main__":
    run(config)