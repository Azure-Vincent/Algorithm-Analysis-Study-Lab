"""Run untrusted student pseudocode in a separate, resource-limited process.

The interpreter in engine/pseudo.py already restricts what pseudocode can express
(no imports, no attribute access, no dunder names, empty builtins, step and recursion
limits). On a public server we additionally isolate execution:

* a fresh Python process per grading request, so a runaway expression
  (e.g. 10**10**10, huge lists) can't stall or crash a web worker;
* CPU-time, memory, file-size and process-count limits (Linux/macOS);
* a wall-clock timeout;
* an empty environment - the child never sees SECRET_KEY or DATABASE_URL.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WALL_TIMEOUT = float(os.environ.get("SANDBOX_TIMEOUT", "10"))


def _failure(tests, msg):
    return {"runnable": False, "error": msg, "error_line": None, "passed": 0, "total": len(tests), "results": []}


def run_tests(src, tests, entry=None, params=None):
    """Same contract as engine.pseudo.run_tests, executed out of process."""
    payload = json.dumps({"src": src, "tests": tests, "entry": entry, "params": params})
    env = {"PYTHONPATH": PROJECT, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8",
           "PATH": os.environ.get("PATH", "")}
    if os.name == "nt":                               # Windows needs SYSTEMROOT to start Python
        env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "")
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "engine.sandbox_worker"],
            input=payload.encode(), capture_output=True, timeout=WALL_TIMEOUT, cwd=PROJECT, env=env,
            start_new_session=True)
    except subprocess.TimeoutExpired:
        return _failure(tests, "Your code took too long to run (time limit reached) - check for an infinite loop.")
    if proc.returncode != 0 or not proc.stdout:
        return _failure(tests, "Your code used too much time or memory and was stopped.")
    try:
        return json.loads(proc.stdout.decode())
    except ValueError:
        return _failure(tests, "Your code couldn't be run.")
