import os
from pathlib import Path

from flask import Flask, jsonify


app = Flask(__name__)
SECRET_PATH = Path("/run/secrets/app_secret")
MIN_SECRET_BYTES = 32


def secret_ready() -> bool:
    """Secret siap bila dapat dibaca UID aplikasi dan cukup panjang."""
    try:
        return len(SECRET_PATH.read_bytes().strip()) >= MIN_SECRET_BYTES
    except OSError:
        return False


@app.get("/")
def index():
    return jsonify(
        service="pens-web",
        status="running",
        uid=os.getuid(),
        gid=os.getgid(),
        secret_ready=secret_ready(),
    )


@app.get("/health")
def health():
    if not secret_ready():
        return jsonify(status="degraded", reason="secret_unavailable"), 503
    return jsonify(status="ok"), 200
