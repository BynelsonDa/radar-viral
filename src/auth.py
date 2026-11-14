"""Autenticación de un administrador para el dashboard Flask.

Configurar AUTH_USERNAME, AUTH_PASSWORD_HASH y SESSION_SECRET desde el entorno.
El sitio estático de Render no utiliza este servidor y NO queda protegido.
"""
import hmac
import os
import secrets
import time
from collections import defaultdict
from functools import wraps

from flask import abort, redirect, request, session, url_for
from werkzeug.security import check_password_hash

# Limitación simple por proceso. Para despliegues grandes usar Redis.
_attempts = defaultdict(list)
WINDOW = 15 * 60
MAX_ATTEMPTS = 8


def configured():
    return bool(os.getenv("AUTH_USERNAME") and os.getenv("AUTH_PASSWORD_HASH") and
                len(os.getenv("SESSION_SECRET", "")) >= 32)


def create_session_secret():
    return secrets.token_urlsafe(48)


def valid_login(username, password):
    expected = os.getenv("AUTH_USERNAME", "")
    hashed = os.getenv("AUTH_PASSWORD_HASH", "")
    if not configured() or not isinstance(username, str) or not isinstance(password, str):
        return False
    if not hmac.compare_digest(username.encode("utf-8"), expected.encode("utf-8")):
        return False
    try:
        return check_password_hash(hashed, password)
    except (ValueError, TypeError):
        return False


def rate_limit_key():
    # No confiar en X-Forwarded-For aportado por clientes.
    return request.remote_addr or "unknown"


def blocked(key):
    now = time.monotonic()
    _attempts[key] = [t for t in _attempts[key] if now - t < WINDOW]
    return len(_attempts[key]) >= MAX_ATTEMPTS


def failed(key):
    _attempts[key].append(time.monotonic())


def clear_attempts(key):
    _attempts.pop(key, None)


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not configured():
            return ("Inicio de sesión sin configurar: establece AUTH_USERNAME, "
                    "AUTH_PASSWORD_HASH y SESSION_SECRET en el servidor.", 503)
        if not session.get("authenticated"):
            if request.path.startswith("/api/"):
                return {"error": "Inicia sesión para continuar."}, 401
            return redirect(url_for("login", next=request.path if request.path == "/" else "/"))
        return view(*args, **kwargs)
    return wrapper


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def check_csrf(token):
    original = session.get("csrf_token", "")
    return bool(original and isinstance(token, str) and
                hmac.compare_digest(original, token))
