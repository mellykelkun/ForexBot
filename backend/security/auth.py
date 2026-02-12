"""
SECURITY MODULE — Access Key Authentication & API Protection
ForexBot SaaS — Zero-account auth via single access key.

Workflow:
  1. generate_access_key() → prints a 64-char crypto-secure key
  2. Key hash is stored in .env as ACCESS_KEY_HASH
  3. Dashboard login page takes the raw key, verifies against hash
  4. API routes use X-API-Token header checked against API_SECRET_TOKEN
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from functools import wraps
from typing import Optional

from flask import request, redirect, url_for, session, jsonify, abort
from dotenv import load_dotenv, set_key

load_dotenv()

# ---------------------------------------------------------------------------
# Key generation & hashing
# ---------------------------------------------------------------------------

def generate_access_key(length: int = 48) -> str:
    """Generate a crypto-secure URL-safe access key (~64 chars)."""
    return secrets.token_urlsafe(length)


def hash_key(raw_key: str) -> str:
    """SHA-256 hash of the raw key (hex digest)."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def verify_key(raw_key: str, stored_hash: str) -> bool:
    """Constant-time comparison of key hash vs stored hash."""
    candidate = hash_key(raw_key)
    return hmac.compare_digest(candidate, stored_hash)


# ---------------------------------------------------------------------------
# .env helpers
# ---------------------------------------------------------------------------

_ENV_PATH: Optional[str] = None


def _env_path() -> str:
    global _ENV_PATH
    if _ENV_PATH is None:
        # Walk up from this file to find .env
        d = os.path.dirname(os.path.abspath(__file__))
        for _ in range(5):
            candidate = os.path.join(d, ".env")
            if os.path.exists(candidate):
                _ENV_PATH = candidate
                return _ENV_PATH
            d = os.path.dirname(d)
        # Fallback: project root
        _ENV_PATH = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            ".env",
        )
    return _ENV_PATH


def get_or_create_api_token() -> str:
    """Return the API secret token, creating one if missing."""
    token = os.getenv("API_SECRET_TOKEN")
    if token:
        return token
    token = secrets.token_urlsafe(32)
    try:
        set_key(_env_path(), "API_SECRET_TOKEN", token)
    except Exception:
        pass
    os.environ["API_SECRET_TOKEN"] = token
    return token


def get_access_key_hash() -> Optional[str]:
    """Return the stored ACCESS_KEY_HASH from env."""
    return os.getenv("ACCESS_KEY_HASH")


# ---------------------------------------------------------------------------
# Flask decorators
# ---------------------------------------------------------------------------

def require_dashboard_auth(f):
    """Decorator: protect dashboard routes with access-key session."""

    @wraps(f)
    def decorated(*args, **kwargs):
        stored_hash = get_access_key_hash()
        # If no key configured yet, allow access (first-run)
        if not stored_hash:
            return f(*args, **kwargs)
        # Check session
        if session.get("authenticated"):
            return f(*args, **kwargs)
        # Redirect to login
        return redirect(url_for("login"))

    return decorated


def require_api_token(f):
    """Decorator: protect API routes with X-API-Token header."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_or_create_api_token()
        provided = request.headers.get("X-API-Token", "")
        if not provided or not hmac.compare_digest(provided, token):
            # Also allow if request comes from localhost (internal calls)
            remote = request.remote_addr or ""
            if remote in ("127.0.0.1", "::1", "localhost"):
                return f(*args, **kwargs)
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated


# ---------------------------------------------------------------------------
# CLI utility
# ---------------------------------------------------------------------------

def setup_access_key_interactive() -> str:
    """Generate a new access key, store its hash in .env, return the raw key."""
    raw_key = generate_access_key()
    h = hash_key(raw_key)
    try:
        set_key(_env_path(), "ACCESS_KEY_HASH", h)
    except Exception:
        pass
    os.environ["ACCESS_KEY_HASH"] = h
    return raw_key


if __name__ == "__main__":
    print("=" * 60)
    print("FOREXBOT — GÉNÉRATION CLÉ D'ACCÈS")
    print("=" * 60)
    key = setup_access_key_interactive()
    api_token = get_or_create_api_token()
    print(f"\n🔑 CLÉ D'ACCÈS DASHBOARD (à conserver) :\n   {key}")
    print(f"\n🔒 TOKEN API INTERNE :\n   {api_token}")
    print(f"\n✅ Hash stocké dans .env")
    print("⚠️  Conservez la clé d'accès — elle ne sera plus affichée.")
