import hashlib
import json
import os
import base64


def encode_password_v1(password: bytes) -> bytes:
    salt = os.urandom(32)

    raw_secret = hashlib.scrypt(password, salt=salt, n=2**14, r=8, p=4, dklen=64)

    bundle = {
        "version": 1,
        "salt": base64.b64encode(salt).decode("utf-8"),
        "secret": base64.b64encode(raw_secret).decode("utf-8"),
    }
    return json.dumps(bundle).encode("utf-8")


def validate_password_v1(password: bytes, secret_bundle: bytes) -> bool:
    bundle = json.loads(secret_bundle.decode("utf-8"))
    assert bundle["version"] == 1

    salt = base64.b64decode(bundle["salt"])
    target_secret = base64.b64decode(bundle["secret"])

    this_secret = hashlib.scrypt(password, salt=salt, n=2**14, r=8, p=4, dklen=64)
    return this_secret == target_secret


def encode_password(password: bytes) -> bytes:
    return encode_password_v1(password)
