"""Big-O Trainer - local study app for algorithm analysis, T(n) derivation and pseudocode.

Run:  python app.py      then open http://127.0.0.1:5000   (no sign-in; data in instance/trainer.db)
"""
from __future__ import annotations

import logging
import os
import re
import secrets
import sqlite3
import uuid
from collections import defaultdict, deque

from flask import Flask, abort, g, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

import config
import db
import profile as local_profile
from engine import generator, grading, mockexam, proofs, stats, tn, tnmath
from engine.catalog import (COMPLEXITY_TOPICS, COMPLEXITY_TYPES, LEVELS, PROOF_LEVELS, PROOF_TOPICS, PROOF_TYPES,
                            PSEUDO_TOPICS, PSEUDO_TYPES, SESSION_TOPICS, TN_LEVELS, TN_TOPICS, TOPICS, TRACK_LABELS, TYPES)

ANALYSIS_METHOD = [
    "Identify the basic operations.",
    "Determine how often each section executes.",
    "Determine whether sections are sequential (add) or nested (multiply).",
    "Write an approximate T(n).",
    "Simplify: drop constants and lower-order terms.",
    "State the appropriate asymptotic bound (O, Θ, or Ω).",
]
PSEUDO_METHOD = [
    "Identify the inputs.",
    "Identify the required output.",
    "Determine what information must be tracked.",
    "Decide whether iteration, selection, or recursion is needed.",
    "Write the smallest correct sequence of steps.",
    "Trace the algorithm with a small example.",
    "Analyze its complexity.",
]


PROOF_METHOD = [
    "Decide whether the claim is true. Intuition (a table, a graph, 'grows slower') can guide you - it is not a proof.",
    "Write the inequality the definition requires (f(n) ≤ c·g(n) for O, c·g(n) ≤ f(n) for Ω, both for Θ).",
    "Choose c > 0 - any valid value, not necessarily the smallest.",
    "Choose n₀ > 0 so the inequality holds for EVERY n ≥ n₀, not just on a finite range.",
    "Justify the inequality algebraically for all n ≥ n₀.",
    "For a false claim, show that no fixed c can work (e.g. f(n)/g(n) grows without bound).",
]
PROOF_KINDS = {"proof", "proof_fill"}                 # graded by engine.proofs
PROOF_PARTS = {"proof_debug", "proof_limit"}          # multiple-choice parts, graded by engine.grading


def _dev_secret_key():
    """Development only: a random key generated once and kept in instance/ (never committed)."""
    path = os.path.join(db.data_dir(), "secret_key")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(secrets.token_hex(32))
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    with open(path) as f:
        return f.read().strip()


CONTEXTS = {"free", "practice", "adaptive", "review", "generated", "test"}
TN_METHOD = [
    "List every statement, splitting each for-loop header into init, condition and update.",
    "Write the cost of each row under the counting model.",
    "Count how many times each row executes (loop conditions run iterations + 1 times).",
    "Build T(n) = Σ cost × executions.",
    "Simplify T(n) into a sum of distinct terms.",
    "Keep the dominant term, drop its constant: that's the Θ class.",
]
SESSION_MODES = {"practice", "adaptive", "review", "test"}

# Header: only the basic functions. Learn and Practice group their pages under a second row of tabs.
NAV = [("/", "Dashboard"), ("/learn", "Learn"), ("/practice", "Practice"), ("/review", "Review"), ("/progress", "Progress")]
SUBNAV = {
    "/learn": [("/learn", "Big O & pseudocode"), ("/learn/tn", "T(n) analysis"), ("/learn/proofs", "Complexity proofs"),
               ("/visualizer", "Growth visualizer"), ("/compare", "Compare algorithms")],
    "/practice": [("/practice", "Practice tests"), ("/complexity", "Complexity"), ("/tn", "T(n) Analysis"),
                  ("/pseudocode", "Pseudocode Lab"), ("/proofs", "Proofs"), ("/proofs/sandbox", "Proof sandbox"),
                  ("/mock", "Mock exam"), ("/adaptive", "Adaptive"), ("/generator", "Generator")],
}
SECTION_OF = {href: section for section, items in SUBNAV.items() for href, _ in items}
SECTION_OF["/tn/reference"] = "/learn"


