"""Tests for the T(n) Analysis section: safe parsing, equivalence, grading, API, progress, mistakes.

Run from the project root:
    python -m unittest discover -s tests -v
"""
import ast
import json
import os
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from data import seed_exercises  # noqa: E402
from data.tn_bank import SPECS  # noqa: E402
from engine import tn, tnmath  # noqa: E402
from engine.catalog import TN_LEVELS, TN_TOPICS  # noqa: E402

SEED = seed_exercises()
TN = {e["id"]: e for e in SEED if e["track"] == "tn"}


def fresh_db(name):
    return os.path.join(tempfile.mkdtemp(), name + ".db")


# ============================================================================ parser
class TestParser(unittest.TestCase):
    def eq(self, a, b, vs=("n", "m", "k")):
        return tnmath.equivalent(tnmath.parse(a, vs).expr, tnmath.parse(b, vs).expr)

    def test_equivalent_forms(self):
        for a, b in [("3n+4", "4+3n"), ("3n+4", "n+n+n+4"), ("3*n + 4", "3n + 4"),
                     ("n(n+1)/2", "(n^2+n)/2"), ("n(n+1)/2", "n^2/2 + n/2"), ("n*(n+1)/2", "0.5n^2+0.5n"),
                     ("2^3", "8"), ("(n+1)(n-1)", "n^2-1"), ("3log(n)+2", "2+3*log(n)"),
                     ("n log(n)", "n*log(n)"), ("4nm+4n+4", "4*m*n + 4*n + 4"), ("nmk", "k*m*n"),
                     ("n**2", "n^2")]:
            with self.subTest(a=a, b=b):
                self.assertTrue(self.eq(a, b))

    def test_non_equivalent(self):
        for a, b in [("3n+4", "3n+5"), ("n^2", "n^3"), ("nm", "n^2"), ("log(n)", "n"), ("n+m", "2n"),
                     ("n(n+1)/2", "n(n-1)/2")]:
            with self.subTest(a=a, b=b):
                self.assertFalse(self.eq(a, b))

    def test_prefixes_and_wrappers(self):
        self.assertTrue(tnmath.equivalent(tnmath.parse("T(n) = 3n + 4").expr, tnmath.parse("3n+4").expr))
        p = tnmath.parse("Θ(n^2)", allow_wrapper=True)
        self.assertEqual(p.wrapper, "theta")
        self.assertEqual(tnmath.parse("Theta(n)", allow_wrapper=True).wrapper, "theta")
        self.assertEqual(tnmath.parse("O(n)", allow_wrapper=True).wrapper, "O")
        self.assertEqual(tnmath.parse("Ω(n)", allow_wrapper=True).wrapper, "omega")

    def test_simplified_detection(self):
        self.assertTrue(tnmath.is_simplified(tnmath.parse("4n + 4")))
        self.assertTrue(tnmath.is_simplified(tnmath.parse("n^2/2 + n/2")))
        self.assertFalse(tnmath.is_simplified(tnmath.parse("n + n + n + 4")))
        self.assertFalse(tnmath.is_simplified(tnmath.parse("1 + (n+1) + n + 2n")))

    def test_pretty_and_theta(self):
        self.assertEqual(tnmath.pretty(tnmath.parse("4n^2+7n+3").expr), "4n² + 7n + 3")
        e = tnmath.parse("4nm + 4n + 4").expr
        self.assertEqual(tnmath.theta_text(e, ("n", "m")), "nm")
        e = tnmath.parse("3n + 2m + 1").expr
        self.assertEqual(tnmath.theta_text(e, ("n", "m")), "n + m")
        self.assertEqual(tnmath.theta_text(tnmath.parse("3log(n) + 2").expr, ("n",)), "log n")
        self.assertEqual(tnmath.theta_text(tnmath.parse("2n log(n) + 5n").expr, ("n",)), "n log n")

    def test_bad_syntax_rejected_with_message(self):
        for bad in ["", "   ", "3n +", "(n+1", "n+1)", "3 * * n", "n^", "x + 1", "n = 3", "3n; 4", "log", "log()",
                    "n%2", "n,m", "n!", "'n'", "\"n\"", "1/0"]:
            with self.subTest(bad=bad):
                with self.assertRaises(tnmath.ParseError) as cm:
                    tnmath.parse(bad)
                self.assertTrue(str(cm.exception))

    def test_variable_restriction(self):
        with self.assertRaises(tnmath.ParseError):
            tnmath.parse("n + m", ("n",))
        tnmath.parse("n + m", ("n", "m"))


