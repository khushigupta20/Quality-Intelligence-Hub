"""
Authentication utility for Quality Intelligence Hub.

Passwords are hashed with Werkzeug's pbkdf2 (sha256) — no extra packages needed.
Credentials are stored in config.json under the "users" key.
The IBM ICA Agent is called as the final verification step when configured.
Falls back to local-only verification if ICA is not configured or unreachable.
"""

import os
import json
import logging
from functools import wraps
from flask import session, redirect, url_for

logger = logging.getLogger(__name__)

# Resolve config.json path (same as settings.py)
CONFIG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'config.json')
)


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plaintext: str) -> str:
    """Return a Werkzeug pbkdf2:sha256 hash of the plaintext password."""
    from werkzeug.security import generate_password_hash
    return generate_password_hash(plaintext, method='pbkdf2:sha256')


def verify_password(plaintext: str, hashed: str) -> bool:
    """Return True if plaintext matches the stored hash."""
    from werkzeug.security import check_password_hash
    try:
        return check_password_hash(hashed, plaintext)
    except Exception:
        return False


# ── User store (config.json "users" key) ─────────────────────────────────────

def _load_config() -> dict:
    """Load the raw config.json file."""
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Could not read config.json in auth: %s", exc)
        return {}


def _save_config(data: dict) -> None:
    """Write the full config dict back to config.json."""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def get_users() -> dict:
    """Return the users dict: { username: { password_hash, role } }.
    If no users exist yet, creates the default admin account automatically.
    """
    config = _load_config()
    users  = config.get("users", {})

    if not users:
        # First run — seed default admin account
        users = {
            "admin": {
                "password_hash": hash_password("admin123"),
                "role":          "admin",
            }
        }
        config["users"] = users
        _save_config(config)
        logger.info("Default admin account created in config.json")

    return users


def save_user(username: str, plaintext_password: str, role: str = "user") -> None:
    """Create or update a user in config.json (password is hashed before storing)."""
    config = _load_config()
    users  = config.get("users", {})
    users[username] = {
        "password_hash": hash_password(plaintext_password),
        "role":          role,
    }
    config["users"] = users
    _save_config(config)
    logger.info("User '%s' saved to config.json", username)


def delete_user(username: str) -> bool:
    """Delete a user from config.json. Returns False if user did not exist."""
    config = _load_config()
    users  = config.get("users", {})
    if username not in users:
        return False
    del users[username]
    config["users"] = users
    _save_config(config)
    logger.info("User '%s' deleted from config.json", username)
    return True


# ── ICA verification step ─────────────────────────────────────────────────────
# NOTE: The IBM ICA Agent is a requirements analysis tool, not an access control
# system. Sending auth prompts to it produces unpredictable responses.
# Authentication is handled entirely by local bcrypt password verification.
# This function is retained as a no-op placeholder for future integration
# with a dedicated identity provider if needed.

def _ica_verify_login(username: str, endpoint: str, api_key: str) -> bool:
    """Always returns True — auth is handled by local password verification only."""
    logger.info("Auth verified locally for '%s' — ICA not used for login", username)
    return True


# ── Main login function ───────────────────────────────────────────────────────

def attempt_login(username: str, password: str,
                  ica_endpoint: str = "", ica_api_key: str = "") -> dict:
    """
    Verify credentials and optionally confirm with ICA.

    Returns:
        {"success": True,  "role": <role>}   on successful login
        {"success": False, "error": <msg>}   on failure
    """
    if not username or not password:
        return {"success": False, "error": "Username and password are required."}

    users = get_users()
    user  = users.get(username.strip().lower())

    if not user:
        logger.warning("Login attempt for unknown user '%s'", username)
        return {"success": False, "error": "Invalid username or password."}

    if not verify_password(password, user.get("password_hash", "")):
        logger.warning("Wrong password for user '%s'", username)
        return {"success": False, "error": "Invalid username or password."}

    # Password OK — now call ICA for final confirmation
    ica_allowed = _ica_verify_login(username.strip().lower(), ica_endpoint, ica_api_key)
    if not ica_allowed:
        logger.warning("ICA denied access for user '%s'", username)
        return {"success": False, "error": "Access denied by ICA Agent. Please contact your administrator."}

    logger.info("User '%s' logged in successfully", username)
    return {"success": True, "role": user.get("role", "user")}


# ── Flask login_required decorator ───────────────────────────────────────────

def login_required(f):
    """Flask route decorator — redirects to /login if no active session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user'):
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated
