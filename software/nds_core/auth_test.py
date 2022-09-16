from .auth import encode_password_v1, validate_password_v1, encode_password


def test_encode_password_v1() -> None:
    res = encode_password_v1(b"testPassword")

    assert validate_password_v1(b"testPassword", res) is True
    assert validate_password_v1(b"testPasswor", res) is False

    # print(encode_password_v1(b"iwertoiu"))
    secret = b'{"version": 1, "salt": "yjtNt3U3Az4iispaYzDX+uNgEYGBV9w/+l74IZUX1HY=", "secret": "DE1wKfI+dvuA43yeWq93vg2l7PtTHltyNGqjVvFCCjWLu9UopIcNNC0sR6nEoEOlnAJnQCsBS0J2sSgWSbyWug=="}'
    assert validate_password_v1(b"iwertoiu", secret) is True


def test_encode_password_is_v1() -> None:
    res = encode_password(b"testPassword")
    assert validate_password_v1(b"testPassword", res) is True
