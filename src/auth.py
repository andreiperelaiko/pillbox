import os
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import APIKeyCookie

from src.db import get_user_by_session


SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "pillbox_session")
SESSION_COOKIE_PATH = os.getenv("SESSION_COOKIE_PATH", "/api")
SESSION_EXPIRE_DAYS = int(os.getenv("SESSION_EXPIRE_DAYS", "30"))
SESSION_SHORT_EXPIRE_DAYS = int(os.getenv("SESSION_SHORT_EXPIRE_DAYS", "1"))
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    rounds = 390000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    digest_b64 = base64.b64encode(digest).decode("utf-8")
    return f"pbkdf2_sha256${rounds}${salt_b64}${digest_b64}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, rounds_str, salt_b64, digest_b64 = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        rounds = int(rounds_str)
        salt = base64.b64decode(salt_b64.encode("utf-8"))
        expected = base64.b64decode(digest_b64.encode("utf-8"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_session_id() -> str:
    return secrets.token_urlsafe(32)


def get_session_expiry(remember_me: bool = False) -> datetime:
    days = SESSION_EXPIRE_DAYS if remember_me else SESSION_SHORT_EXPIRE_DAYS
    return datetime.now(timezone.utc) + timedelta(days=days)


def set_session_cookie(response: Response, session_id: str, remember_me: bool = False) -> None:
    days = SESSION_EXPIRE_DAYS if remember_me else SESSION_SHORT_EXPIRE_DAYS
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        max_age=days * 24 * 60 * 60,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite="lax",
        path=SESSION_COOKIE_PATH,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path=SESSION_COOKIE_PATH)


cookie_scheme = APIKeyCookie(name=SESSION_COOKIE_NAME, auto_error=False)


def get_current_user(session_id: str = Depends(cookie_scheme)) -> Dict[str, Any]:
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = get_user_by_session(session_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    return user
