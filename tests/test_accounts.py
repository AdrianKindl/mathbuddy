"""Account rules: usernames, emails, passwords and hashing (MB R7, spec 011)."""

import pytest

import accounts
from accounts import (
    EMAIL_INVALID,
    EMAIL_TAKEN,
    PASSWORD_TOO_SHORT,
    PASSWORDS_DIFFER,
    USERNAME_INVALID,
    USERNAME_TAKEN,
    hash_password,
    is_valid_email,
    is_valid_username,
    normalize_email,
    sign_up_problems,
    username_key,
    verify_password,
)

SALT = bytes(range(16))
OTHER_SALT = bytes(range(16, 32))


def problems(
    username="adrian",
    email="adrian@example.com",
    password="secret123",
    repeat=None,
    username_taken=False,
    email_taken=False,
):
    return sign_up_problems(
        username,
        email,
        password,
        password if repeat is None else repeat,
        username_taken=username_taken,
        email_taken=email_taken,
    )


# --- Username (MB R7) ---


@pytest.mark.parametrize("name", ["adrian", "Adrian", "abc", "a" * 20, "mia_2", "___", "007"])
def test_valid_usernames(name):
    assert is_valid_username(name)


@pytest.mark.parametrize(
    "name",
    ["", "ab", "a" * 21, "adrian!", "ad rian", "adrian ", "jürgen", "anna-lena", "a.b"],
)
def test_invalid_usernames(name):
    assert not is_valid_username(name)


def test_username_key_ignores_upper_and_lower_case():
    assert username_key("Adrian") == username_key("adrian") == username_key("ADRIAN") == "adrian"


# --- Email ---


@pytest.mark.parametrize("email", ["adrian@example.com", "a.b@uni.novasbe.pt", "A@B.CO"])
def test_valid_emails(email):
    assert is_valid_email(email)


@pytest.mark.parametrize(
    "email", ["", "adrian@", "@example.com", "adrian@example", "adrian example@x.com", "a@@b.com"]
)
def test_invalid_emails(email):
    assert not is_valid_email(email)


def test_emails_are_compared_in_lower_case():
    assert normalize_email(" Adrian@Example.COM ") == "adrian@example.com"


# --- Sign up (A7) ---


def test_valid_sign_up_has_no_problems():
    assert problems() == []


def test_taken_username_is_rejected():
    assert problems(username_taken=True) == [USERNAME_TAKEN]


def test_invalid_username_is_rejected():
    assert problems(username="ab") == [USERNAME_INVALID]


def test_invalid_email_is_rejected():
    assert problems(email="adrian@") == [EMAIL_INVALID]


def test_taken_email_is_rejected():
    assert problems(email_taken=True) == [EMAIL_TAKEN]


def test_password_of_seven_characters_is_rejected():
    assert problems(password="1234567") == [PASSWORD_TOO_SHORT]


def test_password_of_eight_characters_is_accepted():
    assert problems(password="12345678") == []


def test_different_passwords_are_rejected():
    assert problems(password="secret123", repeat="secret124") == [PASSWORDS_DIFFER]


def test_all_problems_are_listed_at_once():
    found = problems(username="a!", email="x", password="short", repeat="other")
    assert set(found) == {USERNAME_INVALID, EMAIL_INVALID, PASSWORD_TOO_SHORT, PASSWORDS_DIFFER}


def test_an_invalid_username_is_not_also_reported_as_taken():
    assert problems(username="a!", username_taken=True) == [USERNAME_INVALID]


# --- Password hashing ---


def test_hash_does_not_contain_the_password():
    stored = hash_password("secret123", SALT)
    assert "secret123" not in stored


def test_same_password_and_salt_give_the_same_hash():
    assert hash_password("secret123", SALT) == hash_password("secret123", SALT)


def test_different_salt_gives_a_different_hash():
    assert hash_password("secret123", SALT) != hash_password("secret123", OTHER_SALT)


def test_right_password_is_accepted():
    assert verify_password("secret123", hash_password("secret123", SALT))


def test_wrong_password_is_refused():
    stored = hash_password("secret123", SALT)
    assert not verify_password("secret124", stored)
    assert not verify_password("", stored)


def test_a_damaged_hash_never_accepts_a_password():
    assert not verify_password("secret123", "")
    assert not verify_password("secret123", "not a hash")


def test_salt_must_be_at_least_16_bytes():
    with pytest.raises(ValueError):
        hash_password("secret123", b"short")


def test_hash_uses_pbkdf2_with_sha256():
    assert hash_password("secret123", SALT).startswith("pbkdf2_sha256$")


def test_sign_in_failure_message_does_not_say_which_part_was_wrong():
    assert accounts.SIGN_IN_FAILED == "Wrong username or password"