class TestParserSecurity(unittest.TestCase):
    """Mathematical input must never execute code or exhaust resources."""

    MALICIOUS = [
        "__import__('os').system('touch /tmp/pwned_tn')",
        "__import__",
        "().__class__.__bases__[0].__subclasses__()",
        "n.__class__",
        "n.__dict__",
        "exec('print(1)')",
        "eval('1+1')",
        "open('/etc/passwd').read()",
        "lambda: 1",
        "f'{n}'",
        "globals()",
        "os.system('id')",
        "Symbol('n')",
        "sympify('n')",
        "Function('f')(n)",
        "n if n else 1",
        "[x for x in range(10**9)]",
        "n @ n",
        "\\x00n",
        "n; import os",
        "import os",
        "n\nimport os",
        "${n}",
        "`n`",
    ]

    def test_malicious_strings_rejected(self):
        marker = "/tmp/pwned_tn"
        if os.path.exists(marker):
            os.remove(marker)
        for s in self.MALICIOUS:
            with self.subTest(s=s):
                with self.assertRaises(tnmath.ParseError):
                    tnmath.parse(s)
                with self.assertRaises(tnmath.ParseError):
                    tnmath.parse(s, allow_wrapper=True)
        self.assertFalse(os.path.exists(marker))

    def test_resource_limits(self):
        cases = ["n^1000000", "9^9^9^9", "2^2^2^2^2", "(n+1)^999", "((((((((((((((((((((((((((n))))))))))))))))))))))))))",
                 "(" * 500 + "n" + ")" * 500, "n+" * 300 + "n", "9" * 50, "n^(n)", "n^log(n)", "(n+1)^8*(n+2)^8*(n+3)^8"]
        for s in cases:
            with self.subTest(s=s[:40]):
                t0 = time.time()
                with self.assertRaises(tnmath.ParseError):
                    tnmath.parse(s)
                self.assertLess(time.time() - t0, 2.0)

    def test_no_eval_in_parser_source(self):
        """The parser module never calls eval/exec/sympify/parse_expr."""
        for mod in ("engine/tnmath.py", "engine/tn.py"):
            src = open(os.path.join(ROOT, mod), encoding="utf-8").read()
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    f = node.func
                    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == "re":
                        continue          # re.compile is a regex, not code compilation
                    name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
                    with self.subTest(mod=mod, line=node.lineno):
                        self.assertNotIn(name, ("eval", "exec", "sympify", "parse_expr", "compile", "__import__"))

    def test_api_rejects_malicious_input(self):
        os.environ.pop("BIGO_DB", None)
        from app import create_app
        c = create_app(db_path=fresh_db("tnsec"), env="testing").test_client()

        def post(url, body):
            return c.post(url, data=json.dumps(body), content_type="application/json")

        for s in self.MALICIOUS + ["9^9^9^9", "(" * 300 + "n" + ")" * 300]:
            with self.subTest(s=s[:40]):
                r = post("/api/tn/preview", {"text": s, "vars": ["n"]})
                self.assertEqual(r.status_code, 200)
                self.assertFalse(r.get_json()["ok"])
                r = post("/api/exercise/tn2-sum/submit", {"answer": {"mode": "direct", "T": {"all": s}, "theta": {"all": s}}})
                self.assertEqual(r.status_code, 200)
                j = r.get_json()
                self.assertFalse(j["correct"])
                self.assertEqual(j["T"]["all"]["category"], "syntax")
                r = post("/api/exercise/tn2-sum/tn_step", {"step": "all-simplify", "value": s})
                self.assertEqual(r.status_code, 200)
                self.assertFalse(r.get_json()["correct"])
        # odd types and oversized payloads don't crash
        for ans in [{"T": "4n+4"}, {"T": {"all": 5}}, {"T": {"all": None}}, {"T": {"all": ["n"]}},
                    {"T": {"all": "n" * 100000}}, {"mode": "table", "cells": {"r1": "x"}}, {"mode": "table", "cells": []}]:
            with self.subTest(ans=str(ans)[:40]):
                r = post("/api/exercise/tn2-sum/submit", {"answer": ans})
                self.assertIn(r.status_code, (200, 400, 413))
        self.assertFalse(os.path.exists("/tmp/pwned_tn"))


