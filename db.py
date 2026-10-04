"""Database layer (SQLite): schema, migrations, seeding, and all progress queries.

Everything is stored in one SQLite file (instance/trainer.db by default; override with BIGO_DB).
Every query uses ? placeholders and bound parameters - no input is ever formatted into SQL.

The app runs locally without sign-in. Progress rows still carry a user_id that points at a single
local profile (see local_profile_id), which keeps databases from earlier versions - including ones
that had accounts - working unchanged.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime

SEED_VERSION = "2026.10.1"
SCHEMA_VERSION = 4
MASTERY_STREAK = 3
PROGRESS_TABLES = ("questions", "attempts", "mistakes", "sessions", "user_solutions")
_PROJECT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.join(_PROJECT, "instance", "trainer.db")
LOCAL_EMAIL = "local@localhost"


class DatabaseError(Exception):
    """Raised when the database file can't be opened; rendered as a friendly 503 page."""


class _Config:
    path = os.path.abspath(os.environ.get("BIGO_DB") or DEFAULT_PATH)


_local = threading.local()


def configure(path):
    """Point the app at a database file (used by create_app and the tests)."""
    close_all()
    if path and path.startswith("sqlite:///"):
        path = path[len("sqlite:///"):]
    _Config.path = os.path.abspath(path or os.environ.get("BIGO_DB") or DEFAULT_PATH)


def sqlite_path():
    return _Config.path


def data_dir():
    """Directory for local runtime files (the database and the secret key)."""
    return os.path.dirname(_Config.path)


def describe():
    return "SQLite (" + os.path.basename(_Config.path) + ")"


def conn():
    """One connection per thread, reopened if the configured path changes."""
    c = getattr(_local, "conn", None)
    if c is not None and getattr(_local, "path", None) == _Config.path:
        return c
    try:
        os.makedirs(os.path.dirname(_Config.path) or ".", exist_ok=True)
        c = sqlite3.connect(_Config.path, check_same_thread=False, timeout=15)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA busy_timeout=15000")
        c.execute("PRAGMA foreign_keys=ON")
    except (sqlite3.Error, OSError) as e:
        raise DatabaseError("database unavailable") from e
    _local.conn, _local.path = c, _Config.path
    return c


def close_all():
    c = getattr(_local, "conn", None)
    if c is not None:
        try:
            c.close()
        except sqlite3.Error:
            pass
    _local.conn = None


def ping():
    conn().execute("SELECT 1").fetchone()
    return True


def now():
    return datetime.now().isoformat(timespec="seconds")


def uid():
    """Id of the local profile all progress belongs to (set per request by profile.load)."""
    from flask import g, has_app_context
    user_id = getattr(g, "user_id", None) if has_app_context() else None
    return user_id if user_id is not None else local_profile_id()


