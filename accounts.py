"""Account rules: usernames, emails, passwords and hashing (MB R7, spec 011).

No Streamlit and no SQL. The salt for a new password is passed in, so tests
can use a fixed one; the app creates it with `secrets.token_bytes`.
"""

import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import datetime

USERNAME_MIN = 3
USERNAME_MAX = 20
PASSWORD_MIN = 8
SALT_MIN_BYTES = 16
HASH_ITERATIONS = 600_000
HASH_NAME = "pbkdf2_sha256"

USERNAME_INVALID = "Username: 3 to 20 characters, only letters, digits and underscore."
USERNAME_TAKEN = "This username is already taken."
EMAIL_INVALID = "Please enter a valid email address."
EMAIL_TAKEN = "This email address already belongs to an account."
PASSWORD_TOO_SHORT = "Password: at least 8 characters."
PASSWORDS_DIFFER = "The two passwords do not match."
SIGN_IN_FAILED = "Wrong username or password"

_USERNAME = re.compile(rf"[A-Za-z0-9_]{{{USERNAME_MIN},{USERNAME_MAX}}}")
_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


@dataclass(frozen=True)
class User:
    id: str
    username: str
    email: str
    password_hash: str
    created_at: datetime


def is_valid_username(username: str) -> bool:
    return _USERNAME.fullmatch(username) is not None


def username_key(username: str) -> str:
    """"Adrian" and "adrian" are the same username (MB R7)."""
    return username.strip().lower()


def is_valid_email(email: str) -> bool:
    return _EMAIL.fullmatch(email) is not None


def normalize_email(email: str) -> str:
    return email.strip().lower()


def sign_up_problems(
    username: str,
    email: str,
    password: str,
    repeat: str,
    *,
    username_taken: bool,
    email_taken: bool,
) -> list[str]:
    """Every reason why this sign up is rejected; empty when it is accepted."""
    found = []
    if not is_valid_username(username):
        found.append(USERNAME_INVALID)
    elif username_taken:
        found.append(USERNAME_TAKEN)
    if not is_valid_email(email):
        found.append(EMAIL_INVALID)
    elif email_taken:
        found.append(EMAIL_TAKEN)
    if len(password) < PASSWORD_MIN:
        found.append(PASSWORD_TOO_SHORT)
    if password != repeat:
        found.append(PASSWORDS_DIFFER)
    return found


def _derive(password: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def hash_password(password: str, salt: bytes) -> str:
    """Stored as "pbkdf2_sha256$<iterations>$<salt hex>$<hash hex>"."""
    if len(salt) < SALT_MIN_BYTES:
        raise ValueError(f"The salt needs at least {SALT_MIN_BYTES} bytes")
    digest = _derive(password, salt, HASH_ITERATIONS)
    return f"{HASH_NAME}${HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        name, iterations, salt_hex, digest_hex = stored.split("$")
        if name != HASH_NAME:
            return False
        digest = _derive(password, bytes.fromhex(salt_hex), int(iterations))
    except ValueError:
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)
