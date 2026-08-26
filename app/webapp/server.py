"""Flask web UI: password-protected Captures and Logs viewer."""
from __future__ import annotations

import hmac
import time
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory, session

from app.config import Config
from app.logging_provider import get_logger

# Simple in-memory brute-force throttle: IP -> (failed_attempts, locked_until_ts)
_login_attempts: dict[str, tuple[int, float]] = {}
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 30


def _is_locked_out(ip: str) -> bool:
    attempts, locked_until = _login_attempts.get(ip, (0, 0.0))
    return attempts >= _MAX_ATTEMPTS and time.time() < locked_until


def _register_failure(ip: str) -> None:
    attempts, _ = _login_attempts.get(ip, (0, 0.0))
    attempts += 1
    locked_until = time.time() + _LOCKOUT_SECONDS if attempts >= _MAX_ATTEMPTS else 0.0
    _login_attempts[ip] = (attempts, locked_until)


def _clear_failures(ip: str) -> None:
    _login_attempts.pop(ip, None)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            return jsonify({"error": "authentication required"}), 401
        return view(*args, **kwargs)

    return wrapped


def create_app(config: Config) -> Flask:
    app = Flask(__name__)
    app.secret_key = config.web_secret_key
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    logger = get_logger()

    if config.web_password == "changeme":
        logger.warning(
            "WEBUI_PASSWORD is not set; using insecure default password. "
            "Set the WEBUI_PASSWORD environment variable."
        )

    @app.get("/login")
    def login_page():
        if session.get("authenticated"):
            return render_template("index.html")
        return render_template("login.html", error=None)

    @app.post("/login")
    def login_submit():
        ip = request.remote_addr or "unknown"
        if _is_locked_out(ip):
            return render_template(
                "login.html", error="Too many attempts. Try again later."
            ), 429

        password = request.form.get("password", "")
        if hmac.compare_digest(password, config.web_password):
            _clear_failures(ip)
            session["authenticated"] = True
            return render_template("index.html")

        _register_failure(ip)
        logger.warning("Failed web UI login attempt from %s", ip)
        return render_template("login.html", error="Invalid password."), 401

    @app.get("/logout")
    def logout():
        session.clear()
        return render_template("login.html", error=None)

    @app.get("/")
    def index():
        if not session.get("authenticated"):
            return render_template("login.html", error=None)
        return render_template("index.html")

    @app.get("/api/captures")
    @login_required
    def api_captures():
        files = sorted(
            config.captures_dir.glob("*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        items = [
            {
                "name": f.name,
                "type": "video" if f.suffix.lower() in (".mp4", ".avi", ".mov") else "image",
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime,
            }
            for f in files
            if f.is_file()
        ]
        return jsonify(items)

    @app.get("/captures/<path:filename>")
    @login_required
    def get_capture(filename: str):
        return send_from_directory(config.captures_dir, filename)

    @app.get("/api/logs")
    @login_required
    def api_logs():
        if not config.log_file.exists():
            return jsonify({"content": ""})
        max_bytes = 200_000
        with open(config.log_file, "r", encoding="utf-8", errors="replace") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - max_bytes))
            content = fh.read()
        return jsonify({"content": content})

    return app