# ============================================================================ bank and model
class TestBank(unittest.TestCase):
    def test_bank_size_and_coverage(self):
        self.assertGreaterEqual(len(TN), 50)
        self.assertEqual(set(e["topic"] for e in TN.values()), set(TN_TOPICS))
        self.assertEqual(set(e["level"] for e in TN.values()), set(TN_LEVELS))
        for e in TN.values():
            with self.subTest(e["id"]):
                for key in ("id", "title", "prompt", "code", "vars", "cases", "rows", "solution", "hints", "guided",
                            "topic", "level", "difficulty"):
                    self.assertTrue(e.get(key) is not None, key)
                self.assertGreaterEqual(len(e["hints"]), 2)
                self.assertIn(e["difficulty"], ("beginner", "intermediate", "advanced"))
                for c in e["cases"]:
                    self.assertIn("T", e["solution"][c])
                    self.assertIn("theta", e["solution"][c])
                if len(e["cases"]) > 1:
                    self.assertTrue(e.get("assumptions") or e.get("case_notes"))

    def test_every_spec_verified_by_simulation(self):
        """Every expected T(n) matches a counted run of the algorithm at several input sizes."""
        for spec in SPECS:
            with self.subTest(spec["id"]):
                self.assertEqual(tn.verify(spec), [])

    def test_model_costs(self):
        # expression costs; an assignment adds 1 for "=" on top of these
        self.assertEqual(tn.op_count("5"), 0)
        self.assertEqual(tn.op_count("sum + A[i]"), 1)
        self.assertEqual(tn.op_count("dx * dx + dy * dy"), 3)
        self.assertEqual(tn.op_count("A[n - 1 - i]"), 2)
        self.assertEqual(tn.op_count("i < n"), 1)

    def test_known_answers(self):
        cases = {"tn2-sum": "4n+4", "tn4-pairs": "4n^2+4n+4", "tn5-triangle": "2n^2+6n+4",
                 "tn6-doubling": "3log(n)+2", "tn7-grid": "4nm+4n+4"}
        for i, t in cases.items():
            with self.subTest(i):
                vs = tuple(TN[i]["vars"])
                self.assertTrue(tnmath.equivalent(tnmath.sympify_trusted(TN[i]["solution"]["all"]["T"]),
                                                  tnmath.parse(t, vs).expr))
        ls = TN["tn8-linear-search"]["solution"]
        self.assertTrue(tnmath.equivalent(tnmath.sympify_trusted(ls["best"]["T"]), tnmath.parse("4").expr))
        self.assertTrue(tnmath.equivalent(tnmath.sympify_trusted(ls["worst"]["T"]), tnmath.parse("3n+3").expr))