# ============================================================================ schema & migrations
SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL, created_at TEXT NOT NULL, last_login_at TEXT
);
CREATE TABLE IF NOT EXISTS exercises (
    id TEXT PRIMARY KEY, track TEXT NOT NULL, type TEXT NOT NULL, topic TEXT NOT NULL, level INTEGER NOT NULL,
    difficulty TEXT NOT NULL, title TEXT NOT NULL, tags TEXT, source TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT
);
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    mode TEXT, config TEXT, served TEXT, created_at TEXT, ended_at TEXT
);
CREATE TABLE IF NOT EXISTS questions (
    instance_id TEXT PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exercise_id TEXT NOT NULL, track TEXT, topic TEXT, type TEXT, difficulty TEXT, session_id TEXT, context TEXT,
    attempts INTEGER DEFAULT 0, hints_used INTEGER DEFAULT 0, correct INTEGER DEFAULT 0,
    first_try_correct INTEGER DEFAULT 0, revealed INTEGER DEFAULT 0, started_at TEXT, updated_at TEXT,
    t_first INTEGER, theta_first INTEGER, t_correct INTEGER DEFAULT 0, theta_correct INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    instance_id TEXT, exercise_id TEXT NOT NULL, session_id TEXT, context TEXT,
    attempt_no INTEGER, correct INTEGER, hints_used INTEGER, revealed INTEGER, answer_text TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS mistakes (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, exercise_id TEXT NOT NULL,
    question TEXT, my_answer TEXT, correct_answer TEXT, explanation TEXT,
    topic TEXT, track TEXT, type TEXT, difficulty TEXT, attempts INTEGER, hints_used INTEGER,
    times_missed INTEGER DEFAULT 0, first_missed_at TEXT, last_missed_at TEXT, last_attempted_at TEXT,
    status TEXT DEFAULT 'open', correct_streak INTEGER DEFAULT 0, retry_count INTEGER DEFAULT 0,
    retry_correct INTEGER DEFAULT 0, category TEXT,
    UNIQUE (user_id, exercise_id)
);
CREATE TABLE IF NOT EXISTS user_solutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exercise_id TEXT NOT NULL, code TEXT, created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_q_user ON questions(user_id, exercise_id);
CREATE INDEX IF NOT EXISTS idx_q_sess ON questions(session_id);
CREATE INDEX IF NOT EXISTS idx_a_user ON attempts(user_id, exercise_id);
CREATE INDEX IF NOT EXISTS idx_s_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sol_user ON user_solutions(user_id, exercise_id);
"""

# columns added after a table first shipped: (table, column, definition)
ADDED_COLUMNS = [
    ("questions", "t_first", "INTEGER"),
    ("questions", "theta_first", "INTEGER"),
    ("questions", "t_correct", "INTEGER DEFAULT 0"),
    ("questions", "theta_correct", "INTEGER DEFAULT 0"),
    ("mistakes", "category", "TEXT"),
]


def _sqlite_tables(c):
    return {r["name"] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _sqlite_columns(c, table):
    return {r["name"] for r in c.execute(f"PRAGMA table_info({table})")}


def _migrate_sqlite_legacy(c):
    """Schema v1 (single-user, no accounts) → v2+. Old rows keep user_id NULL and are
    handed to the first account that signs up."""
    tables = _sqlite_tables(c)
    if "mistakes" in tables and "user_id" not in _sqlite_columns(c, "mistakes"):
        c.execute("ALTER TABLE mistakes RENAME TO mistakes_legacy")
    for t in ("questions", "attempts", "sessions", "user_solutions"):
        if t in tables and "user_id" not in _sqlite_columns(c, t):
            c.execute(f"ALTER TABLE {t} ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE")


def init_db(force_reseed=False):
    """Create or migrate the schema and seed reference data. Idempotent and safe to run on
    every start: progress is never modified or deleted."""
    c = conn()
    with c:
        _migrate_sqlite_legacy(c)
    c.executescript(SCHEMA)
    c.commit()
    if "mistakes_legacy" in _sqlite_tables(c):
        with c:
            cols = ", ".join(sorted(_sqlite_columns(c, "mistakes_legacy")))
            c.execute(f"INSERT OR IGNORE INTO mistakes({cols}) SELECT {cols} FROM mistakes_legacy")
            c.execute("DROP TABLE mistakes_legacy")
    with c:
        for table, column, definition in ADDED_COLUMNS:
            if column not in _sqlite_columns(c, table):
                c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        c.execute("DROP TABLE IF EXISTS login_failures")     # left over from the sign-in version
    _set_meta("schema_version", str(SCHEMA_VERSION))
    local_profile_id()
    return seed(force_reseed)


def _get_meta(key):
    r = conn().execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return r["value"] if r else None


def _set_meta(key, value):
    c = conn()
    c.execute("INSERT INTO meta(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
    c.commit()


def seed(force=False):
    """Insert/update the built-in exercise bank when its version changes."""
    from data import seed_exercises
    c = conn()
    count = c.execute("SELECT COUNT(*) AS n FROM exercises WHERE source='seed'").fetchone()["n"]
    if not force and _get_meta("seed_version") == SEED_VERSION and count > 0:
        return 0
    exs = seed_exercises()
    with c:
        for ex in exs:
            upsert_exercise(ex, "seed", commit=False)
        ids = [ex["id"] for ex in exs]
        stale = [r["id"] for r in c.execute("SELECT id FROM exercises WHERE source='seed'") if r["id"] not in set(ids)]
        for sid in stale:
            c.execute("DELETE FROM exercises WHERE id=?", (sid,))
        c.execute("INSERT INTO meta(key, value) VALUES ('seed_version', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                  (SEED_VERSION,))
    return len(exs)


# ============================================================================ local profile
def local_profile_id():
    """The single local profile. Databases from the sign-in version keep the first account's
    progress; a fresh database gets a new profile. Rows saved before any profile existed
    (the very first version) are attached to it."""
    c = conn()
    row = c.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
    if row:
        return row["id"]
    with c:
        new_id = c.execute("INSERT INTO users(email, password_hash, created_at) VALUES (?, '!', ?)",
                           (LOCAL_EMAIL, now())).lastrowid
        for t in PROGRESS_TABLES:
            c.execute(f"UPDATE {t} SET user_id=? WHERE user_id IS NULL", (new_id,))
    return new_id


# ============================================================================ exercises (shared reference data)
def upsert_exercise(ex, source, commit=True):
    c = conn()
    c.execute(
        "INSERT INTO exercises(id, track, type, topic, level, difficulty, title, tags, source, payload, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET track=excluded.track, type=excluded.type, "
        "topic=excluded.topic, level=excluded.level, difficulty=excluded.difficulty, title=excluded.title, "
        "tags=excluded.tags, source=excluded.source, payload=excluded.payload",
        (ex["id"], ex["track"], ex["type"], ex["topic"], ex["level"], ex["difficulty"], ex["title"],
         json.dumps(ex.get("tags", [])), source, json.dumps(ex, ensure_ascii=False), now()))
    if commit:
        c.commit()


def get_exercise(ex_id):
    r = conn().execute("SELECT payload FROM exercises WHERE id=?", (ex_id,)).fetchone()
    return json.loads(r["payload"]) if r else None


def list_exercises(track=None, type_=None, topic=None, level=None, source="seed"):
    q = "SELECT id, track, type, topic, level, difficulty, title, tags, source FROM exercises WHERE 1=1"
    args = []
    for col, val in (("track", track), ("type", type_), ("topic", topic), ("level", level), ("source", source)):
        if val not in (None, "", "all"):
            q += f" AND {col}=?"                 # col comes from the fixed tuple above, never from input
            args.append(val)
    q += " ORDER BY level, track, type, id"
    rows = [dict(r) for r in conn().execute(q, args)]
    for r in rows:
        r["tags"] = json.loads(r["tags"] or "[]")
    return rows


def exercise_status_map():
    """exercise_id -> 'solved' | 'missed' | 'mastered' | 'improving' for the current user."""
    u = uid()
    out = {}
    for r in conn().execute("SELECT exercise_id, MAX(correct) AS ok FROM questions WHERE user_id=? AND (attempts > 0 OR revealed = 1) "
                            "GROUP BY exercise_id", (u,)):
        out[r["exercise_id"]] = "solved" if r["ok"] else "missed"
    for r in conn().execute("SELECT exercise_id, status FROM mistakes WHERE user_id=?", (u,)):
        out[r["exercise_id"]] = "missed" if r["status"] == "open" else r["status"]
    return out


# ============================================================================ attempts & outcomes
def ensure_question(instance_id, ex, session_id, context):
    c = conn()
    u = uid()
    if session_id and not c.execute("SELECT 1 AS ok FROM sessions WHERE id=? AND user_id=?", (session_id, u)).fetchone():
        session_id = None                          # never attach work to someone else's session
    c.execute("INSERT INTO questions(instance_id, user_id, exercise_id, track, topic, type, difficulty, session_id, context, started_at, updated_at) "
              "VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(instance_id) DO NOTHING",
              (instance_id, u, ex["id"], ex["track"], ex["topic"], ex["type"], ex["difficulty"], session_id, context, now(), now()))
    c.commit()
    row = dict(c.execute("SELECT * FROM questions WHERE instance_id=?", (instance_id,)).fetchone())
    if row["user_id"] != u or row["exercise_id"] != ex["id"]:
        raise PermissionError("question instance belongs to another user or exercise")
    return row


def record_submission(instance_id, ex, session_id, context, correct, hints_used, answer_text, correct_text, explanation,
                      question_text, parts=None, category=None):
    """Record one submission. `parts` (T(n) exercises) = {"t": bool, "theta": bool}, graded independently."""
    c = conn()
    u = uid()
    q = ensure_question(instance_id, ex, session_id, context)
    finished_before = q["correct"] or q["revealed"]
    attempt_no = q["attempts"] + 1
    with c:
        c.execute("INSERT INTO attempts(user_id, instance_id, exercise_id, session_id, context, attempt_no, correct, hints_used, revealed, answer_text, created_at) "
                  "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (u, instance_id, ex["id"], q["session_id"], context, attempt_no, int(correct), hints_used, 0, answer_text, now()))
        if not finished_before:
            first = int(correct) if attempt_no == 1 else q["first_try_correct"]
            c.execute("UPDATE questions SET attempts=?, hints_used=?, correct=?, first_try_correct=?, updated_at=? WHERE instance_id=? AND user_id=?",
                      (attempt_no, max(q["hints_used"], hints_used), int(correct), first, now(), instance_id, u))
            if parts is not None:
                t_ok, th_ok = int(bool(parts.get("t"))), int(bool(parts.get("theta")))
                c.execute("UPDATE questions SET t_first=COALESCE(t_first, ?), theta_first=COALESCE(theta_first, ?), "
                          "t_correct=MAX(COALESCE(t_correct, 0), ?), theta_correct=MAX(COALESCE(theta_correct, 0), ?) "
                          "WHERE instance_id=? AND user_id=?", (t_ok, th_ok, t_ok, th_ok, instance_id, u))
    if finished_before:
        return {"attempt_no": attempt_no, "counted": False}
    if correct:
        _mistake_success(ex, clean=(attempt_no == 1 and hints_used == 0))
    else:
        _mistake_fail(ex, answer_text, correct_text, explanation, question_text, attempt_no, hints_used, category)
    return {"attempt_no": attempt_no, "counted": True}


def record_reveal(instance_id, ex, session_id, context, hints_used, answer_text, correct_text, explanation, question_text):
    c = conn()
    u = uid()
    q = ensure_question(instance_id, ex, session_id, context)
    if q["correct"] or q["revealed"]:
        return
    with c:
        c.execute("UPDATE questions SET revealed=1, hints_used=?, updated_at=? WHERE instance_id=? AND user_id=?",
                  (max(q["hints_used"], hints_used), now(), instance_id, u))
        c.execute("INSERT INTO attempts(user_id, instance_id, exercise_id, session_id, context, attempt_no, correct, hints_used, revealed, answer_text, created_at) "
                  "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (u, instance_id, ex["id"], q["session_id"], context, q["attempts"], 0, hints_used, 1, "(solution revealed)", now()))
    if q["attempts"] == 0:
        _mistake_fail(ex, answer_text or "(revealed the solution without answering)", correct_text, explanation, question_text, 0, hints_used)


def _mistake_fail(ex, my_answer, correct_answer, explanation, question, attempts, hints_used, category=None):
    c = conn()
    u = uid()
    with c:
        c.execute("INSERT INTO mistakes(user_id, exercise_id, question, topic, track, type, difficulty, times_missed, first_missed_at, status, correct_streak) "
                  "VALUES (?,?,?,?,?,?,?,0,?, 'open', 0) ON CONFLICT(user_id, exercise_id) DO NOTHING",
                  (u, ex["id"], question, ex["topic"], ex["track"], ex["type"], ex["difficulty"], now()))
        row = c.execute("SELECT hints_used, times_missed FROM mistakes WHERE user_id=? AND exercise_id=?", (u, ex["id"])).fetchone()
        c.execute("UPDATE mistakes SET question=?, my_answer=?, correct_answer=?, explanation=?, attempts=?, hints_used=?, "
                  "times_missed=times_missed+1, last_missed_at=?, last_attempted_at=?, status='open', correct_streak=0, "
                  "retry_count=retry_count+?, category=COALESCE(?, category) WHERE user_id=? AND exercise_id=?",
                  (question, my_answer, correct_answer, explanation, attempts, max(row["hints_used"] or 0, int(hints_used > 0)),
                   now(), now(), 1 if (row["times_missed"] and attempts <= 1) else 0, category, u, ex["id"]))


def _mistake_success(ex, clean):
    c = conn()
    u = uid()
    row = c.execute("SELECT correct_streak, status FROM mistakes WHERE user_id=? AND exercise_id=?", (u, ex["id"])).fetchone()
    if row is None:
        return
    streak = row["correct_streak"] + 1 if clean else row["correct_streak"]
    status = "mastered" if streak >= MASTERY_STREAK else ("improving" if streak >= 1 else row["status"])
    with c:
        c.execute("UPDATE mistakes SET correct_streak=?, status=?, last_attempted_at=?, retry_count=retry_count+1, "
                  "retry_correct=retry_correct+? WHERE user_id=? AND exercise_id=?",
                  (streak, status, now(), int(clean), u, ex["id"]))


def list_mistakes(status=None, track=None):
    q = "SELECT * FROM mistakes WHERE user_id=?"
    args = [uid()]
    if status and status != "all":
        q += " AND status=?"
        args.append(status)
    if track and track != "all":
        q += " AND track=?"
        args.append(track)
    q += " ORDER BY CASE status WHEN 'open' THEN 0 WHEN 'improving' THEN 1 ELSE 2 END, last_missed_at DESC"
    return [_public(dict(r)) for r in conn().execute(q, args)]


def _public(row):
    row.pop("user_id", None)
    return row


def mistake_detail(ex_id):
    u = uid()
    r = conn().execute("SELECT * FROM mistakes WHERE user_id=? AND exercise_id=?", (u, ex_id)).fetchone()
    if not r:
        return None
    d = _public(dict(r))
    d["history"] = [dict(x) for x in conn().execute(
        "SELECT attempt_no, correct, hints_used, revealed, answer_text, context, created_at FROM attempts "
        "WHERE user_id=? AND exercise_id=? ORDER BY id DESC LIMIT 30", (u, ex_id))]
    return d


def save_user_solution(ex_id, code):
    c = conn()
    c.execute("INSERT INTO user_solutions(user_id, exercise_id, code, created_at) VALUES (?,?,?,?)", (uid(), ex_id, code, now()))
    c.commit()


def latest_user_solution(ex_id):
    r = conn().execute("SELECT code, created_at FROM user_solutions WHERE user_id=? AND exercise_id=? ORDER BY id DESC LIMIT 1",
                       (uid(), ex_id)).fetchone()
    return dict(r) if r else None


# ============================================================================ sessions
def create_session(sid, mode, config):
    c = conn()
    c.execute("INSERT INTO sessions(id, user_id, mode, config, served, created_at) VALUES (?,?,?,?,?,?)",
              (sid, uid(), mode, json.dumps(config), "[]", now()))
    c.commit()


def get_session(sid):
    r = conn().execute("SELECT * FROM sessions WHERE id=? AND user_id=?", (sid, uid())).fetchone()
    if not r:
        return None
    d = _public(dict(r))
    d["config"] = json.loads(d["config"])
    d["served"] = json.loads(d["served"])
    return d


def update_served(sid, served):
    c = conn()
    c.execute("UPDATE sessions SET served=? WHERE id=? AND user_id=?", (json.dumps(served), sid, uid()))
    c.commit()


def end_session(sid):
    c = conn()
    c.execute("UPDATE sessions SET ended_at=COALESCE(ended_at, ?) WHERE id=? AND user_id=?", (now(), sid, uid()))
    c.commit()


def question_attempts(instance_id):
    row = conn().execute("SELECT attempts FROM questions WHERE instance_id=? AND user_id=?", (instance_id, uid())).fetchone()
    return row["attempts"] if row else 0


def session_answers(sid):
    """instance_id -> the last answer submitted for it in this session."""
    out = {}
    for r in conn().execute("SELECT instance_id, answer_text FROM attempts WHERE session_id=? AND user_id=? AND revealed=0 ORDER BY id",
                            (sid, uid())):
        out[r["instance_id"]] = r["answer_text"]
    return out


def session_questions(sid):
    return [dict(r) for r in conn().execute("SELECT * FROM questions WHERE session_id=? AND user_id=? ORDER BY started_at", (sid, uid()))]


def recent_sessions(limit=10):
    out = []
    for r in conn().execute("SELECT * FROM sessions WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (uid(), limit)).fetchall():
        d = _public(dict(r))
        d["config"] = json.loads(d["config"])
        qs = session_questions(d["id"])
        done = [q for q in qs if q["attempts"] or q["revealed"]]
        d["answered"] = len(done)
        d["correct"] = sum(1 for q in done if q["correct"])
        out.append(d)
    return out


# ============================================================================ stats
def answered_questions(track=None):
    q = "SELECT * FROM questions WHERE user_id=? AND (attempts > 0 OR revealed = 1)"
    args = [uid()]
    if track:
        q += " AND track=?"
        args.append(track)
    return [dict(r) for r in conn().execute(q, args)]


def reset_progress():
    """Delete the current user's progress (the account itself is kept)."""
    c = conn()
    u = uid()
    with c:
        for t in PROGRESS_TABLES:
            c.execute(f"DELETE FROM {t} WHERE user_id=?", (u,))
