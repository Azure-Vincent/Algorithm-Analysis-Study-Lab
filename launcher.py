"""Desktop launcher: starts the existing Flask app on a local Waitress server and opens the browser.

This is what the packaged executable (AlgorithmStudy.exe) runs. It only launches the app;
all routes and logic stay in app.py. Developers can keep using `python app.py`, or run
`python launcher.py` to try the desktop behaviour from source.

    Start the app (create_app)  ->  wait until /healthz answers  ->  open the browser once
    ->  keep serving  ->  on window close / Ctrl+C: stop the server, checkpoint the database

Options:  --port N   preferred port (default: PORT env var, else 5000; a free port is used if taken)
          --data-dir PATH   where the database lives (default: the per-user folder below)
          --no-browser      don't open a browser (used by the smoke test)

The server binds to 127.0.0.1 only, so it is not reachable from other machines.
User data is kept outside the executable, so rebuilding or updating the app never resets it:
    Windows  %LOCALAPPDATA%\\AlgorithmStudy\\trainer.db
    macOS    ~/Library/Application Support/AlgorithmStudy/trainer.db
    Linux    ~/.local/share/AlgorithmStudy/trainer.db   ($XDG_DATA_HOME respected)
BIGO_DB, if set, still overrides the database file exactly as it does for app.py.
"""
from __future__ import annotations

import sys

SANDBOX_FLAG = "--sandbox-worker"

# The packaged app re-runs itself as the pseudocode sandbox worker (see engine/sandbox.py).
# Handle that first, before importing Flask/SymPy, so grading subprocesses start quickly.
if len(sys.argv) > 1 and sys.argv[1] == SANDBOX_FLAG:
    from engine import sandbox_worker
    sandbox_worker.main()
    sys.exit(0)

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import signal  # noqa: E402
import socket  # noqa: E402
import sqlite3  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
import traceback  # noqa: E402
import urllib.request  # noqa: E402
import webbrowser  # noqa: E402

APP_NAME = "AlgorithmStudy"
HOST = "127.0.0.1"
DEFAULT_PORT = 5000
APP_ID = "bigo-trainer"          # returned by /healthz, used to recognise an already-running copy
FROZEN = getattr(sys, "frozen", False)


def user_data_dir() -> str:
    """Per-user folder for writable data (never inside the executable or its temp folder)."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, APP_NAME)


def health(port: int, timeout: float = 1.0):
    """The app's /healthz answer on this port, or None if nothing (or something else) answers."""
    try:
        with urllib.request.urlopen(f"http://{HOST}:{port}/healthz", timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data if data.get("app") == APP_ID else None
    except Exception:
        return None


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if os.name != "nt":              # same as the server: ignore old TIME_WAIT connections after a restart
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((HOST, port))
            return True
        except OSError:
            return False


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, 0))
        return s.getsockname()[1]


def checkpoint(db_file: str):
    """Fold SQLite's write-ahead log back into the main file (committed data is safe either way)."""
    try:
        con = sqlite3.connect(db_file, timeout=5)
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        con.close()
    except sqlite3.Error:
        pass


def open_browser(url: str):
    try:
        webbrowser.open(url, new=2)
    except Exception:
        print(f"  Couldn't open a browser automatically - open {url} yourself.", flush=True)


def parse_args(argv):
    p = argparse.ArgumentParser(prog=APP_NAME, description="Algorithm Study (Big-O Trainer) desktop launcher")
    p.add_argument("--port", type=int, default=int(os.environ.get("PORT") or DEFAULT_PORT))
    p.add_argument("--data-dir", default=None)
    p.add_argument("--no-browser", action="store_true")
    return p.parse_args(argv)


def run(argv=None) -> int:
    args = parse_args(argv)

    # 1. Already running? Reuse it instead of starting a second server on the same database.
    if health(args.port):
        url = f"http://{HOST}:{args.port}/"
        print(f"  Algorithm Study is already running at {url}", flush=True)
        if not args.no_browser:
            open_browser(url)
        return 0

    # 2. Persistent data location (set before the app is imported/configured).
    if not os.environ.get("BIGO_DB"):
        data_dir = os.path.abspath(args.data_dir or user_data_dir())
        os.makedirs(data_dir, exist_ok=True)
        os.environ["BIGO_DB"] = os.path.join(data_dir, "trainer.db")
    os.environ.setdefault("APP_ENV", "development")

    from waitress import create_server
    from waitress import wasyncore
    from app import create_app
    import db

    application = create_app()
    db_file = db.sqlite_path()

    # 3. Bind to localhost: the preferred port if it's free, otherwise any free port.
    port = args.port if port_is_free(args.port) else free_port()
    server = create_server(application, host=HOST, port=port, threads=8, ident=APP_NAME)
    url = f"http://{HOST}:{port}/"
    thread = threading.Thread(target=server.run, name="waitress", daemon=True)
    thread.start()

    # 4. Wait until the app really answers, then open the browser exactly once.
    deadline = time.time() + 30
    while time.time() < deadline and not health(port, timeout=0.5):
        time.sleep(0.1)
    if not health(port):
        print("  The server didn't start. See the messages above.", flush=True)
        return 1
    print(flush=True)
    print(f"  Algorithm Study is running at {url}", flush=True)
    print(f"  Your progress is saved in {db_file}", flush=True)
    print("  Keep this window open while you study. Close it (or press Ctrl+C) to quit.", flush=True)
    print(flush=True)
    if not args.no_browser:
        open_browser(url)

    # 5. Serve until asked to stop.
    stop = threading.Event()
    stopped = threading.Event()

    def request_stop(*_):
        stop.set()

    for name in ("SIGINT", "SIGTERM", "SIGBREAK", "SIGHUP"):
        if hasattr(signal, name):
            try:
                signal.signal(getattr(signal, name), request_stop)
            except (ValueError, OSError):
                pass
    if os.name == "nt":                                   # closing the console window / logoff / shutdown
        import ctypes

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint)
        def console_handler(_event):
            stop.set()
            stopped.wait(4)                               # Windows allows ~5 s before ending the process
            return True
        ctypes.windll.kernel32.SetConsoleCtrlHandler(console_handler, True)
        run._console_handler = console_handler            # keep a reference so it isn't collected

    while not stop.wait(0.5):
        if not thread.is_alive():
            break

    # 6. Clean shutdown: finish in-flight requests, close sockets, checkpoint the database.
    print("  Stopping Algorithm Study...", flush=True)
    try:
        server.task_dispatcher.shutdown(timeout=3)
        wasyncore.close_all(server._map)
    except Exception:
        pass
    thread.join(3)
    checkpoint(db_file)
    stopped.set()
    print("  Stopped. Your progress is saved.", flush=True)
    return 0


def main():
    try:
        code = run(sys.argv[1:])
    except Exception:
        traceback.print_exc()
        if FROZEN and sys.stdin and sys.stdin.isatty():
            input("\n  Algorithm Study hit an error (details above). Press Enter to close this window.")
        code = 1
    sys.exit(code)


if __name__ == "__main__":
    main()
