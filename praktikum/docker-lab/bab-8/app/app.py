import os
from pathlib import Path

from flask import Flask, jsonify


app = Flask(__name__)
SECRET_PATH = Path("/run/secrets/app_secret")


@app.get("/")
def index():
    return jsonify(
        service="pens-web",
        status="running",
        uid=os.getuid(),
        gid=os.getgid(),
        secret_mounted=SECRET_PATH.is_file(),
    )


@app.get("/health")
def health():
    if not SECRET_PATH.is_file():
        return jsonify(status="degraded", reason="secret_missing"), 503
    return jsonify(status="ok"), 200
