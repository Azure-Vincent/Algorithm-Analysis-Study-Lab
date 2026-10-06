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
SANDBOX_FLAG = "--sandbox-worker"     # see launcher.py


def _failure(tests, msg):
    return {"runnable": False, "error": msg, "error_line": None, "passed": 0, "total": len(tests), "results": []}


def run_tests(src, tests, entry=None, params=None, one_indexed=False):
    """Same contract as engine.pseudo.run_tests, executed out of process."""
    payload = json.dumps({"src": src, "tests": tests, "entry": entry, "params": params, "one_indexed": bool(one_indexed)})
    env = {"PYTHONPATH": PROJECT, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8",
           "PATH": os.environ.get("PATH", "")}
    if os.name == "nt":                               # Windows needs SYSTEMROOT to start Python
        env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "")
    if getattr(sys, "frozen", False):
        # Packaged executable (launcher.py): sys.executable is the app itself, which runs the
        # worker when given this flag. TEMP/TMP let the bootloader find its files.
        cmd = [sys.executable, SANDBOX_FLAG]
        for k in ("TEMP", "TMP", "TMPDIR", "LOCALAPPDATA", "_PYI_APPLICATION_HOME_DIR", "_PYI_ARCHIVE_FILE",
                  "_PYI_PARENT_PROCESS_LEVEL"):
            if k in os.environ:
                env[k] = os.environ[k]
        cwd = None
    else:
        cmd = [sys.executable, "-m", "engine.sandbox_worker"]
        cwd = PROJECT
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)   # Windows: never flash a console window
    try:
        proc = subprocess.run(
            cmd, input=payload.encode(), capture_output=True, timeout=WALL_TIMEOUT, cwd=cwd, env=env,
            start_new_session=True, creationflags=flags)
    except subprocess.TimeoutExpired:
        return _failure(tests, "Your code took too long to run (time limit reached) - check for an infinite loop.")
    if proc.returncode != 0 or not proc.stdout:
        return _failure(tests, "Your code used too much time or memory and was stopped.")
    try:
        return json.loads(proc.stdout.decode())
    except ValueError:
        return _failure(tests, "Your code couldn't be run.")
