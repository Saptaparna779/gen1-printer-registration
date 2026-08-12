"""
JWT authentication for the GEN 1 Printer Onboarding & Registration service.

Provides:
- create_access_token(): issues a signed JWT for a given subject (user).
- verify_token(): validates a JWT's signature and expiry, raising an
  HTTPException if invalid.

This is a minimal, demo-appropriate implementation:
- Single shared secret key (HS256), loaded from .env.
- No refresh tokens, no scopes/roles -- just "is this caller authenticated."
"""
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import Header, HTTPException
from jose import JWTError, jwt

load_dotenv()

JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(subject: str) -> str:
    """Create a signed JWT for the given subject (e.g. a user_id)."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(authorization: str = Header(...)) -> str:
    """
    FastAPI dependency: extracts and verifies a JWT from the
    Authorization header. Expects the format: "Bearer <token>".
    Returns the token's subject (e.g. user_id) if valid.
    Raises HTTPException(401) if missing, malformed, or invalid.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or malformed Authorization header. Expected: Bearer <token>",
        )
    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(status_code=401, detail="Token missing subject")
    return subject