def nav_section(path):
    """Which main tab a page belongs to (exercise pages count as Practice)."""
    if path.startswith(("/exercise/", "/mock/")):
        return "/practice"
    return SECTION_OF.get(path.rstrip("/") or "/", path if path in dict(NAV) else None)
DIFFICULTIES = {"beginner", "intermediate", "advanced", "mixed"}
ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,80}$")

CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; "
       "form-action 'self'; frame-ancestors 'none'")


def create_app(db_path=None, env=None):
    """Application factory. `db_path` is the SQLite file to use (default: instance/trainer.db)."""
    cfg = config.load(env)
    app = Flask(__name__)
    app.config.from_object(cfg)
    app.json.ensure_ascii = False
    db.configure(db_path or cfg.BIGO_DB)
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = _dev_secret_key()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    db.init_db()
    app.logger.info("Big-O Trainer started (%s, %s)", cfg.ENV_NAME, db.describe())

    app.before_request(local_profile.load)

    @app.get("/healthz")
    def health():
        """Liveness check for the platform (does not wake a scaled-to-zero database)."""
        return {"ok": True, "app": "bigo-trainer"}

    @app.get("/healthz/db")
    def health_db():
        db.ping()
        return {"ok": True, "database": "reachable"}

    @app.after_request
    def security_headers(resp):
        h = resp.headers
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("Referrer-Policy", "same-origin")
        h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        h.setdefault("Content-Security-Policy", CSP)
        if request.path.startswith("/api/"):
            h.setdefault("Cache-Control", "no-store")
        return resp

    # ------------------------------------------------------------------ request validation helpers
    def _body():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            abort(400, description="Expected a JSON object.")
        return body

    def _int(value, default, lo, hi):
        try:
            v = int(value)
        except (TypeError, ValueError):
            return default
        return max(lo, min(hi, v))

    def _ident(value):
        return value if isinstance(value, str) and ID_RE.match(value) else None

    @app.context_processor
    def inject():
        return {"TOPICS": TOPICS, "TYPES": TYPES, "LEVELS": LEVELS, "ANALYSIS_METHOD": ANALYSIS_METHOD,
                "PSEUDO_METHOD": PSEUDO_METHOD, "SESSION_TOPICS": SESSION_TOPICS,
                "COMPLEXITY_TYPES": COMPLEXITY_TYPES, "PSEUDO_TYPES": PSEUDO_TYPES,
                "COMPLEXITY_TOPICS": COMPLEXITY_TOPICS, "PSEUDO_TOPICS": PSEUDO_TOPICS,
                "TN_TOPICS": TN_TOPICS, "TN_LEVELS": TN_LEVELS, "TN_MODEL": tn.MODEL_RULES, "TRACK_LABELS": TRACK_LABELS,
                "FAMILIES": generator.FAMILIES, "NAV": NAV, "SUBNAV": SUBNAV,
                "PROOF_TOPICS": PROOF_TOPICS, "PROOF_LEVELS": PROOF_LEVELS, "PROOF_TYPES": PROOF_TYPES,
                "NAV_SECTION": nav_section(request.path)}

    # ------------------------------------------------------------------ pages
    @app.route("/")
    def dashboard():
        ts = stats.track_stats()
        mistakes = db.list_mistakes()
        open_m = sum(1 for m in mistakes if m["status"] == "open")
        return render_template("dashboard.html", ts=ts, open_mistakes=open_m, total_mistakes=len(mistakes),
                               weak=[t for t in stats.topic_stats() if t["accuracy"] is not None][:3])

    @app.route("/complexity")
    def complexity_page():
        return render_template("browse.html", track="complexity", types=COMPLEXITY_TYPES, topics=COMPLEXITY_TOPICS,
                               heading="Complexity Practice")

    @app.route("/tn")
    def tn_page():
        return render_template("tn_browse.html", stats=stats.tn_stats())

    @app.route("/learn/tn")
    @app.route("/tn/reference")
    def tn_reference_page():
        return render_template("tn_reference.html")

    @app.route("/pseudocode")
    def pseudocode_page():
        return render_template("browse.html", track="pseudocode", types=PSEUDO_TYPES, topics=PSEUDO_TOPICS,
                               heading="Pseudocode Lab")

    @app.route("/exercise/<ex_id>")
    def exercise_page(ex_id):
        ex = _ex_or_404(ex_id)
        ctx = request.args.get("ctx", "free")
        return render_template("exercise.html", ex_id=ex_id, ex_title=ex["title"], track=ex["track"],
                               context=ctx if ctx in CONTEXTS else "free",
                               back=({"complexity": ("/complexity", "Complexity Practice"),
                                      "pseudocode": ("/pseudocode", "Pseudocode Lab"),
                                      "tn": ("/tn", "T(n) Analysis"),
                                      "proofs": ("/proofs", "Proofs")}).get(ex["track"], ("/", "Dashboard")))

    @app.route("/proofs")
    def proofs_page():
        return render_template("browse.html", track="proofs", types=PROOF_TYPES, topics=PROOF_TOPICS,
                               heading="Complexity Proofs", levels=PROOF_LEVELS, mastery=stats.proof_mastery())

    @app.route("/proofs/sandbox")
    def proof_sandbox_page():
        return render_template("proof_sandbox.html")

    @app.route("/learn/proofs")
    def proofs_learn_page():
        return render_template("proofs_learn.html")

    @app.route("/mock")
    @app.route("/mock/<exam_id>")
    def mock_page(exam_id=None):
        if exam_id is not None and not (_ident(exam_id) and db.get_mock_exam(exam_id)):
            abort(404, description="mock exam not found")
        return render_template("mock.html", exam_id=exam_id, history=db.list_mock_exams(10), categories=mockexam.CATEGORIES)

    @app.route("/practice")
    def practice_page():
        return render_template("practice.html", mode="test")

    @app.route("/adaptive")
    def adaptive_page():
        return render_template("practice.html", mode="adaptive", weak=stats.weak_topic_table())

    @app.route("/review")
    def review_page():
        return render_template("review.html")

    @app.route("/progress")
    def progress_page():
        return render_template("progress.html", ts=stats.track_stats(), topics=stats.topic_stats(), tnst=stats.tn_stats(),
                               types=stats.type_stats(), sessions=db.recent_sessions(12), proof_mastery=stats.proof_mastery(),
                               mock_exams=db.list_mock_exams(10),
                               mistakes=db.list_mistakes())

    @app.route("/learn")
    def learn_page():
        return render_template("learn.html")

    @app.route("/visualizer")
    def visualizer_page():
        return render_template("visualizer.html")

    @app.route("/compare")
    def compare_page():
        exercises = db.list_exercises(track="complexity", type_="compare")
        return render_template("compare.html", exercises=exercises)

    @app.route("/generator")
    def generator_page():
        return render_template("generator.html")

    # ------------------------------------------------------------------ API: exercises
    def _ex_or_404(ex_id):
        ex = db.get_exercise(ex_id) if _ident(ex_id) else None
        if not ex:
            abort(404, description="exercise not found")
        return ex

    @app.get("/api/exercises")
    def api_exercises():
        rows = db.list_exercises(track=request.args.get("track"), type_=request.args.get("type"),
                                 topic=request.args.get("topic"),
                                 level=_int(request.args.get("level"), None, 1, 6) if request.args.get("level") else None)
        status = db.exercise_status_map()
        for r in rows:
            r["status"] = status.get(r["id"], "unseen")
            r["type_label"] = TYPES.get(r["type"], r["type"])
            r["topic_label"] = TOPICS.get(r["topic"], r["topic"])
        return jsonify(rows)

    @app.get("/api/exercise/<ex_id>")
    def api_exercise(ex_id):
        ex = _ex_or_404(ex_id)
        if ex["type"] == "tn":
            view = {k: ex.get(k) for k in ("id", "track", "type", "topic", "level", "difficulty", "title", "prompt", "note")}
            view.pop("note")
            view["hint_count"] = len(ex.get("hints", []))
            view.update(tn.public_view(ex))
            view["level_label"] = TN_LEVELS.get(ex["level"], "")
            view["method"] = TN_METHOD
            view["provable"] = proofs.tn_provable(ex)
        elif ex["type"] in PROOF_KINDS:
            view = proofs.public_view(ex)
            view["level_label"] = PROOF_LEVELS.get(ex["level"], "")
            view["method"] = PROOF_METHOD
        else:
            view = grading.public_view(ex)
            view["level_label"] = (PROOF_LEVELS if ex["track"] == "proofs" else LEVELS).get(ex["level"], "")
            view["method"] = (PROOF_METHOD if ex["track"] == "proofs" else
                              ANALYSIS_METHOD if ex["track"] == "complexity" or ex["type"] == "to_complexity" else PSEUDO_METHOD)
        view["type_label"] = TYPES.get(ex["type"], ex["type"])
        view["topic_label"] = TOPICS.get(ex["topic"], ex["topic"])
        if ex["type"] == "to_complexity":
            view["my_solution"] = db.latest_user_solution(ex["source"])
        m = db.mistake_detail(ex_id)
        view["mistake_status"] = m["status"] if m else None
        return jsonify(view)

    @app.post("/api/exercise/<ex_id>/hint")
    def api_hint(ex_id):
        ex = _ex_or_404(ex_id)
        n = _int(_body().get("n", 1), 0, 0, 99)
        hints = ex.get("hints", [])
        if not 1 <= n <= len(hints):
            abort(400, description="no such hint")
        return jsonify({"n": n, "total": len(hints), "hint": hints[n - 1]})

    @app.post("/api/exercise/<ex_id>/check_part")
    def api_check_part(ex_id):
        ex = _ex_or_404(ex_id)
        body = _body()
        if "parts" not in ex:
            abort(400, description="this exercise has no parts")
        try:
            res = grading.check_part(ex, body.get("part"), body.get("value"))
        except (KeyError, TypeError, ValueError):
            abort(400, description="unknown part")
        return jsonify(res)

    @app.post("/api/tn/preview")
    def api_tn_preview():
        """Show how an expression is read (safe parser; nothing is evaluated)."""
        body = _body()
        variables = [v for v in (body.get("vars") or ["n"]) if v in ("n", "m", "k", "i", "j")] or ["n"]
        try:
            parsed = tnmath.parse(str(body.get("text", ""))[:400], tuple(variables), allow_wrapper=True)
        except tnmath.ParseError as e:
            return jsonify({"ok": False, "error": str(e)})
        text = tnmath.pretty(parsed.expr)
        if parsed.wrapper:
            text = {"theta": "Θ", "O": "O", "omega": "Ω"}[parsed.wrapper] + "(" + text + ")"
        return jsonify({"ok": True, "pretty": text})

    @app.post("/api/exercise/<ex_id>/tn_step")
    def api_tn_step(ex_id):
        """Check one step of guided T(n) derivation."""
        ex = _ex_or_404(ex_id)
        if ex["type"] != "tn":
            abort(400, description="not a T(n) exercise")
        body = _body()
        value = body.get("value")
        try:
            res = tn.check_step(ex, str(body.get("step", "")), str(value)[:400] if value is not None else "",
                                reveal=body.get("reveal") is True)
        except KeyError:
            abort(400, description="unknown step")
        return jsonify(res)

    def _question_text(ex):
        if ex["track"] == "proofs":
            claim = proofs.claim_text(ex) if ex["type"] == "proof" else ex.get("claim", "")
            body = ex.get("proof_text") or ex.get("template") or ""
            return f"{ex['title']}\n{ex.get('prompt', '')}\n\n{claim}\n{body}".strip()
        if ex["type"] == "tn":
            return f"{ex['title']}\n{ex.get('assumptions') or ''}\n\n{ex['code']}".strip()
        code = ex.get("code") or ex.get("template") or ex.get("buggy") or ""
        if ex["type"] == "order":
            code = "(ordering exercise)\n" + ex["solution"]
        if ex["type"] == "write":
            code = ""
        if ex.get("formula") and not code:
            code = ex["formula"]
        return f"{ex['title']}\n{ex.get('prompt', '')}\n\n{code}".strip()

    def _explanation(ex):
        if ex["type"] == "tn":
            return tn.explanation_text(ex)
        if ex["type"] in PROOF_KINDS:
            return proofs.explanation_text(ex)
        return "\n".join(ex.get("steps", []))

    @app.post("/api/exercise/<ex_id>/submit")
    def api_submit(ex_id):
        ex = _ex_or_404(ex_id)
        body = _body()
        answer = body.get("answer") or {}
        if not isinstance(answer, dict):
            abort(400, description="answer must be an object")
        try:
            if ex["type"] == "tn":
                result = tn.grade(ex, answer)
            elif ex["type"] == "proof":
                result = proofs.grade_proof(ex, answer)
            elif ex["type"] == "proof_fill":
                result = proofs.grade_fill(ex, answer)
            else:
                result = grading.grade(ex, answer)
        except (TypeError, ValueError, AttributeError, KeyError, IndexError):
            abort(400, description="That answer couldn't be read. Please check every field and try again.")
        if ex["type"] in PROOF_KINDS:
            result["solution"] = proofs.solution_payload(ex)
        if ex["type"] in PROOF_PARTS:
            result["skills"] = proofs.parts_skills(ex, result)
            result["category"] = None if result["correct"] else ("proof_debug" if ex["type"] == "proof_debug" else "limits")
        parts = {"t": result["t_correct"], "theta": result["theta_correct"]} if ex["type"] == "tn" else None
        instance = _ident(body.get("instance_id")) or str(uuid.uuid4())
        hints_used = _int(body.get("hints_used"), 0, 0, 20)
        context = body.get("context") if body.get("context") in CONTEXTS else "free"
        if context == "test" and db.question_attempts(instance):
            abort(400, description="This test question has already been answered.")
        rec = db.record_submission(instance, ex, _ident(body.get("session_id")), context, result["correct"],
                                   hints_used, result.get("answer_text", ""), result.get("correct_text", ""),
                                   _explanation(ex), _question_text(ex), parts=parts, category=result.get("category"))
        skills = result.pop("skills", None)
        if skills:
            db.record_proof_skills(instance, ex["id"], skills)
        result["attempt_no"] = rec["attempt_no"]
        result["instance_id"] = instance
        if result["correct"] and ex["type"] in ("write", "complete", "debug"):
            code = answer.get("code", "")
            db.save_user_solution(ex_id, result.get("assembled") or (code if isinstance(code, str) else ""))
        if context == "test":
            # practice tests give no feedback until the end-of-test report
            return jsonify({"recorded": True, "attempt_no": rec["attempt_no"], "instance_id": instance})
        if ex["type"] == "tn" and result["correct"]:
            result["solution"] = tn.solution_payload(ex)
        # retry-style exercises keep the full solution hidden until correct or explicitly revealed
        locks = ex["track"] == "complexity" or ex["type"] in ("to_complexity", "trace") or ex["type"] in PROOF_PARTS
        result["locked"] = bool(locks or result["correct"])
        if not result["locked"]:
            result.pop("solution", None)
        m = db.mistake_detail(ex_id)
        result["mistake_status"] = m["status"] if m else None
        result.pop("assembled", None) if ex["type"] != "order" else None
        return jsonify(result)

    @app.post("/api/exercise/<ex_id>/reveal")
    def api_reveal(ex_id):
        ex = _ex_or_404(ex_id)
        body = _body()
        instance = _ident(body.get("instance_id")) or str(uuid.uuid4())
        context = body.get("context") if body.get("context") in CONTEXTS else "free"
        is_tn, is_proof = ex["type"] == "tn", ex["type"] in PROOF_KINDS
        mod = tn if is_tn else (proofs if is_proof else grading)
        db.record_reveal(instance, ex, _ident(body.get("session_id")), context, _int(body.get("hints_used"), 0, 0, 20),
                         "", mod.correct_text(ex), _explanation(ex), _question_text(ex))
        return jsonify({"solution": mod.solution_payload(ex), "instance_id": instance})

    @app.get("/api/mistakes")
    def api_mistakes():
        rows = db.list_mistakes(request.args.get("status"), request.args.get("track"))
        for r in rows:
            r["topic_label"] = TOPICS.get(r["topic"], r["topic"])
            r["type_label"] = TYPES.get(r["type"], r["type"])
            r["category_label"] = (proofs.category_label(r.get("category")) if r.get("track") == "proofs"
                                   else tn.category_label(r.get("category")))
        return jsonify(rows)

    @app.get("/api/mistakes/<ex_id>")
    def api_mistake(ex_id):
        d = db.mistake_detail(ex_id) if _ident(ex_id) else None
        if not d:
            abort(404)
        return jsonify(d)

    # ------------------------------------------------------------------ API: sessions
    @app.post("/api/session")
    def api_session_create():
        body = _body()
        mode = body.get("mode") if body.get("mode") in SESSION_MODES else "practice"
        count = _int(body.get("count", 10), 10, 0, 100)
        difficulty = body.get("difficulty") if body.get("difficulty") in DIFFICULTIES else "mixed"
        topic = body.get("topic") if body.get("topic") in SESSION_TOPICS else "mixed"
        cfg = {"count": count, "difficulty": difficulty, "topic": topic,
               "adaptive": mode == "adaptive", "review": mode == "review"}
        # optional narrowing from a track page: subject, catalog topic, exercise type and level
        track = body.get("track") if body.get("track") in TRACK_LABELS else None
        if track:
            cfg["track"] = track
            cfg["topic"] = "mixed"
            if body.get("subtopic") in TOPICS:
                cfg["subtopic"] = body["subtopic"]
            if body.get("type") in TYPES:
                cfg["type"] = body["type"]
            if body.get("level") not in (None, ""):
                cfg["level"] = _int(body.get("level"), 1, 1, 9)
            if body.get("style") in ("course", "general"):
                cfg["style"] = body["style"]
        sid = uuid.uuid4().hex
        db.create_session(sid, mode, cfg)
        pool = stats.build_pool(cfg)
        return jsonify({"id": sid, "config": cfg, "pool_size": len(pool)})

    @app.post("/api/session/<sid>/next")
    def api_session_next(sid):
        s = db.get_session(sid)
        if not s:
            abort(404)
        cfg = s["config"]
        if s["ended_at"] or (cfg["count"] and len(s["served"]) >= cfg["count"]):
            db.end_session(sid)
            return jsonify({"done": True})
        ex_id = stats.pick_next(s)
        if not ex_id:
            db.end_session(sid)
            return jsonify({"done": True, "reason": "No more questions match these settings."})
        s["served"].append(ex_id)
        db.update_served(sid, s["served"])
        return jsonify({"done": False, "exercise_id": ex_id, "index": len(s["served"]), "total": cfg["count"] or None})

    def _summary(sid):
        summary = stats.session_summary(sid)
        if summary["session"]["mode"] == "test":
            summary["review"] = _test_review(sid)
        return summary

    def _test_review(sid):
        """Every question served in a practice test, with the answer given, the correct answer and why."""
        rows = defaultdict(deque)
        for q in db.session_questions(sid):
            rows[q["exercise_id"]].append(q)
        answers = db.session_answers(sid)
        out = []
        for ex_id in db.get_session(sid)["served"]:
            ex = db.get_exercise(ex_id)
            if not ex:
                continue
            q = rows[ex_id].popleft() if rows[ex_id] else None
            answered = bool(q and q["attempts"])
            out.append({"exercise_id": ex_id, "title": ex["title"], "track": TRACK_LABELS.get(ex["track"], ex["track"]),
                        "topic_label": TOPICS.get(ex["topic"], ex["topic"]), "type_label": TYPES.get(ex["type"], ex["type"]),
                        "answered": answered, "correct": bool(answered and q["correct"]),
                        "your_answer": answers.get(q["instance_id"], "") if answered else "",
                        "correct_answer": (tn if ex["type"] == "tn" else proofs if ex["type"] in PROOF_KINDS else grading).correct_text(ex),
                        "explanation": _explanation(ex)})
        return out

    @app.post("/api/session/<sid>/end")
    def api_session_end(sid):
        if not db.get_session(sid):
            abort(404)
        db.end_session(sid)
        return jsonify(_summary(sid))

    @app.get("/api/session/<sid>/summary")
    def api_session_summary(sid):
        if not db.get_session(sid):
            abort(404)
        return jsonify(_summary(sid))

    # ------------------------------------------------------------------ API: stats / generator
    @app.get("/api/stats")
    def api_stats():
        return jsonify({"tracks": stats.track_stats(), "topics": stats.topic_stats(), "types": stats.type_stats(),
                        "weak": stats.weak_topic_table(), "tn": stats.tn_stats()})

    @app.post("/api/generate")
    def api_generate():
        body = _body()
        family = body.get("family", "mixed")
        if family not in generator.FAMILIES:
            abort(400, description="unknown family")
        seed = body.get("seed")
        seed = _int(seed, None, 0, 10 ** 9) if seed not in (None, "") else None
        ex = generator.generate(family, seed)
        stored = stats.store_generated(ex)
        return jsonify({"id": stored["id"], "seed": ex["seed"], "family": ex["family"]})

    # ------------------------------------------------------------------ API: proofs
    def _proof_error(e):
        return jsonify({"ok": False, "error": str(e)})

    @app.post("/api/proofs/investigate")
    def api_proof_investigate():
        """Proof sandbox + visual inequality checker. f, g and constants go through the safe parser only."""
        body = _body()
        rel = body.get("rel") if body.get("rel") in proofs.REL_SYMBOL else "O"
        consts = body.get("consts") if isinstance(body.get("consts"), dict) else None
        if consts:
            consts = {k: str(v)[:40] for k, v in consts.items() if k in ("c", "c1", "c2", "n0")}
        try:
            out = proofs.investigate(str(body.get("f", ""))[:200], str(body.get("g", ""))[:200], rel, consts,
                                     _int(body.get("nmax"), 40, 5, 200))
        except tnmath.ParseError as e:
            return _proof_error(e)
        out["ok"] = True
        return jsonify(out)

    @app.post("/api/proofs/from_tn/<ex_id>")
    def api_proof_from_tn(ex_id):
        """'Prove its complexity': turn a T(n) exercise into a Θ proof exercise (stored like generated challenges)."""
        ex = _ex_or_404(ex_id)
        if ex["type"] != "tn" or not proofs.tn_provable(ex):
            abort(400, description="This T(n) exercise has no single T(n) to prove.")
        try:
            pex = proofs.from_tn(ex)
        except tnmath.ParseError as e:
            abort(400, description=str(e))
        stored = stats.store_generated(pex)
        return jsonify({"id": stored["id"]})

    # ------------------------------------------------------------------ API: mock exams
    def _mock_or_404(exam_id):
        ex = db.get_mock_exam(exam_id) if _ident(exam_id) else None
        if not ex:
            abort(404, description="mock exam not found")
        return ex

    def _mock_view(ex):
        view = {"id": ex["id"], "count": ex["count"], "created_at": ex["created_at"], "submitted": bool(ex["submitted_at"]),
                "questions": [mockexam.public_question(q) for q in ex["questions"]], "answers": ex["answers"],
                "flags": ex["flags"], "categories": mockexam.CATEGORIES}
        if ex["submitted_at"]:
            view["results"] = ex["results"]                   # answers and model solutions only after submission
        return view

    @app.post("/api/mock")
    def api_mock_create():
        body = _body()
        exam = generator.mock_exam(_int(body.get("count"), 12, 4, 24))
        exam_id = uuid.uuid4().hex
        db.create_mock_exam(exam_id, exam)
        return jsonify({"id": exam_id})

    @app.get("/api/mock")
    def api_mock_list():
        return jsonify(db.list_mock_exams(20))

    @app.get("/api/mock/<exam_id>")
    def api_mock_get(exam_id):
        return jsonify(_mock_view(_mock_or_404(exam_id)))

    @app.post("/api/mock/<exam_id>/answer")
    def api_mock_answer(exam_id):
        ex = _mock_or_404(exam_id)
        body = _body()
        qid = body.get("qid")
        if qid not in {q["qid"] for q in ex["questions"]}:
            abort(400, description="unknown question")
        answer = body.get("answer")
        if answer is not None:
            if not isinstance(answer, dict) or len(answer) > 12:
                abort(400, description="answer must be an object")
            answer = {str(k)[:20]: str(v)[:8000] for k, v in answer.items() if isinstance(v, (str, int, float))}
        flagged = body.get("flagged") if isinstance(body.get("flagged"), bool) else None
        if not db.save_mock_answer(exam_id, qid, answer, flagged):
            abort(400, description="This exam has already been submitted.")
        return jsonify({"ok": True})

    @app.post("/api/mock/<exam_id>/submit")
    def api_mock_submit(exam_id):
        ex = _mock_or_404(exam_id)
        if not ex["submitted_at"]:
            results = mockexam.grade_exam({"questions": ex["questions"]}, ex["answers"])
            db.finish_mock_exam(exam_id, results)
        return jsonify(_mock_view(_mock_or_404(exam_id)))

    @app.post("/api/reset")
    def api_reset():
        body = _body()
        if body.get("confirm") != "RESET":
            abort(400, description="confirmation required")
        db.reset_progress()
        return jsonify({"ok": True})

    # ------------------------------------------------------------------ errors (never leak internals)
    MESSAGES = {400: "The request couldn't be processed.", 401: "Please log in.", 403: "You don't have access to that.",
                404: "That page doesn't exist.", 405: "That action isn't allowed here.",
                413: "That submission is too large.", 415: "Unsupported request format.",
                500: "Something went wrong on our side.", 503: "The service is temporarily unavailable."}

    def _error(code, description=None):
        msg = description or MESSAGES.get(code, "Error")
        if request.path.startswith("/api/"):
            return jsonify({"error": msg}), code
        return render_template("error.html", code=code, message=msg), code

    @app.errorhandler(HTTPException)
    def http_error(e):
        desc = e.description if e.code in (400, 404) and e.description and not e.description.startswith(("The ", "Bad ")) else None
        return _error(e.code or 500, desc)

    @app.errorhandler(PermissionError)
    def forbidden(e):
        return _error(403)

    @app.errorhandler(db.DatabaseError)
    def db_unavailable(e):
        app.logger.error("database unavailable: %s", type(e.__cause__).__name__ if e.__cause__ else e)
        return _error(503, "The database is temporarily unavailable. Please try again in a moment.")

    @app.errorhandler(Exception)
    def unexpected(e):
        if _is_db_error(e):
            app.logger.exception("database error")
            return _error(503, "The database is temporarily unavailable. Please try again in a moment.")
        app.logger.exception("unhandled error on %s %s", request.method, request.path)
        return _error(500)

    return app


def _is_db_error(e):
    return isinstance(e, sqlite3.Error)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    application = create_app(env=os.environ.get("APP_ENV", "development"))
    print(f"\n  Big-O Trainer running at  http://127.0.0.1:{port}\n  (press Ctrl+C to stop)\n")
    application.run(host="127.0.0.1", port=port, debug=False)
