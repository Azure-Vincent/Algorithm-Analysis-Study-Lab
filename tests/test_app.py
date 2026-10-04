"""End-to-end validation for Big-O Trainer.

Run from the project root:
    python -m unittest discover -s tests -v
Uses only the standard library (plus Flask, already required).
"""
import json
import math
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from data import raw_exercises, seed_exercises  # noqa: E402
from engine import generator, grading  # noqa: E402
from engine.pseudo import run_tests, run_trace, to_plist, Program  # noqa: E402

SEED = seed_exercises()

def fresh_db(name):
    """A brand-new empty SQLite database for one test class."""
    return os.path.join(tempfile.mkdtemp(), name + ".db")


BY_ID = {e["id"]: e for e in SEED}
RAW = {e["id"]: e for e in raw_exercises()}


def of_type(*types):
    return [e for e in SEED if e["type"] in types]


class TestContent(unittest.TestCase):
    def test_bank_sizes(self):
        cx = [e for e in SEED if e["track"] == "complexity"]
        pc = of_type("fill", "order", "complete", "write", "to_complexity")
        self.assertGreaterEqual(len(cx), 75)
        self.assertGreaterEqual(len(pc), 40)
        self.assertGreaterEqual(len(of_type("trace")), 15)
        self.assertGreaterEqual(len(of_type("debug")), 15)
        for lvl in range(1, 7):
            self.assertTrue(any(e["level"] == lvl for e in cx), f"no complexity exercise at level {lvl}")
        for mode in ("identify", "bounds", "analyze", "count", "compare", "cases"):
            self.assertTrue(any(e["type"] == mode for e in cx), mode)

    def test_structural_variety(self):
        codes = [(e["type"], re.sub(r"\s+", " ", e.get("code", ""))) for e in SEED if e["track"] == "complexity" and e.get("code")]
        self.assertEqual(len(codes), len(set(codes)), "duplicate complexity code snippets")

    def test_complexity_answers(self):
        for e in SEED:
            if e["track"] != "complexity" and e["type"] != "to_complexity":
                continue
            with self.subTest(e["id"]):
                self.assertGreaterEqual(len(e["hints"]), 3)
                self.assertTrue(e["steps"])
                for p in e["parts"]:
                    if p["kind"] == "choice":
                        self.assertIn(p["answer"], p["options"])
                        self.assertEqual(len(p["options"]), len(set(p["options"])))
                    elif p["kind"] == "multi":
                        self.assertTrue(set(p["answer"]) <= set(p["options"]))
                    elif p["kind"] == "order":
                        self.assertEqual(sorted(p["answer"]), sorted(p["options"]))
                for h in e.get("highlights", []):
                    for ln in h["lines"]:
                        self.assertTrue(1 <= ln <= len(e["code"].split("\n")))

    def test_bounds_consistency(self):
        from engine.growth import RANK
        for e in of_type("bounds"):
            parts = {p["id"]: p for p in e["parts"]}
            if "T" not in parts or parts["T"]["answer"] not in RANK:
                continue
            th = RANK[parts["T"]["answer"]]
            with self.subTest(e["id"]):
                self.assertTrue(all(RANK[c] >= th for c in parts["O"]["answer"]))
                self.assertTrue(all(RANK[c] <= th for c in parts["W"]["answer"]))
                self.assertIn(parts["T"]["answer"], parts["O"]["answer"])
                self.assertIn(parts["T"]["answer"], parts["W"]["answer"])

    def test_count_simulations(self):
        for ex in RAW.values():
            if ex["type"] != "count":
                continue
            with self.subTest(ex["id"]):
                at = ex["_at"]
                exact = ex["_sim"](**at)
                self.assertEqual(exact, ex["parts"][0]["answer"])
                if ex["_expr_fn"]:
                    self.assertEqual(ex["_expr_fn"](**at), exact)
                    doubled = {k: v * 2 for k, v in at.items()}
                    self.assertEqual(ex["_expr_fn"](**doubled), ex["_sim"](**doubled))


