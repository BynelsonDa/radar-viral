"""Private Flask deployment using existing GitHub Actions data/live.json snapshot.

No MySQL is required. All data and assets are protected by a session.
"""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, redirect, render_template_string, request, send_file, send_from_directory, session
from auth import blocked, check_csrf, clear_attempts, configured, csrf_token, failed, rate_limit_key, valid_login

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "web"
load_dotenv(ROOT / ".env")

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET") or os.urandom(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("AUTH_COOKIE_SECURE", "1") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)


@app.after_request
def headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.before_request
def guard():
    if request.path in ("/health", "/login"):
        return None
    if not configured():
        return "Inicio de sesión sin configurar. Define los secretos AUTH_* y SESSION_SECRET en Render.", 503
    if not session.get("authenticated"):
        if request.path.startswith("/api/") or request.path.startswith("/data/"):
            return {"error": "Se requiere inicio de sesión."}, 401
        return redirect("/login")
    return None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.route("/login", methods=["GET", "POST"])
def login():
    if not configured():
        return "Cuenta sin activar: configura AUTH_USERNAME, AUTH_PASSWORD_HASH y SESSION_SECRET.", 503
    if session.get("authenticated"):
        return redirect("/")
    error, status = None, 200
    if request.method == "POST":
        key = rate_limit_key()
        if not check_csrf(request.form.get("csrf_token", "")):
            error, status = "Formulario caducado. Actualiza la página.", 400
        elif blocked(key):
            error, status = "Demasiados intentos. Inténtalo más tarde.", 429
        elif valid_login(request.form.get("username", ""), request.form.get("password", "")):
            clear_attempts(key)
            session.clear()
            session.permanent = True
            session["authenticated"] = True
            session["username"] = os.environ["AUTH_USERNAME"]
            csrf_token()
            return redirect("/")
        else:
            failed(key)
            error, status = "Usuario o contraseña incorrectos.", 401
    return render_template_string((WEB / "login.html").read_text(encoding="utf-8"),
                                  csrf=csrf_token(), error=error), status


@app.post("/logout")
def logout():
    if not check_csrf(request.form.get("csrf_token", "")):
        abort(400)
    session.clear()
    return redirect("/login")


@app.get("/api/session")
def user_session():
    return {"username": session.get("username"), "csrf_token": csrf_token()}


@app.get("/data/live.json")
def live_data():
    return send_file(ROOT / "data" / "live.json", mimetype="application/json")


@app.get("/data/channel.json")
def channel_data():
    return send_file(ROOT / "data" / "channel.json", mimetype="application/json")


@app.get("/")
def index():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    # The existing offline.js processes the tracked data/live.json snapshot.
    html = html.replace('<script src="/app.js" defer></script>',
        '<script>window.RADAR_LIVE_FILE="/data/live.json";</script>'
        '<script src="/offline.js" defer></script>'
        '<script src="/app.js" defer></script>'
        '<script src="/private-session.js" defer></script>')
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.get("/<path:filename>")
def assets(filename):
    if filename not in {"app.js", "style.css", "ideas.js", "offline.js", "private-session.js", "channel-panel.js"}:
        abort(404)
    return send_from_directory(WEB, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
