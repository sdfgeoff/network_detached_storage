from typing import Optional, Literal, Callable, List, Tuple
import socket
import os
import time
from .config import _Config

from . import log


Methods = Literal["GET", "POST", "DELETE"]
Headers = List[Tuple[bytes, bytes]]


class HTTPRequest:
    method: Methods
    url: str
    content: bytes
    headers: Headers

    def __init__(self, method: Methods, url: str, content: bytes, headers: Headers):
        self.method = method
        self.url = url
        self.content = content
        self.headers = headers


class HTTPResponse:
    status_code: int
    data: bytes
    headers: Headers

    def __init__(self, status_code: int, data: bytes):
        self.status_code = status_code
        self.data = data


def create_http_socket(server_config: _Config) -> socket.socket:
    '''Creates a TCP socket to be used for servicing HTTP requests'''
    http_socket = socket.socket()
    http_socket.bind(('0.0.0.0', server_config.WEBSERVER_PORT))
    
    # Allow reuse
    http_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    http_socket.listen(1)
    http_socket.settimeout(0)
    return http_socket




def parse_method(raw: bytes) -> Methods:
    method: Optional[Methods] = None
    if raw == b'GET':
        method = 'GET'
    elif raw == b'POST':
        method = 'POST'
    elif raw == b'DELETE':
        method = 'DELETE'

    if method is None:
        raise Exception(f"unknown method {repr(raw)}")
    
    return method

def parse_request(raw: bytes) -> Optional[HTTPRequest]:
    """ Extracts a HTTP request from raw bytes """
    try:
        lines = raw.split(b'\n')
        method_raw, url_raw, protocol = lines[0].strip().split(b' ')
        headers: Headers = [ 
            tuple(l.strip().split(b':', maxsplit=1)) # type: ignore # Mypy can't tell about the maxsplit
            for l in lines[1:]
        ]  

        method = parse_method(method_raw)
        url = url_raw.decode('utf-8')
    except Exception as err:
        log.warn("failed_parsing_request", {"exception": str(err)})


    return HTTPRequest(
        method=method, 
        url=url, 
        headers=headers ,
        content=b""
    )



def get_data_from_client(client_socket: socket.socket) -> Optional[bytes]:
    # TODO: continue receiving until end of transmission
    try:
        raw = client_socket.recv(1024)
    except OSError as err:
        log.warn("client_recv_err", {"exception": str(err)})
        return None

    return raw



def send_response_bytes(server_config: _Config, client_socket: socket.socket, page_bytes: bytes) -> None:
    try:
        client_socket.settimeout(server_config.WEBSERVER_CLIENT_TIMEOUT_MS)
        while len(page_bytes) > 0:
            sent = client_socket.send(page_bytes)
            page_bytes = page_bytes[sent:]
            time.sleep(server_config.WEBSERVER_BUFFER_SEND_MS / 1000)    
        client_socket.settimeout(0)

    except OSError:
        log.warn('client_timed_out', {})


def encode_page(response: HTTPResponse) -> bytes:
    status_line = f"HTTP/1.1 {response.status_code} {STATUS_CODE_TO_REASON[response.status_code]}".encode('utf-8')
    headers = b''
    return status_line + b'\r\n' + headers + b'\r\n' + response.data



def serve_page(server_config: _Config, http_socket: socket.socket, page_handler: Callable[[HTTPRequest], HTTPResponse]) -> None:
    '''A dumb http server that can serve multiple pages'''
    try:
        client_socket, addr = http_socket.accept()
    except OSError:
        return

    log.info('client_connected', {"addr": addr})
    raw = get_data_from_client(client_socket)
    if raw is not None:
        page_request = parse_request(raw)
        if page_request is not None:
            page_response = page_handler(page_request)
            page_bytes = encode_page(page_response)
            send_response_bytes(server_config, client_socket, page_bytes)


            

    client_socket.close()



STATUS_CODE_TO_REASON = {
    100: "Continue",
    101: "Switching Protocols",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    307: "Temporary Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Time-out",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Request Entity Too Large",
    414: "Request-URI Too Large",
    415: "Unsupported Media Type",
    416: "Requested range not satisfiable",
    417: "Expectation Failed",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Time-out",
    505: "HTTP Version not supported",
}