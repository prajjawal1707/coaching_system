import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from jose import jwt, JWTError

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
DEMO_CODE_PEPPER = os.getenv("DEMO_CODE_PEPPER")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
FEEFLOW_DEMO_ADMIN_KEY = os.getenv("FEEFLOW_DEMO_ADMIN_KEY")

ALGORITHM = "HS256"
SESSION_MINUTES = 60

if not all([
    JWT_SECRET_KEY,
    DEMO_CODE_PEPPER,
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    FEEFLOW_DEMO_ADMIN_KEY,
]):
    raise RuntimeError("Missing RBAC environment variables.")


def generate_access_code():
    # Eight numeric digits, generated on the backend.
    return f"{secrets.randbelow(100_000_000):08d}"


def hash_access_code(role: str, student_id: str, code: str) -> str:
    raw = f"{role}:{student_id}:{code}:{DEMO_CODE_PEPPER}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def check_access_code(
    role: str,
    student_id: str,
    code: str,
    saved_hash: str,
) -> bool:
    return hmac.compare_digest(
        hash_access_code(role, student_id, code),
        saved_hash,
    )


def create_demo_token(role: str, student_id: str, link_id: str = ""):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": student_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=SESSION_MINUTES),
    }

    if link_id:
        payload["link_id"] = link_id

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )


def read_demo_token(token: str):
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        role = payload.get("role")
        student_id = payload.get("sub")

        if role not in ("student", "parent") or not student_id:
            raise ValueError("Invalid demo session.")

        return payload

    except (JWTError, ValueError):
        raise ValueError("Session invalid or expired.")


def verify_supabase_user(access_token: str):
    """Ask Supabase Auth to validate the supplied access token."""
    response = httpx.get(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {access_token}",
        },
        timeout=10.0,
    )

    if response.status_code != 200:
        raise ValueError("Invalid Supabase login session.")

    return response.json()