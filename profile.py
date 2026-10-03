"""Local, sign-in-free access: every request works on the single local profile.

The app is meant to run on your own computer (it binds to 127.0.0.1). Two protections stay in
place because a web page you visit in another tab could still try to send requests to
localhost: API writes must be JSON (browsers can't send cross-site JSON without CORS, which this
app never grants), and pages forbid being framed.
"""
from __future__ import annotations

from flask import g, jsonify, request

import db


def load():
    """before_request hook."""
    g.user_id = db.local_profile_id()
    if request.method == "POST" and request.path.startswith("/api/") and not request.is_json:
        return jsonify({"error": "JSON body required"}), 415
    return None