# ============================================================================ grading (engine level)
class TestGrading(unittest.TestCase):
    def g(self, ex_id, T, theta, **kw):
        ex = TN[ex_id]
        return tn.grade(ex, {"mode": kw.get("mode", "direct"), "T": T, "theta": theta, "cells": kw.get("cells", {})})

    def test_correct_and_equivalent(self):
        for T in ["4n+4", "4+4n", "n+n+n+n+4", "4(n+1)", "T(n) = 4n + 4"]:
            with self.subTest(T=T):
                r = self.g("tn2-sum", {"all": T}, {"all": "Θ(n)"})
                self.assertTrue(r["correct"], r)
        r = self.g("tn5-triangle", {"all": "2n^2+6n+4"}, {"all": "Theta(n^2)"})
        self.assertTrue(r["correct"])

    def test_parts_graded_independently(self):
        r = self.g("tn2-sum", {"all": "4n+4"}, {"all": "Θ(n^2)"})
        self.assertTrue(r["t_correct"])
        self.assertFalse(r["theta_correct"])
        self.assertFalse(r["correct"])
        r = self.g("tn2-sum", {"all": "4n+5"}, {"all": "Θ(n)"})
        self.assertFalse(r["t_correct"])
        self.assertTrue(r["theta_correct"])

    def test_asymptotic_only_and_notation(self):
        r = self.g("tn2-sum", {"all": "Θ(n)"}, {"all": "Θ(n)"})
        self.assertEqual(r["T"]["all"]["category"], "asymptotic_only")
        r = self.g("tn2-sum", {"all": "4n+4"}, {"all": "O(n)"})
        self.assertEqual(r["theta"]["all"]["category"], "wrong_notation")
        self.assertFalse(r["theta_correct"])

    def test_error_specific_feedback(self):
        expect = [("tn2-sum", "4n+3", "missed_final_check"),
                  ("tn4-pairs", "4n+4", None),
                  ("tn7-grid", "4n^2+4n+4", "merged_variables"),
                  ("tn6-doubling", "3n+2", "missing_log")]
        for ex_id, T, cat in expect:
            with self.subTest(ex_id):
                vs = tuple(TN[ex_id]["vars"])
                r = self.g(ex_id, {"all": T}, {"all": "Θ(" + TN[ex_id]["solution"]["all"]["theta"].replace("²", "^2") + ")"})
                self.assertFalse(r["t_correct"])
                self.assertTrue(r["T"]["all"].get("headline"))
                if cat:
                    self.assertEqual(r["T"]["all"]["category"], cat)
                self.assertEqual(r["category"], r["T"]["all"]["category"])
        r = self.g("tn4-pairs", {"all": "4n+4"}, {"all": "Θ(n^2)"})
        self.assertIn(r["T"]["all"]["category"], ("inner_once", "missing_loop_factor"))

    def test_multi_variable(self):
        r = self.g("tn7-grid", {"all": "4mn+4n+4"}, {"all": "Θ(mn)"})
        self.assertTrue(r["correct"])
        r = self.g("tn7-grid", {"all": "4mn+4n+4"}, {"all": "Θ(n^2)"})
        self.assertFalse(r["theta_correct"])

    def test_best_worst_cases(self):
        r = self.g("tn8-linear-search", {"best": "4", "worst": "3n+3"}, {"best": "Θ(1)", "worst": "Θ(n)"})
        self.assertTrue(r["correct"])
        r = self.g("tn8-linear-search", {"best": "4", "worst": "3n+3"}, {"best": "Θ(n)", "worst": "Θ(n)"})
        self.assertFalse(r["correct"])
        self.assertTrue(r["t_correct"])

    def test_table_mode(self):
        ex = TN["tn2-sum"]
        good = {row["key"]: {"exec": row["exec"]} for row in ex["solution"]["all"]["table"]}
        r = self.g("tn2-sum", {"all": "4n+4"}, {"all": "Θ(n)"}, mode="table", cells=good)
        self.assertTrue(r["cells_correct"])
        self.assertTrue(r["correct"])
        bad = dict(good)
        cond = next(row["key"] for row in ex["rows"] if row["role"] == "cond")
        bad[cond] = {"exec": "n"}
        r = self.g("tn2-sum", {"all": "4n+4"}, {"all": "Θ(n)"}, mode="table", cells=bad)
        self.assertFalse(r["cells_correct"])
        self.assertFalse(r["cells"][cond]["exec"]["correct"])
        self.assertNotIn("expected", r["cells"][cond]["exec"])  # no answer leak on a wrong table

    def test_guided_steps(self):
        ex = TN["tn2-sum"]
        r = tn.check_step(ex, "all-simplify", "n+n+n+n+4")
        self.assertFalse(r["correct"])
        self.assertIn("simplified", r["error"])
        self.assertNotIn("expected", r)
        r = tn.check_step(ex, "all-simplify", "4n+5")
        self.assertFalse(r["correct"])
        self.assertNotIn("expected", r)
        r = tn.check_step(ex, "all-simplify", "4n+4")
        self.assertTrue(r["correct"])
        self.assertEqual(r["expected"], "4n + 4")
        r = tn.check_step(ex, "all-theta", "Θ(n)")
        self.assertTrue(r["correct"])
        r = tn.check_step(ex, "all-theta", "O(n)")
        self.assertFalse(r["correct"])
        r = tn.check_step(ex, "all-combine", "", reveal=True)
        self.assertTrue(r["revealed"])
        self.assertIn("expected", r)


