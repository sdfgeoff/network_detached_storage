from .webserver import parse_request, encode_page, HTTPResponse


def test_parse_garbage_returns_none() -> None:
    assert parse_request(b"asdioiwe") is None


def test_parse_simple_get_request() -> None:
    request_data = (
        b"GET /hello.htm HTTP/1.1\r\n"
        b"User-Agent: Mozilla/4.0 (compatible; MSIE5.01; Windows NT)\r\n"
        b"Host: www.tutorialspoint.com\r\n"
        b"Accept-Language: en-us\r\n"
        b"Accept-Encoding: gzip, deflate\r\n"
        b"Connection: Keep-Alive\r\n"
        b"\r\n"
    )

    parsed = parse_request(request_data)
    assert parsed is not None
    assert parsed.url == "/hello.htm"
    assert parsed.method == "GET"
    assert parsed.headers == [
        (b"User-Agent", b"Mozilla/4.0 (compatible; MSIE5.01; Windows NT)"),
        (b"Host", b"www.tutorialspoint.com"),
        (b"Accept-Language", b"en-us"),
        (b"Accept-Encoding", b"gzip, deflate"),
        (b"Connection", b"Keep-Alive"),
    ]

    assert parsed.content == b""


def test_encode_simple_response() -> None:
    response = HTTPResponse(
        status_code=200,
        data=b"argle",
        headers=[
            (b"header1", b"val1"),
            (b"header2", b"val2"),
        ],
    )
    assert (
        encode_page(response) == b"HTTP/1.1 200 OK\r\n"
        b"header1: val1\r\n"
        b"header2: val2\r\n"
        b"\r\n"
        b"argle"
    )
