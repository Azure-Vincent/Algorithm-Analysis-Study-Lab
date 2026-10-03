"""Smoke test for the packaged executable (or `python launcher.py`).

    python tests/smoke_exe.py dist/AlgorithmStudy.exe        # Windows
    python tests/smoke_exe.py dist/AlgorithmStudy            # macOS / Linux
    python tests/smoke_exe.py launcher.py                    # from source

Starts the app with a throwaway data folder, checks pages/assets/grading (including the
pseudocode sandbox, which re-runs the executable), checks it listens on 127.0.0.1 only,
stops it, starts it again and confirms the saved progress is still there.
Uses only the standard library.
"""
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
target = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dist", "AlgorithmStudy"))
fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg, flush=True)
    if not cond:
        fails.append(msg)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


PORT = free_port()
BASE = f"http://127.0.0.1:{PORT}"


def get(path, timeout=10):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return r.status, r.read()


def post(path, body, timeout=60):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def start(data_dir, log):
    cmd = [sys.executable, target] if target.endswith(".py") else [target]
    env = {k: v for k, v in os.environ.items() if k not in ("BIGO_DB", "PORT")}
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    proc = subprocess.Popen(cmd + ["--no-browser", "--port", str(PORT), "--data-dir", data_dir],
                            cwd=tempfile.gettempdir(), env=env, stdout=log, stderr=subprocess.STDOUT,
                            creationflags=flags)
    t0 = time.time()
    while time.time() - t0 < 90:
        try:
            if json.loads(get("/healthz", 1)[1]).get("app") == "bigo-trainer":
                return proc, time.time() - t0
        except Exception:
            time.sleep(0.2)
        if proc.poll() is not None:
            break
    return proc, None


def stop(proc):
    if os.name == "nt":
        proc.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        proc.send_signal(signal.SIGINT)
    try:
        return proc.wait(20)
    except subprocess.TimeoutExpired:
        proc.kill()
        return None


def listening_addresses():
    """Local addresses with our port in LISTEN state (Linux /proc or netstat elsewhere)."""
    addrs = set()
    if os.path.exists("/proc/net/tcp"):
        for fn in ("/proc/net/tcp", "/proc/net/tcp6"):
            if not os.path.exists(fn):
                continue
            for line in open(fn).read().splitlines()[1:]:
                local, st = line.split()[1], line.split()[3]
                ip, port = local.split(":")
                if int(port, 16) == PORT and st == "0A":
                    addrs.add(ip)
    else:
        out = subprocess.run(["netstat", "-an"], capture_output=True, text=True).stdout
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1].endswith(f":{PORT}") and ("LISTEN" in line.upper()):
                addrs.add(parts[1].rsplit(":", 1)[0])
    return addrs


data_dir = tempfile.mkdtemp(prefix="algostudy-smoke-")
proc = None
log_path = os.path.join(data_dir, "app.log")
try:
    with open(log_path, "w") as log:
        proc, secs = start(data_dir, log)
        check(secs is not None, f"app starts and answers /healthz ({secs:.1f}s)" if secs else "app starts")
        if secs is None:
            raise SystemExit
        for path in ["/", "/tn", "/tn/reference", "/complexity", "/pseudocode", "/progress", "/review",
                     "/exercise/tn2-sum", "/static/css/style.css", "/static/js/tn.js", "/static/js/runner.js"]:
            status, body = get(path)
            check(status == 200 and len(body) > 200, f"GET {path}")
        check(b"T(n) Analysis" in get("/")[1], "dashboard template renders")
        n = len(json.loads(get("/api/exercises?track=tn")[1]))
        check(n >= 50, f"exercise data loads ({n} T(n) exercises)")

        r = post("/api/exercise/tn4-pairs/submit", {"instance_id": "smoke-1",
                 "answer": {"mode": "direct", "T": {"all": "4n+4"}, "theta": {"all": "n^2"}}})
        check(r["correct"] is False and r["T"]["all"]["category"], "wrong T(n) graded with feedback")
        r = post("/api/exercise/tn4-pairs/submit", {"instance_id": "smoke-1",
                 "answer": {"mode": "direct", "T": {"all": "4n^2+4n+4"}, "theta": {"all": "n^2"}}})
        check(r["correct"] is True, "corrected T(n) accepted")
        t0 = time.time()
        r = post("/api/exercise/pw-count-even/submit", {"answer": {"code":
                 "procedure CountEven(numbers)\n    count = 0\n    for i = 0 to length(numbers) - 1\n"
                 "        if numbers[i] mod 2 == 0\n            count = count + 1\n    return count"}})
        check(r["correct"] is True, f"pseudocode runs in the sandbox ({time.time() - t0:.1f}s)")
        r = post("/api/exercise/pw-count-even/submit", {"answer": {"code": "procedure CountEven(numbers)\n    while true\n        x = 1"}})
        check(r["correct"] is False, "runaway pseudocode is stopped")

        addrs = listening_addresses()
        local_only = addrs and all(a in ("0100007F", "127.0.0.1") for a in addrs)
        check(bool(local_only), f"listens on 127.0.0.1 only {sorted(addrs)}")
        code = stop(proc)
        check(code == 0, f"stops cleanly (exit code {code})")
        check(os.path.exists(os.path.join(data_dir, "trainer.db")), "database is in the data folder")

        proc, secs = start(data_dir, log)
        check(secs is not None, "app starts again")
        st = json.loads(get("/api/stats")[1])["tn"]["overall"]
        ms = json.loads(get("/api/mistakes?track=tn")[1])
        check(st["answered"] >= 1 and any(m["exercise_id"] == "tn4-pairs" for m in ms),
              "progress and mistakes persisted across restart")
        stop(proc)
finally:
    if proc is not None and proc.poll() is None:
        stop(proc)
    if fails:
        print("\n--- app output ---\n" + open(log_path, errors="replace").read())
    shutil.rmtree(data_dir, ignore_errors=True)

print("\n" + ("\n".join("FAILED: " + f for f in fails) if fails else "SMOKE TEST PASSED"))
sys.exit(1 if fails else 0)