# ============================================================================ API, progress, mistakes
class TestTnAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.pop("BIGO_DB", None)
        from app import create_app
        cls.db_path = fresh_db("tnapi")
        cls.app = create_app(db_path=cls.db_path, env="testing")

    def setUp(self):
        self.c = self.app.test_client()

    def post(self, url, body=None):
        r = self.c.post(url, data=json.dumps(body or {}), content_type="application/json")
        self.assertLess(r.status_code, 400, r.data[:300])
        return r.get_json()

    def test_01_pages(self):
        for url in ["/tn", "/tn/reference", "/exercise/tn2-sum", "/exercise/tn8-linear-search", "/",
                    "/progress", "/review", "/practice?topic=tn&difficulty=beginner"]:
            with self.subTest(url):
                r = self.c.get(url)
                self.assertEqual(r.status_code, 200)
        ref = self.c.get("/tn/reference").get_data(as_text=True)
        self.assertIn("not a stopwatch", ref)
        self.assertIn("4n + 4", ref)
        self.assertIn("T(n) Analysis", self.c.get("/").get_data(as_text=True))

    def test_02_public_view_no_leaks(self):
        rows = self.c.get("/api/exercises?track=tn").get_json()
        self.assertEqual(len(rows), len(TN))
        for ex_id in TN:
            v = self.c.get(f"/api/exercise/{ex_id}").get_json()
            blob = json.dumps(v, ensure_ascii=False)
            with self.subTest(ex_id):
                self.assertEqual(v["type"], "tn")
                self.assertNotIn('"solution"', blob)
                self.assertNotIn('"answer"', blob)
                self.assertNotIn('"exec":', blob)
                self.assertNotIn('"explain"', blob)
                self.assertNotIn('"variants"', blob)
                self.assertNotIn('"hints"', blob)
                for row in v["rows"]:
                    self.assertNotIn("total", row)
                    if v["table_blank"] in ("cost", "both"):
                        self.assertIsNone(row["cost"])

    def test_03_preview(self):
        j = self.post("/api/tn/preview", {"text": "n(n+1)/2", "vars": ["n"]})
        self.assertTrue(j["ok"])
        self.assertIn("n²", j["pretty"])
        j = self.post("/api/tn/preview", {"text": "Θ(n^2)", "vars": ["n"]})
        self.assertEqual(j["pretty"], "Θ(n²)")
        self.assertFalse(self.post("/api/tn/preview", {"text": "3n +", "vars": ["n"]})["ok"])

    def test_04_progressive_hints(self):
        h1 = self.post("/api/exercise/tn4-pairs/hint", {"n": 1})
        self.assertEqual(h1["n"], 1)
        self.assertGreaterEqual(h1["total"], 2)
        # the first hint never gives away the complete T(n)
        self.assertNotIn("4n² + 4n + 4", h1["hint"])
        self.assertNotIn("4n^2", h1["hint"])

    def test_05_wrong_then_right_tracks_parts_and_mistakes(self):
        sess = self.post("/api/session", {"mode": "practice", "topic": "tn", "difficulty": "intermediate", "count": 3})
        self.assertGreater(sess["pool_size"], 0)
        nxt = self.post(f"/api/session/{sess['id']}/next")
        self.assertIn(nxt["exercise_id"], TN)

        inst = "inst-pairs-1"
        j = self.post("/api/exercise/tn4-pairs/submit", {
            "instance_id": inst, "session_id": sess["id"], "context": "session", "hints_used": 1,
            "answer": {"mode": "direct", "T": {"all": "4n+4"}, "theta": {"all": "Θ(n^2)"}}})
        self.assertFalse(j["correct"])
        self.assertFalse(j["t_correct"])
        self.assertTrue(j["theta_correct"])
        self.assertNotIn("solution", j)
        j = self.post("/api/exercise/tn4-pairs/submit", {
            "instance_id": inst, "session_id": sess["id"], "context": "session", "hints_used": 1,
            "answer": {"mode": "direct", "T": {"all": "4n^2+4n+4"}, "theta": {"all": "Θ(n^2)"}}})
        self.assertTrue(j["correct"])
        self.assertEqual(j["attempt_no"], 2)
        self.assertIn("solution", j)
        self.assertEqual(j["solution"]["cases"]["all"]["theta"], "n²")

        mistakes = self.c.get("/api/mistakes?track=tn").get_json()
        m = next(x for x in mistakes if x["exercise_id"] == "tn4-pairs")
        self.assertIn(m["category"], ("inner_once", "missing_loop_factor"))
        self.assertTrue(m["category_label"])
        self.assertIn("4n", m["my_answer"])
        self.assertIn("4n² + 4n + 4", m["correct_answer"])

        # first try fully right on another exercise
        self.post("/api/exercise/tn2-sum/submit", {
            "instance_id": "inst-sum-1", "answer": {"mode": "direct", "T": {"all": "4n+4"}, "theta": {"all": "Θ(n)"}}})

        st = self.c.get("/api/stats").get_json()["tn"]
        o = st["overall"]
        self.assertEqual(o["answered"], 2)
        self.assertEqual(o["correct_T"], 2)
        self.assertEqual(o["correct_theta"], 2)
        self.assertEqual(o["t_first"], 50)
        self.assertEqual(o["theta_first"], 100)
        self.assertEqual(o["hinted"], 1)
        topics = {r["topic"]: r for r in st["by_topic"]}
        self.assertEqual(topics["tn_nested"]["t_first"], 0)
        self.assertEqual(topics["tn_single"]["t_first"], 100)

        summ = self.post(f"/api/session/{sess['id']}/end")
        self.assertGreaterEqual(summ["answered"], 1)

        # progress page shows the T(n) section; complexity stats unaffected
        html = self.c.get("/progress").get_data(as_text=True)
        self.assertIn("tn-progress", html)
        self.assertIn("Nested loops", html)
        tracks = self.c.get("/api/stats").get_json()["tracks"]
        self.assertEqual(tracks["complexity"]["answered"], 0)

    def test_06_review_retry(self):
        sess = self.post("/api/session", {"mode": "review", "count": 0})
        self.assertGreater(sess["pool_size"], 0)
        nxt = self.post(f"/api/session/{sess['id']}/next")
        self.assertEqual(nxt["exercise_id"], "tn4-pairs")
        j = self.post("/api/exercise/tn4-pairs/submit", {
            "instance_id": "inst-retry", "session_id": sess["id"], "context": "review",
            "answer": {"mode": "direct", "T": {"all": "4n^2+4n+4"}, "theta": {"all": "Θ(n^2)"}}})
        self.assertTrue(j["correct"])
        self.assertIn(j["mistake_status"], ("improving", "mastered"))

    def test_07_reveal_and_step_api(self):
        j = self.post("/api/exercise/tn5-triangle/tn_step", {"step": "all-simplify", "value": "2n^2+6n+4"})
        self.assertTrue(j["correct"])
        j = self.post("/api/exercise/tn5-triangle/tn_step", {"step": "all-simplify", "value": "2n^2+6n+5"})
        self.assertFalse(j["correct"])
        self.assertNotIn("expected", j)
        r = self.c.post("/api/exercise/tn5-triangle/tn_step", data=json.dumps({"step": "nope", "value": "1"}),
                        content_type="application/json")
        self.assertEqual(r.status_code, 400)
        j = self.post("/api/exercise/tn6-doubling/reveal", {"instance_id": "rev-1"})
        self.assertIn("solution", j)

    def test_08_adaptive_and_mixed_sessions_include_tn(self):
        sess = self.post("/api/session", {"mode": "adaptive", "topic": "tn", "count": 5})
        self.assertGreater(sess["pool_size"], 0)
        nxt = self.post(f"/api/session/{sess['id']}/next")
        self.assertIn(nxt["exercise_id"], TN)

    def test_09_non_json_rejected(self):
        r = self.c.post("/api/exercise/tn2-sum/submit", data="answer=1",
                        content_type="application/x-www-form-urlencoded")
        self.assertEqual(r.status_code, 415)

    def test_10_persistence_across_restart(self):
        from app import create_app
        import db as dbmod
        dbmod.close_all()
        app2 = create_app(db_path=self.db_path, env="testing")
        st = app2.test_client().get("/api/stats").get_json()["tn"]["overall"]
        self.assertGreaterEqual(st["answered"], 2)
        ms = app2.test_client().get("/api/mistakes?track=tn").get_json()
        self.assertTrue(any(m["exercise_id"] == "tn4-pairs" for m in ms))


if __name__ == "__main__":
    unittest.main()
