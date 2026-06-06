from datetime import datetime, timezone

from src.auth import (
    create_session_id,
    get_session_expiry,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password():
    password_hash = hash_password("secret123")
    assert verify_password("secret123", password_hash)
    assert not verify_password("wrong", password_hash)


def test_hash_password_is_unique():
    first = hash_password("same")
    second = hash_password("same")
    assert first != second


def test_verify_password_rejects_invalid_format():
    assert not verify_password("secret", "not-a-valid-hash")


def test_create_session_id_is_unique():
    assert create_session_id() != create_session_id()


def test_get_session_expiry_short_and_long():
    short = get_session_expiry(remember_me=False)
    long = get_session_expiry(remember_me=True)
    assert long > short
    assert short > datetime.now(timezone.utc)