class TestPseudocode(unittest.TestCase):
    def _ok(self, code, ex):
        r = run_tests(code, ex["tests"], ex.get("entry"), ex.get("params"))
        self.assertTrue(r["runnable"], r.get("error"))
        self.assertEqual(r["passed"], r["total"], json.dumps(r["results"], ensure_ascii=False))

    def test_reference_solutions_pass(self):
        for ex in of_type("fill", "order", "complete", "write", "debug"):
            with self.subTest(ex["id"]):
                self._ok(ex["solution"], ex)

    def test_fill_blanks_accept(self):
        for ex in of_type("fill"):
            with self.subTest(ex["id"]):
                filled = ex["template"]
                for i, b in enumerate(ex["blanks"]):
                    filled = filled.replace(f"[[{i}]]", grading.pretty(b["accept"][0]))
                self._ok(filled, ex)
                ans = {"blanks": [grading.pretty(b["accept"][0]) for b in ex["blanks"]]}
                self.assertTrue(grading.grade(ex, ans)["correct"])
                bad = {"blanks": ["zzz"] * len(ex["blanks"])}
                self.assertFalse(grading.grade(ex, bad)["correct"])

    def test_order_grading(self):
        for ex in of_type("order"):
            with self.subTest(ex["id"]):
                n = len(ex["lines"])
                self.assertTrue(grading.grade(ex, {"order": list(range(n))})["correct"])
                self.assertFalse(grading.grade(ex, {"order": list(reversed(range(n)))})["correct"])
                view = grading.public_view(ex)
                self.assertNotEqual([x["id"] for x in view["items"]], list(range(n)))

    def test_complete_assembly(self):
        for ex in of_type("complete"):
            with self.subTest(ex["id"]):
                header, footer, indent = grading.split_template(ex["template"])
                sol = ex["solution"].split("\n")
                hl, fl = header.split("\n"), (footer.split("\n") if footer else [])
                body = sol[len(hl): len(sol) - len(fl)]
                # student writes the body flush-left
                common = min(len(l) - len(l.lstrip()) for l in body if l.strip())
                student = "\n".join(l[common:] for l in body)
                r = grading.grade(ex, {"code": student})
                self.assertTrue(r["correct"], json.dumps(r["tests"], ensure_ascii=False))
                self.assertFalse(grading.grade(ex, {"code": "return 0"})["correct"])

    def test_write_grading_and_rubric(self):
        for ex in of_type("write"):
            with self.subTest(ex["id"]):
                r = grading.grade(ex, {"code": ex["solution"]})
                self.assertTrue(r["correct"])
                missing = [x["label"] for x in r["rubric"] if not x["ok"]]
                self.assertEqual(missing, [], "rubric misses the reference solution")
                self.assertFalse(grading.grade(ex, {"code": ex["starter"] + "return 0"})["correct"])

    def test_debug_bugs_are_real(self):
        for ex in of_type("debug"):
            with self.subTest(ex["id"]):
                r = run_tests(ex["buggy"], ex["tests"], ex.get("entry"), ex.get("params"))
                self.assertLess(r["passed"], r["total"], "buggy code passes every test")
                good = grading.grade(ex, {"line": ex["bug_line_numbers"][0], "code": ex["solution"]})
                self.assertTrue(good["correct"])
                self.assertFalse(grading.grade(ex, {"line": ex["bug_line_numbers"][0], "code": ex["buggy"]})["correct"])

    def test_traces(self):
        for ex in of_type("trace"):
            with self.subTest(ex["id"]):
                self.assertGreater(len(ex["rows"]), 0)
                rows = [[grading.fmt(r[w]) for w in ex["watch"]] for r in ex["rows"]]
                self.assertTrue(grading.grade(ex, {"rows": rows})["correct"])
                rows[0][0] = "999999"
                self.assertFalse(grading.grade(ex, {"rows": rows})["correct"])

    def test_spec_trace_example(self):
        ex = BY_ID["pt-sum"]
        self.assertEqual([r["sum"] for r in ex["rows"]], [5, 7, 15, 18])

    def test_forgiving_syntax(self):
        ex = BY_ID["pw-count-even"]
        variants = [
            "procedure CountEven(numbers)\n    count ← 0\n    for each x in numbers do\n        if x mod 2 = 0 then\n            count++\n        end if\n    end for\n    return count\nend procedure",
            "function countEvens(arr)\n    c := 0\n    for i from 0 to arr.length - 1\n        if arr[i] % 2 == 0:\n            c += 1\n    return c",
            "total = 0\nfor i = 0 to length(numbers) - 1\n    if numbers[i] mod 2 == 0\n        increment total\nreturn total",
        ]
        for v in variants:
            with self.subTest(v[:30]):
                self.assertTrue(grading.grade(ex, {"code": v})["correct"])

    def test_sandbox(self):
        for bad in ["procedure F(A)\n    return A.__class__", "procedure F(A)\n    import os", "procedure F(A)\n    while true\n        x = 1"]:
            r = run_tests(bad, [{"args": [[1]], "expect": 1}])
            self.assertEqual(r["passed"], 0)


