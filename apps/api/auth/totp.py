import os
import pyotp

TOTP_SKIP = os.getenv("TOTP_SKIP", "false").lower() == "true"


def generate_secret() -> str:
    return pyotp.random_base32()


def get_totp(secret: str) -> pyotp.TOTP:
    return pyotp.TOTP(secret)


def verify_totp(secret: str, token: str) -> bool:
    if TOTP_SKIP:
        return True
    totp = get_totp(secret)
    return totp.verify(token, valid_window=1)


def get_totp_uri(secret: str, name: str, issuer: str = "ecommerce") -> str:
    totp = get_totp(secret)
    return totp.provisioning_uri(name=name, issuer_name=issuer)
