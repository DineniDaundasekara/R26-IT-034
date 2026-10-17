"""MongoDB authentication for login and register."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError
import certifi

PBKDF2_ITERATIONS = 210_000
TOKEN_TTL_DAYS = 7
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
DEFAULT_DB_NAME = "career_intelligence"
DEFAULT_MONGODB_URI = "mongodb+srv://manodyasamindi2002_db_user:1QOWkociPRVeVesB@cluster0.6ib0dah.mongodb.net/?appName=Cluster0"

DEMO_ACCOUNT = {
    "full_name": "Research Demo",
    "email": "demo@pathready.ai",
    "password": "PathReady2026",
    "role": "user",
}

ADMIN_ACCOUNT = {
    "full_name": "HR Admin",
    "email": "hr@career-intel.ai",
    "password": "CareerIntel2026",
    "role": "admin",
}

_client: Optional[MongoClient] = None
_db = None


class AuthRegisterRequest(BaseModel):
    fullName: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class AuthLoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=128)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _public_ip() -> str:
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=4) as response:
            return response.read().decode("utf-8").strip()
    except Exception:
        return "unknown"


def _mongo_error(exc: Exception) -> HTTPException:
    print(f"[AUTH] MongoDB error: {type(exc).__name__}: {exc}")
    ip_address = _public_ip()
    return HTTPException(
        status_code=503,
        detail=(
            "MongoDB Atlas blocked this computer (IP not allowed). "
            "Open cloud.mongodb.com -> Network Access -> Add IP Address -> "
            "Allow Access from Anywhere (0.0.0.0/0), wait 1 minute, then register again. "
            f"This computer's public IP is {ip_address}."
        ),
    )


def _mongo_client(uri: str) -> MongoClient:
    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=15000,
        connectTimeoutMS=15000,
        tls=True,
        tlsCAFile=certifi.where(),
        tlsDisableOCSPEndpointCheck=True,
    )
    client.admin.command("ping")
    return client


def get_db():
    global _client, _db
    if _db is not None:
        return _db

    uri = os.getenv("MONGODB_URI", "").strip() or DEFAULT_MONGODB_URI
    if not uri:
        raise HTTPException(
            status_code=503,
            detail="MONGODB_URI is not configured. Add it to the project .env file.",
        )

    db_name = os.getenv("MONGODB_DB", DEFAULT_DB_NAME).strip() or DEFAULT_DB_NAME
    try:
        _client = _mongo_client(uri)
        _db = _client[db_name]
        return _db
    except HTTPException:
        raise
    except Exception as exc:
        _client = None
        _db = None
        raise _mongo_error(exc)


def mongo_ready() -> bool:
    try:
        get_db().command("ping")
        return True
    except Exception:
        return False


def _hash_password(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        PBKDF2_ITERATIONS,
    ).hex()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _validate_email(email: str) -> str:
    normalized = _normalize_email(email)
    if not EMAIL_PATTERN.match(normalized):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    return normalized


def _validate_name(full_name: str) -> str:
    cleaned = " ".join(full_name.strip().split())
    if len(cleaned) < 2:
        raise HTTPException(status_code=400, detail="Please enter your full name.")
    return cleaned


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    if password.isalpha() or password.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Password must include both letters and numbers.",
        )


def _public_user(doc: dict) -> dict:
    created = doc.get("created_at")
    if isinstance(created, datetime):
        created = created.isoformat()
    return {
        "id": str(doc["_id"]),
        "fullName": doc.get("full_name", ""),
        "email": doc.get("email", ""),
        "role": doc.get("role", "user"),
        "createdAt": created,
    }


def _create_session(db, user_id) -> str:
    token = secrets.token_urlsafe(48)
    db.sessions.insert_one(
        {
            "token": token,
            "user_id": user_id,
            "expires_at": _utc_now() + timedelta(days=TOKEN_TTL_DAYS),
            "created_at": _utc_now(),
        }
    )
    return token


def _seed_account(db, account: dict) -> None:
    if db.users.find_one({"email": account["email"]}):
        return

    salt_hex = secrets.token_hex(16)
    db.users.insert_one(
        {
            "full_name": account["full_name"],
            "email": account["email"],
            "password_hash": _hash_password(account["password"], salt_hex),
            "password_salt": salt_hex,
            "role": account.get("role", "user"),
            "created_at": _utc_now(),
        }
    )


def init_auth_db() -> None:
    db = get_db()
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.sessions.create_index([("token", ASCENDING)], unique=True)
    db.sessions.create_index([("expires_at", ASCENDING)])
    _seed_account(db, DEMO_ACCOUNT)
    _seed_account(db, ADMIN_ACCOUNT)
    print("[INIT] MongoDB auth connected: users and sessions collections ready.")


def register_user(payload: AuthRegisterRequest) -> dict:
    full_name = _validate_name(payload.fullName)
    email = _validate_email(payload.email)
    _validate_password(payload.password)

    salt_hex = secrets.token_hex(16)
    db = get_db()

    try:
        result = db.users.insert_one(
            {
                "full_name": full_name,
                "email": email,
                "password_hash": _hash_password(payload.password, salt_hex),
                "password_salt": salt_hex,
                "role": "user",
                "created_at": _utc_now(),
            }
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists. Please sign in.",
        )
    except PyMongoError as exc:
        raise _mongo_error(exc)

    user = db.users.find_one({"_id": result.inserted_id})
    token = _create_session(db, result.inserted_id)
    return {"success": True, "token": token, "user": _public_user(user)}


def login_user(payload: AuthLoginRequest) -> dict:
    email = _validate_email(payload.email)
    db = get_db()
    user = db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    expected = user["password_hash"]
    actual = _hash_password(payload.password, user["password_salt"])
    if not hmac.compare_digest(expected, actual):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = _create_session(db, user["_id"])
    return {"success": True, "token": token, "user": _public_user(user)}


def authenticate_token(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Please sign in to continue.")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Please sign in to continue.")

    db = get_db()
    session = db.sessions.find_one({"token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Your session is no longer valid.")

    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at is None or expires_at.tzinfo is None:
        if isinstance(expires_at, datetime):
            expires_at = expires_at.replace(tzinfo=timezone.utc)

    if not isinstance(expires_at, datetime) or expires_at < _utc_now():
        db.sessions.delete_one({"token": token})
        raise HTTPException(status_code=401, detail="Your session has expired. Please sign in again.")

    user = db.users.find_one({"_id": session["user_id"]})
    if not user:
        db.sessions.delete_one({"token": token})
        raise HTTPException(status_code=401, detail="Your session is no longer valid.")

    return {"success": True, "user": _public_user(user)}


def require_admin(authorization: Optional[str]) -> dict:
    """Authenticates the session token and additionally requires the admin role.

    Used to gate HR-only endpoints server-side, independent of whatever the
    frontend chooses to show or hide.
    """
    session = authenticate_token(authorization)
    user = session["user"]
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return session


def logout_session(authorization: Optional[str]) -> dict:
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if token:
        try:
            get_db().sessions.delete_one({"token": token})
        except Exception:
            pass

    return {"success": True}