class TestGenerator(unittest.TestCase):
    FAMS = ["single", "sequential", "nested", "multivar", "dependent", "conditional", "mixed"]

    def _run_code(self, ex, env):
        src = ex["code"] + "\nreturn count"
        prog = Program(src, params=["n", "m", "k", "A"])
        best = 0
        for sign in (1, -1):
            args = [env["n"], env["m"], env["k"], to_plist([sign] * (env["n"] + 1))]
            best = max(best, prog.call("_main", args))
        return best

    def test_rendering_matches_spec(self):
        env = {"n": 13, "m": 5, "k": 7}
        for fam in self.FAMS:
            for seed in range(25):
                ex = generator.generate(fam, seed)
                with self.subTest(f"{fam}-{seed}"):
                    self.assertEqual(self._run_code(ex, env), generator.simulate(ex["_spec"], env), ex["code"])
                    opts = ex["parts"][0]["options"]
                    self.assertIn(ex["parts"][0]["answer"], opts)
                    self.assertEqual(len(opts), len(set(opts)))
                    self.assertGreaterEqual(len(opts), 3)

    def test_deterministic(self):
        a, b = generator.generate("mixed", 1234), generator.generate("mixed", 1234)
        self.assertEqual(a["code"], b["code"])
        self.assertEqual(a["parts"], b["parts"])

    def test_answers_match_growth(self):
        """The symbolic answer must track exact operation counts (differences cancel constants)."""
        checked = 0
        for fam in self.FAMS:
            for seed in range(40):
                ex = generator.generate(fam, seed)
                blocks = ex["_spec"]
                monos = generator.simplify_sum([generator.block_cost(b) for b in blocks])
                vars_ = sorted({v for m in monos for v in m.t}) or ["n"]
                for var in vars_:
                    base = {"n": 16, "m": 16, "k": 16}

                    def pred(s):
                        env = dict(base, **{var: s})
                        return sum(m.value(env) for m in monos)

                    sc = 4096
                    while sc > 64 and pred(sc) > 3e6:
                        sc //= 2
                    sb, sa = max(4, sc // 8), max(2, sc // 64)

                    def act(s):
                        return generator.simulate(blocks, dict(base, **{var: s}))

                    with self.subTest(f"{fam}-{seed}-{var}"):
                        pa, pb, pc = pred(sa), pred(sb), pred(sc)
                        ta, tb, tc = act(sa), act(sb), act(sc)
                        if pc - pa < 1e-9:
                            self.assertEqual(tc, ta)
                            continue
                        qb = (tb - ta) / (pb - pa)
                        qc = (tc - ta) / (pc - pa)
                        self.assertGreater(qb, 0, ex["code"])
                        ratio = qc / qb
                        self.assertTrue(0.7 <= ratio <= 1.45, f"{ex['parts'][0]['answer']} ratio {ratio:.2f}\n{ex['code']}")
                        checked += 1
        self.assertGreater(checked, 200)


class TestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.db_path = fresh_db("app")
        from app import create_app
        cls.app = create_app(cls.db_path, env="testing")
        cls.client = cls.app.test_client()

    def setUp(self):
        import db
        db.configure(self.db_path)

    def post(self, url, body=None):
        r = self.client.post(url, data=json.dumps(body or {}), content_type="application/json")
        self.assertLess(r.status_code, 400, r.data[:300])
        return r.get_json()

    def test_01_pages_and_assets(self):
        for url in ["/", "/complexity", "/pseudocode", "/practice", "/adaptive", "/review", "/progress", "/learn",
                    "/visualizer", "/compare", "/generator", "/exercise/c2-nested-two", "/exercise/pw-count-even",
                    "/tn", "/tn/reference", "/exercise/tn2-sum"]:
            with self.subTest(url):
                r = self.client.get(url)
                self.assertEqual(r.status_code, 200)
                html = r.get_data(as_text=True)
                for asset in re.findall(r'(?:src|href)="(/static/[^"]+)"', html):
                    self.assertEqual(self.client.get(asset).status_code, 200, asset)
        self.assertEqual(self.client.get("/exercise/nope").status_code, 404)

    def test_02_public_view_hides_answers(self):
        for ex in SEED:
            v = self.client.get(f"/api/exercise/{ex['id']}").get_json()
            blob = json.dumps(v, ensure_ascii=False)
            with self.subTest(ex["id"]):
                self.assertNotIn('"answer":', blob)
                self.assertNotIn('"steps"', blob)
                self.assertNotIn('"solution"', blob)
                if ex["type"] != "tn":   # T(n) rows are the table skeleton (no counts), checked in test_tn
                    self.assertNotIn('"rows"', blob)

    def test_03_submit_every_type(self):
        cases = {
            "c2-nested-two": {"parts": {"answer": "n²"}},
            "cb-quadratic": {"parts": {"O": ["n²", "n³", "2ⁿ"], "T": "n²", "W": ["1", "log n", "n", "n log n", "n²"]}},
            "c2-count-nested": {"parts": {"exact": "16", "expr": "n²", "answer": "n²"}},
            "cf-linear-search": {"parts": {"best": "1", "avg": "n", "worst": "n", "rel": "The worst-case running time is Ω(n)."}},
            "ce-100n-vs-n2": {"parts": {"small": "B (n²)", "cross": "100", "large": "A (100n)"}},
            "ce-order-growth": {"parts": {"order": ["1", "log n", "√n", "n", "n log n", "n²", "n³", "2ⁿ", "n!"]}},
            "pf-count-gt10": {"blanks": ["length(numbers) - 1", "count + 1", "count"]},
            "po-max": {"order": list(range(6))},
            "pc-count-positive": {"code": "for i = 0 to length(numbers) - 1\n    if numbers[i] > 0\n        count = count + 1"},
            "pw-count-even": {"code": BY_ID["pw-count-even"]["solution"]},
            "pd-max": {"line": 4, "code": BY_ID["pd-max"]["solution"]},
            "pt-sum": {"rows": [["0", "5"], ["1", "7"], ["2", "15"], ["3", "18"]]},
            "tc-count-even": {"parts": {"answer": "n"}},
        }
        for ex_id, ans in cases.items():
            with self.subTest(ex_id):
                r = self.post(f"/api/exercise/{ex_id}/submit", {"answer": ans, "context": "free"})
                self.assertTrue(r["correct"], json.dumps(r, ensure_ascii=False)[:800])
                self.assertIn("solution", r)
                self.assertTrue(r["solution"]["steps"])

    def test_04_incorrect_feedback_and_mistakes(self):
        r = self.post("/api/exercise/c2-nested-two/submit", {"answer": {"parts": {"answer": "n"}}, "hints_used": 2})
        self.assertFalse(r["correct"])
        sol = r["solution"]
        self.assertTrue(any("n × n" in s for s in sol["steps"]))
        self.assertTrue(sol["highlights"])
        m = self.client.get("/api/mistakes/c2-nested-two").get_json()
        self.assertEqual(m["status"], "open")
        self.assertIn("O(n)", m["my_answer"])
        self.assertIn("O(n²)", m["correct_answer"])
        self.assertEqual(m["hints_used"], 1)
        self.assertEqual(m["topic"], "nested_loops")
        self.assertTrue(m["explanation"])
        # retry-style exercise keeps solution hidden when wrong
        r2 = self.post("/api/exercise/pw-count-even/submit", {"answer": {"code": "procedure CountEven(numbers)\n    return 0"}})
        self.assertFalse(r2["correct"])
        self.assertNotIn("solution", r2)
        self.assertTrue(r2["rubric"])
        # mastery: three clean correct answers
        for i in range(3):
            self.post("/api/exercise/c2-nested-two/submit", {"answer": {"parts": {"answer": "n²"}}, "context": "review"})
        m = self.client.get("/api/mistakes/c2-nested-two").get_json()
        self.assertEqual(m["status"], "mastered")
        self.assertGreaterEqual(len(m["history"]), 4)

    def test_05_hints_and_reveal(self):
        h = self.post("/api/exercise/c2-triple/hint", {"n": 1})
        self.assertTrue(h["hint"])
        r = self.post("/api/exercise/c2-triple/reveal", {"hints_used": 1})
        self.assertTrue(r["solution"]["steps"])
        self.assertEqual(self.client.get("/api/mistakes/c2-triple").get_json()["status"], "open")
        cp = self.post("/api/exercise/c2-count-nested/check_part", {"part": "exact", "value": "16"})
        self.assertTrue(cp["correct"])

    def test_06_sessions(self):
        for mode, topic, diff in [("practice", "nested", "beginner"), ("practice", "pseudocode", "mixed"), ("adaptive", "mixed", "mixed"),
                                  ("practice", "big_theta", "mixed"), ("practice", "recursion", "advanced")]:
            with self.subTest(f"{mode}-{topic}"):
                s = self.post("/api/session", {"mode": mode, "count": 5, "topic": topic, "difficulty": diff})
                self.assertGreater(s["pool_size"], 0)
                seen = 0
                while True:
                    n = self.post(f"/api/session/{s['id']}/next")
                    if n["done"]:
                        break
                    seen += 1
                    ex = BY_ID.get(n["exercise_id"])
                    ans = {"parts": {"answer": "n"}} if (ex is None or ex["track"] == "complexity") else {"code": "x"}
                    self.post(f"/api/exercise/{n['exercise_id']}/submit", {"answer": ans, "session_id": s["id"], "context": mode, "hints_used": seen % 2})
                self.assertEqual(seen, 5)
                summ = self.client.get(f"/api/session/{s['id']}/summary").get_json()
                self.assertEqual(summ["answered"], 5)
                for key in ("correct", "incorrect", "accuracy", "no_hints", "after_hints", "avg_attempts", "difficult_topics"):
                    self.assertIn(key, summ)
        rv = self.post("/api/session", {"mode": "review", "count": 0})
        self.assertGreater(rv["pool_size"], 0)

    def test_06b_session_from_track_page(self):
        """Sessions started on a track page only serve exercises matching the chosen subject, topic, type and level."""
        for filt in [{"track": "complexity", "subtopic": "nested_loops"}, {"track": "pseudocode", "type": "trace"},
                     {"track": "tn", "subtopic": "tn_log", "level": 6}, {"track": "tn", "difficulty": "beginner"}]:
            with self.subTest(**{k: str(v) for k, v in filt.items()}):
                s = self.post("/api/session", dict(filt, mode="practice", count=6))
                self.assertGreater(s["pool_size"], 0)
                for _ in range(6):
                    n = self.post(f"/api/session/{s['id']}/next")
                    self.assertFalse(n["done"])
                    ex = BY_ID[n["exercise_id"]]
                    self.assertEqual(ex["track"], filt["track"])
                    for key, col in (("subtopic", "topic"), ("type", "type"), ("level", "level"), ("difficulty", "difficulty")):
                        if key in filt:
                            self.assertEqual(ex[col], filt[key])
        # filters only apply with a valid track; an impossible combination yields an empty session, not generated filler
        s = self.post("/api/session", {"mode": "practice", "count": 3, "track": "tn", "subtopic": "nested_loops"})
        self.assertEqual(s["pool_size"], 0)
        self.assertTrue(self.post(f"/api/session/{s['id']}/next")["done"])
        s = self.post("/api/session", {"mode": "practice", "count": 3, "track": "bogus", "subtopic": "tn_log"})
        self.assertNotIn("subtopic", s["config"])

    def test_07_generator_api(self):
        r = self.post("/api/generate", {"family": "nested", "seed": 7})
        v = self.client.get(f"/api/exercise/{r['id']}").get_json()
        self.assertEqual(v["type"], "generated")
        ex = generator.generate("nested", 7)
        res = self.post(f"/api/exercise/{r['id']}/submit", {"answer": {"parts": {"answer": ex["parts"][0]["answer"]}}})
        self.assertTrue(res["correct"])

    def test_08_stats_and_persistence(self):
        st = self.client.get("/api/stats").get_json()
        self.assertGreater(st["tracks"]["complexity"]["answered"], 0)
        self.assertGreater(st["tracks"]["pseudocode"]["answered"], 0)
        self.assertTrue(st["topics"])
        # restart: a fresh app on the same database file sees the same progress
        import db
        db.close_all()
        from app import create_app
        app2 = create_app(self.db_path, env="testing")
        c2 = app2.test_client()
        st2 = c2.get("/api/stats").get_json()
        self.assertEqual(st2["tracks"], st["tracks"])
        self.assertTrue(c2.get("/api/mistakes?status=all").get_json())
        self.assertEqual(c2.get("/progress").status_code, 200)


class TestLocalMode(unittest.TestCase):
    """No sign-in: everything opens directly and belongs to one local profile."""

    def setUp(self):
        import db
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "local.db")
        from app import create_app
        self.app = create_app(self.db_path, env="testing")
        db.configure(self.db_path)

    def test_no_sign_in_pages(self):
        c = self.app.test_client()
        self.assertEqual(c.get("/").status_code, 200)
        self.assertEqual(c.get("/api/exercise/c2-nested-two").status_code, 200)
        for url in ("/login", "/signup", "/account"):
            self.assertEqual(c.get(url).status_code, 404, url)
        self.assertNotIn(b"Log out", c.get("/").data)
        self.assertEqual(c.get("/healthz").status_code, 200)

    def test_single_profile_and_persistence(self):
        import db
        a, b = self.app.test_client(), self.app.test_client()
        a.post("/api/exercise/c2-nested-two/submit", json={"answer": {"parts": {"answer": "n"}}})
        # a second browser sees the same (single) profile's data
        self.assertEqual(b.get("/api/stats").get_json()["tracks"]["complexity"]["answered"], 1)
        self.assertEqual(db.conn().execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"], 1)

    def test_json_required_for_api_posts(self):
        c = self.app.test_client()
        r = c.post("/api/exercise/c2-nested-two/submit", data="answer=1", content_type="application/x-www-form-urlencoded")
        self.assertEqual(r.status_code, 415)
        r = c.post("/api/reset", data='{"confirm": "RESET"}', content_type="text/plain")
        self.assertEqual(r.status_code, 415)

    def test_upgrade_from_accounts_version(self):
        """A database from the sign-in version keeps the first account's progress."""
        import sqlite3
        import db
        path = os.path.join(self.tmp, "accounts.db")
        from app import create_app
        create_app(path, env="testing")
        con = sqlite3.connect(path)
        con.execute("DELETE FROM users")
        con.execute("INSERT INTO users(id, email, password_hash, created_at) VALUES (7, 'me@example.com', 'scrypt:x', 'now')")
        con.execute("INSERT INTO users(id, email, password_hash, created_at) VALUES (9, 'other@example.com', 'scrypt:y', 'now')")
        con.execute("INSERT INTO questions(instance_id, user_id, exercise_id, track, topic, type, difficulty, attempts, correct, first_try_correct) "
                    "VALUES ('q7', 7, 'c2-nested-two', 'complexity', 'nested_loops', 'identify', 'beginner', 1, 1, 1)")
        con.execute("INSERT INTO questions(instance_id, user_id, exercise_id, track, topic, type, difficulty, attempts, correct, first_try_correct) "
                    "VALUES ('q9', 9, 'c2-triple', 'complexity', 'nested_loops', 'identify', 'beginner', 1, 0, 0)")
        con.execute("CREATE TABLE IF NOT EXISTS login_failures (id INTEGER PRIMARY KEY, rate_key TEXT, created_at REAL)")
        con.commit()
        con.close()
        db.close_all()
        app = create_app(path, env="testing")
        st = app.test_client().get("/api/stats").get_json()
        self.assertEqual(st["tracks"]["complexity"]["answered"], 1)
        self.assertNotIn("login_failures", {r["name"] for r in db.conn().execute("SELECT name FROM sqlite_master")})

    def test_legacy_database_upgrade(self):
        """A database from the very first (pre-accounts) version keeps its progress."""
        import sqlite3
        import db
        path = os.path.join(self.tmp, "legacy.db")
        old = sqlite3.connect(path)
        old.executescript("""
            CREATE TABLE questions (instance_id TEXT PRIMARY KEY, exercise_id TEXT, track TEXT, topic TEXT, type TEXT, difficulty TEXT,
                session_id TEXT, context TEXT, attempts INTEGER DEFAULT 0, hints_used INTEGER DEFAULT 0, correct INTEGER DEFAULT 0,
                first_try_correct INTEGER DEFAULT 0, revealed INTEGER DEFAULT 0, started_at TEXT, updated_at TEXT);
            CREATE TABLE mistakes (exercise_id TEXT PRIMARY KEY, question TEXT, my_answer TEXT, correct_answer TEXT, explanation TEXT,
                topic TEXT, track TEXT, type TEXT, difficulty TEXT, attempts INTEGER, hints_used INTEGER, times_missed INTEGER DEFAULT 0,
                first_missed_at TEXT, last_missed_at TEXT, last_attempted_at TEXT, status TEXT DEFAULT 'open', correct_streak INTEGER DEFAULT 0,
                retry_count INTEGER DEFAULT 0, retry_correct INTEGER DEFAULT 0);
            INSERT INTO questions(instance_id, exercise_id, track, topic, type, difficulty, attempts, correct, first_try_correct)
                VALUES ('old1', 'c2-nested-two', 'complexity', 'nested_loops', 'identify', 'beginner', 1, 1, 1);
            INSERT INTO mistakes(exercise_id, question, topic, track, type, difficulty, status) VALUES ('c1-const-assign', 'q', 'fundamentals', 'complexity', 'identify', 'beginner', 'open');
        """)
        old.commit()
        old.close()
        db.close_all()
        from app import create_app
        c = create_app(path, env="testing").test_client()
        self.assertEqual(c.get("/api/stats").get_json()["tracks"]["complexity"]["answered"], 1)
        self.assertEqual(len(c.get("/api/mistakes?status=all").get_json()), 1)


class TestSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = fresh_db("prod")
        from app import create_app
        cls.app = create_app(cls.db_path, env="testing")

    def setUp(self):
        import db
        db.configure(self.db_path)
        self.c = self.app.test_client()

    def test_security_headers_and_no_debug(self):
        r = self.c.get("/")
        self.assertFalse(self.app.debug)
        for h in ("Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy"):
            self.assertIn(h, r.headers)
        cookie = r.headers.get("Set-Cookie", "") or ""
        if cookie:
            self.assertIn("HttpOnly", cookie)

    def test_error_pages_do_not_leak(self):
        r = self.c.get("/definitely/not/here")
        self.assertEqual(r.status_code, 404)
        self.assertNotIn(b"Traceback", r.data)
        self.assertEqual(self.c.get("/api/exercise/nope").get_json(), {"error": "exercise not found"})
        self.assertEqual(self.c.get("/api/exercise/..%2F..%2Fetc").status_code, 404)
        from engine import stats
        orig = stats.track_stats
        stats.track_stats = lambda: 1 / 0
        try:
            r = self.c.get("/")
        finally:
            stats.track_stats = orig
        self.assertEqual(r.status_code, 500)
        body = r.get_data(as_text=True)
        for leak in ("Traceback", "ZeroDivisionError", "track_stats", os.path.dirname(ROOT), "SECRET"):
            self.assertNotIn(leak, body)

    def test_database_errors_are_friendly(self):
        import sqlite3
        import db
        orig = db.get_exercise

        def boom(_):
            raise sqlite3.OperationalError("disk I/O error at /secret/path")
        db.get_exercise = boom
        try:
            r = self.c.get("/api/exercise/c2-nested-two")
        finally:
            db.get_exercise = orig
        self.assertEqual(r.status_code, 503)
        self.assertNotIn(b"/secret/path", r.data)

    def test_invalid_submissions(self):
        c = self.c
        self.assertEqual(c.post("/api/exercise/c2-nested-two/submit", data="not json", content_type="application/json").status_code, 400)
        self.assertEqual(c.post("/api/exercise/c2-nested-two/submit", json=[1, 2]).status_code, 400)
        self.assertEqual(c.post("/api/exercise/c2-nested-two/submit", json={"answer": "O(n)"}).status_code, 400)
        r = c.post("/api/exercise/c2-nested-two/submit", json={"answer": {"parts": {"answer": ["weird"]}}, "hints_used": "lots"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.get_json()["correct"])
        self.assertEqual(c.post("/api/exercise/pt-sum/submit", json={"answer": {"rows": "x"}}).status_code, 200)
        self.assertEqual(c.post("/api/session", json={"mode": "hack", "count": "x", "topic": "<script>"}).status_code, 200)
        self.assertEqual(c.post("/api/exercise/c2-nested-two/hint", json={"n": 99}).status_code, 400)
        big = {"answer": {"code": "x" * 400_000}}
        self.assertEqual(c.post("/api/exercise/pw-count-even/submit", json=big).status_code, 413)

    def test_user_html_is_escaped(self):
        c = self.c
        payload = "<script>alert(1)</script>"
        c.post("/api/exercise/pw-count-even/submit", json={"answer": {"code": payload}})
        page = c.get("/progress").get_data(as_text=True)
        self.assertNotIn(payload, page)
        from engine import grading
        sol = grading.grade(BY_ID["pw-count-even"], {"code": payload})
        self.assertFalse(sol["correct"])

    def test_sandbox_blocks_escapes_and_limits_resources(self):
        from engine import sandbox
        t = [{"args": [1], "expect": 1}]
        attacks = [
            'procedure F(x)\n    s = "{0._" + "_globals_" + "_}"\n    return s.format(x)',
            'procedure F(x)\n    return f"{x}"',
            'procedure F(x)\n    return _rng',
            'procedure F(x)\n    return x.__class__',
            'procedure F(x)\n    import os',
        ]
        for a in attacks:
            with self.subTest(a[:40]):
                r = sandbox.run_tests(a, t)
                self.assertEqual(r["passed"], 0)
        slow = sandbox.run_tests("procedure F(x)\n    return 10 ^ 10 ^ 10", t)
        self.assertFalse(slow["runnable"])
        ok = sandbox.run_tests("procedure F(x)\n    return x", t)
        self.assertEqual(ok["passed"], 1)

    def test_sandbox_child_has_no_secrets(self):
        import subprocess
        from engine import sandbox
        seen = {}
        orig = subprocess.run

        def spy(*a, **k):
            seen.update(k.get("env") or {})
            return orig(*a, **k)
        subprocess.run = spy
        os.environ["SECRET_KEY"] = "top-secret-value"
        try:
            sandbox.run_tests("procedure F(x)\n    return x", [{"args": [1], "expect": 1}])
        finally:
            subprocess.run = orig
            os.environ.pop("SECRET_KEY", None)
        self.assertNotIn("SECRET_KEY", seen)
        self.assertNotIn("BIGO_DB", seen)

    def test_database_init_is_idempotent(self):
        import db
        with self.app.app_context():
            self.c.post("/api/exercise/c2-nested-two/submit", json={"answer": {"parts": {"answer": "n"}}})
            count = lambda: db.conn().execute("SELECT COUNT(*) AS n FROM questions").fetchone()["n"]
            before = count()
            db.init_db()
            db.init_db(force_reseed=True)
            self.assertEqual(count(), before)
        self.assertGreaterEqual(len(self.c.get("/api/mistakes?status=all").get_json()), 1)
        self.assertEqual(self.c.get("/healthz").get_json(), {"ok": True, "app": "bigo-trainer"})

    def test_unknown_session_id_is_ignored(self):
        r = self.c.post("/api/exercise/c2-nested-two/submit", json={"answer": {"parts": {"answer": "n"}}, "session_id": "made-up-session"})
        self.assertEqual(r.status_code, 200)
        import db
        row = db.conn().execute("SELECT session_id FROM questions WHERE instance_id=?", (r.get_json()["instance_id"],)).fetchone()
        self.assertIsNone(row["session_id"])


if __name__ == "__main__":
    unittest.main()


class TestLauncher(unittest.TestCase):
    """The desktop launcher's helpers (the full packaged app is covered by tests/smoke_exe.py)."""

    def test_user_data_dir_is_outside_the_app(self):
        import launcher
        d = launcher.user_data_dir()
        self.assertTrue(d.endswith("AlgorithmStudy"))
        self.assertFalse(os.path.abspath(d).startswith(ROOT))

    def test_sandbox_flag_matches(self):
        import launcher
        from engine import sandbox
        self.assertEqual(launcher.SANDBOX_FLAG, sandbox.SANDBOX_FLAG)

    def test_health_ignores_closed_ports(self):
        import launcher
        port = launcher.free_port()
        self.assertIsNone(launcher.health(port, timeout=0.3))
        self.assertTrue(launcher.port_is_free(port))
