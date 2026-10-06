"""Tests for the Time Complexity Proofs section: safe parsing, the c / n₀ checker, the exercise bank,
grading feedback, API, mastery tracking, mistakes, adaptive practice, the sandbox and the T(n) link.

Run from the project root:
    python -m unittest discover -s tests -v
"""
import json
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import sympy as sp  # noqa: E402

from data import proofs_bank, seed_exercises  # noqa: E402
from engine import grading, proofs as P, tnmath  # noqa: E402
from engine.catalog import PROOF_TOPICS  # noqa: E402

SEED = seed_exercises()
PROOFS = {e["id"]: e for e in SEED if e["track"] == "proofs"}
SIDES = {"O": [("upper", "c")], "omega": [("lower", "c")], "theta": [("lower", "c1"), ("upper", "c2")]}


def fresh_db(name):
    return os.path.join(tempfile.mkdtemp(), name + ".db")


# ============================================================================ parsing & safety
class TestProofParsing(unittest.TestCase):
    def test_growth_mode_accepts_the_growth_classes(self):
        for text, expected in [("2^n", 2 ** P.N), ("n!", sp.factorial(P.N)), ("sqrt(n)", sp.sqrt(P.N)),
                               ("n log n", P.N * sp.log(P.N) / sp.log(2)), ("log₂(n²)", 2 * sp.log(P.N) / sp.log(2)),
                               ("3n^2 + 5n + 2", 3 * P.N ** 2 + 5 * P.N + 2), ("1", sp.Integer(1))]:
            with self.subTest(text):
                self.assertEqual(sp.simplify(P.parse_fn(text) - expected), 0)

    def test_normal_t_n_parsing_is_unchanged(self):
        for text in ["2^n", "n!", "sqrt(n)"]:
            with self.subTest(text), self.assertRaises(tnmath.ParseError):
                tnmath.parse(text)

    def test_hostile_or_unsupported_input_is_rejected(self):
        for text in ["__import__('os').system('ls')", "n.__class__", "eval(n)", "exec('1')", "lambda: 1", "n^n",
                     "2^n^n", "x + 1", "n" * 300, "9" * 40, "(" * 40 + "n" + ")" * 40, "n!!", "3!", "open('f')",
                     "2^(n+1)", "", "n; import os"]:
            with self.subTest(text[:30]), self.assertRaises(tnmath.ParseError):
                P.parse_fn(text)

    def test_constants_parse_safely(self):
        self.assertEqual(P.parse_number("1/2", "c"), sp.Rational(1, 2))
        self.assertEqual(P.parse_number(" 0.25 ", "c"), sp.Rational(1, 4))
        for bad in ["0", "-3", "n", "c", "1e9999", "__import__", "", "10000000000"]:
            with self.subTest(bad), self.assertRaises(tnmath.ParseError):
                P.parse_number(bad, "c")

    def test_engine_never_evaluates_text(self):
        src = open(os.path.join(ROOT, "engine", "proofs.py"), encoding="utf-8").read()
        code = re.sub(r'"""[\s\S]*?"""', "", src)
        self.assertIsNone(re.search(r"\b(eval|exec|sympify|lambdify|parse_expr|nsimplify)\s*\(\s*['\"]", code))
        self.assertIsNone(re.search(r"\b(eval|exec|lambdify|parse_expr)\s*\(", code))
        self.assertNotIn("sp.sympify", code)


# ============================================================================ the checker
class TestChecker(unittest.TestCase):
    def check(self, f, g, c, n0, side):
        return P.check_bound(P.parse_fn(f), P.parse_fn(g), sp.nsimplify(c), sp.nsimplify(n0), side)

    def test_valid_bounds(self):
        self.assertTrue(self.check("log2(n)", "n^2", 1, 1, "upper")["ok"])
        self.assertTrue(self.check("n^2 + 3n", "n^2", 1, 1, "lower")["ok"])
        self.assertTrue(self.check("3n^2 + 5n + 2", "n^2", 10, 1, "upper")["ok"])
        self.assertTrue(self.check("5n", "n", 5, 1, "upper")["ok"])           # c equal to the limit, exactly tight

    def test_finite_range_is_detected(self):
        r = self.check("n^2", "n", 10, 1, "upper")
        self.assertFalse(r["ok"])
        self.assertFalse(r["eventually"])
        self.assertEqual((r["holds_at"], r["first_fail"]), (10, 11))

    def test_n0_too_small_is_distinguished(self):
        r = self.check("n^3", "2^n", 1, 1, "upper")
        self.assertFalse(r["ok"])
        self.assertTrue(r["eventually"])
        self.assertEqual(r["first_fail"], 2)
        self.assertTrue(self.check("n^3", "2^n", 1, 10, "upper")["ok"])
        self.assertEqual(P.smallest_n0(P.parse_fn("n^3"), P.parse_fn("2^n"), 1, "upper"), 10)

    def test_negative_f_fails_the_definition(self):
        r = self.check("n^2 - 10n", "n^2", "1/2", 1, "lower")
        self.assertFalse(r["ok"])
        self.assertTrue(r["negative"])
        self.assertTrue(self.check("n^2 - 10n", "n^2", "1/2", 20, "lower")["ok"])

    def test_limits_and_truth(self):
        cases = [("log2(n)", "n^2", 0), ("3n^2+5n+2", "n^2", 3), ("n!", "2^n", sp.oo), ("2^n", "n^3", sp.oo),
                 ("2^n", "n!", 0), ("n log2(n)", "n", sp.oo)]
        for f, g, L in cases:
            with self.subTest(f=f, g=g):
                self.assertEqual(P.ratio_limit(P.parse_fn(f), P.parse_fn(g)), L)
        self.assertTrue(P.relation_truth(P.parse_fn("log2(n)"), P.parse_fn("n^2"), "O"))
        self.assertFalse(P.relation_truth(P.parse_fn("n^2"), P.parse_fn("n"), "O"))
        self.assertFalse(P.relation_truth(P.parse_fn("n log2(n)"), P.parse_fn("n"), "theta"))

    def test_suggested_constants_are_valid(self):
        for f, g, rel in [("log2(n)", "n^2", "O"), ("n^2 + 3n", "n^2", "omega"), ("3n^2 + 5n + 2", "n^2", "theta"),
                          ("n^3", "2^n", "O"), ("2^n", "n!", "O"), ("n log2(n) + 5n", "n log2(n)", "theta")]:
            F, G = P.parse_fn(f), P.parse_fn(g)
            sug = P.suggest_constants(F, G, rel)
            with self.subTest(f=f, g=g, rel=rel):
                self.assertIsNotNone(sug)
                for side, k in SIDES[rel]:
                    self.assertTrue(P.check_bound(F, G, sug[k], sug["n0"], side)["ok"])


# ============================================================================ the exercise bank
class TestProofBank(unittest.TestCase):
    def test_size_types_and_coverage(self):
        proofs = [e for e in PROOFS.values() if e["type"] == "proof"]
        self.assertGreaterEqual(len(PROOFS), 40)
        self.assertGreaterEqual(len(proofs), 40)
        self.assertTrue({"proof", "proof_fill", "proof_debug", "proof_limit"} <= {e["type"] for e in PROOFS.values()})
        self.assertGreaterEqual(sum(1 for e in proofs if not e["truth"]), 10)
        self.assertGreaterEqual(sum(1 for e in proofs if e["truth"]), 25)
        self.assertEqual({e["rel"] for e in proofs}, {"O", "omega", "theta"})
        self.assertEqual({e["level"] for e in PROOFS.values()}, {1, 2, 3, 4, 5})
        self.assertTrue({e["topic"] for e in PROOFS.values()} <= set(PROOF_TOPICS))
        texts = " ".join(e["f_text"] + " " + e["g_text"] for e in proofs)
        for cls in ["log₂ n", "n log₂ n", "n²", "n³", "2ⁿ", "n!", "3n + 7", "5n² + 2n + 1", "n² + 100n", "4n³ + n²"]:
            with self.subTest(cls):
                self.assertIn(cls, texts)
        self.assertTrue(any(e["f_text"] == "1" or e["g_text"] == "1" for e in proofs))
        claims = [(e["f"], e["g"], e["rel"]) for e in proofs]
        self.assertEqual(len(claims), len(set(claims)), "duplicate claims")

    def test_truth_values_match_the_limit(self):
        for e in PROOFS.values():
            if e["type"] != "proof":
                continue
            with self.subTest(e["id"]):
                f, g = P.exercise_fns(e)
                self.assertEqual(P.relation_truth(f, g, e["rel"]), e["truth"])

    def test_reference_constants_satisfy_the_definition(self):
        for e in PROOFS.values():
            if e["type"] != "proof" or not e["truth"]:
                continue
            f, g = P.exercise_fns(e)
            for side, k in SIDES[e["rel"]]:
                with self.subTest(e["id"], side=side):
                    self.assertTrue(P.check_bound(f, g, P._const(e["solution"][k]), P._const(e["solution"]["n0"]), side)["ok"])

    def test_every_exercise_has_teaching_material(self):
        for e in PROOFS.values():
            with self.subTest(e["id"]):
                self.assertGreaterEqual(len(e["hints"]), 2)
                if e["type"] == "proof":
                    self.assertTrue(e["why"])
                    self.assertTrue(e["intuition"])
                    self.assertTrue(P.worked_steps(e))
                else:
                    self.assertTrue(e["steps"])

    def test_reference_answers_grade_correct(self):
        for e in PROOFS.values():
            with self.subTest(e["id"]):
                if e["type"] == "proof":
                    if e["truth"]:
                        ans = {"verdict": "true", "inequality": P.required_inequality(e["rel"], "f(n)", "g(n)"),
                               "explanation": e["why"][0]}
                        ans.update({k: e["solution"][k] for k in e["solution"]})
                    else:
                        ans = {"verdict": "false", "explanation": "f(n)/g(n) grows without bound, so no fixed c works."}
                    r = P.grade_proof(e, ans)
                elif e["type"] == "proof_fill":
                    r = P.grade_fill(e, {"blanks": [b.get("show") or b["accept"][0] for b in e["blanks"]]})
                else:
                    r = grading.grade(e, {"parts": {p["id"]: p["answer"] for p in e["parts"]}})
                self.assertTrue(r["correct"], r.get("messages"))
                if e["type"] == "proof_fill":
                    self.assertFalse(P.grade_fill(e, {"blanks": ["999999"] * len(e["blanks"])})["correct"])


# ============================================================================ feedback
class TestFeedback(unittest.TestCase):
    def grade(self, ex_id, **answer):
        return P.grade_proof(PROOFS[ex_id], answer)

    def test_conceptual_errors_are_named(self):
        ok = dict(explanation="for n >= 1, log n <= n <= n^2")
        cases = [
            ("pf-o-log-n2", dict(verdict="true", inequality="c n^2 <= log2(n)", c="1", n0="1", **ok), "reversed", "reversed"),
            ("pf-o-log-n2", dict(verdict="true", inequality="log2(n) <= c n^2", c="1", n0="1", explanation="log grows slower"),
             "intuition_only", "not a proof"),
            ("pf-o-log-n2", dict(verdict="false", explanation="it can't"), "wrong_verdict", "TRUE"),
            ("pf-f-n2-n", dict(verdict="true", inequality="n^2 <= c n", c="10", n0="1", explanation="n^2 <= 10n"),
             "wrong_verdict", "FALSE"),
            ("pf-f-n2-n", dict(verdict="false", explanation="it is wrong"), "disproof_reason", "WHY"),
            ("pf-o-n3-2n", dict(verdict="true", inequality="n^3 <= c 2^n", c="1", n0="1", explanation="induction for n >= 1"),
             "n0_too_small", "larger n₀"),
            ("pf-t-3n2-n2", dict(verdict="true", inequality="3n^2+5n+2 <= c2 n^2", c1="3", c2="10", n0="1",
                                 explanation="5n <= 5n^2"), "one_sided", "both an upper and a lower bound"),
            ("pf-w-n2m10n-n2", dict(verdict="true", inequality="c n^2 <= n^2 - 10n", c="1/2", n0="1",
                                    explanation="for n >= 20, 10n <= n^2/2"), "negative", "0 ≤"),
            ("pf-o-3n7-n", dict(verdict="true", inequality="3n + 7 <= c n", c="0", n0="1", explanation="7 <= 7n"),
             "bad_constant", "positive"),
        ]
        for ex_id, ans, cat, phrase in cases:
            with self.subTest(ex_id, cat=cat):
                r = self.grade(ex_id, **ans)
                self.assertFalse(r["correct"])
                self.assertEqual(r["category"], cat)
                self.assertIn(phrase, " ".join(r["messages"]))

    def test_finite_range_feedback_wording(self):
        r = self.grade("pf-t-n2-100n", verdict="true", inequality="c1 n^2 <= n^2 + 100n <= c2 n^2", c1="2", c2="101", n0="1",
                       explanation="100n <= 100n^2")
        self.assertEqual(r["category"], "finite_range")
        msg = " ".join(r["messages"])
        self.assertIn("works for n = 100", msg)
        self.assertIn("EVERY n ≥ n₀", msg)

    def test_any_valid_constants_are_accepted(self):
        # not the reference constants - just valid ones
        r = self.grade("pf-o-2n3-n3", verdict="true", inequality="f(n) <= c*g(n)", c="3", n0="8",
                       explanation="for n >= 8, 5n^2 + 100 <= n^3")
        self.assertTrue(r["correct"], r["messages"])
        r = self.grade("pf-t-3n2-n2", verdict="true", inequality="0 ≤ c₁·g(n) ≤ f(n) ≤ c₂·g(n)", c1="1/2", c2="4", n0="6",
                       explanation="for n >= 6, 5n + 2 <= n^2")
        self.assertTrue(r["correct"], r["messages"])

    def test_skills_are_reported(self):
        r = self.grade("pf-o-n3-2n", verdict="true", inequality="n^3 <= c 2^n", c="1", n0="1", explanation="n >= 1")
        self.assertEqual(r["skills"], {"big_o": False, "choose_c": True, "choose_n0": False, "growth": False})
        r = self.grade("pf-f-n2-n", verdict="false", explanation="n^2/n = n is unbounded, so no constant c works")
        self.assertTrue(r["correct"])
        self.assertEqual(r["skills"], {"big_o": True, "disprove": True})


# ============================================================================ API / tracking / integration
class TestProofAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.pop("BIGO_DB", None)
        from app import create_app
        cls.app = create_app(db_path=fresh_db("proofs"), env="testing")

    def setUp(self):
        self.c = self.app.test_client()

    def post(self, url, body=None, ok=True):
        r = self.c.post(url, data=json.dumps(body or {}), content_type="application/json")
        if ok:
            self.assertLess(r.status_code, 400, r.data[:300])
        return r

    def test_01_pages(self):
        for url in ["/proofs", "/learn/proofs", "/proofs/sandbox", "/exercise/pf-o-log-n2", "/exercise/pf-c-3n2",
                    "/exercise/pf-d-finite", "/exercise/pf-l-kinds", "/progress", "/review", "/adaptive"]:
            with self.subTest(url):
                self.assertEqual(self.c.get(url).status_code, 200)
        html = self.c.get("/proofs").get_data(as_text=True)
        self.assertIn("Your proof mastery", html)
        self.assertIn("Selecting n₀", html)

    def test_02_public_view_hides_answers(self):
        for ex_id in PROOFS:
            v = self.c.get(f"/api/exercise/{ex_id}").get_json()
            blob = json.dumps(v, ensure_ascii=False)
            with self.subTest(ex_id):
                for key in ('"solution"', '"truth"', '"why"', '"answer"', '"accept"'):
                    self.assertNotIn(key, blob)

    def test_03_wrong_then_right_tracks_mistakes_and_mastery(self):
        ex_id = "pf-o-n3-2n"
        bad = {"verdict": "true", "inequality": "n^3 <= c 2^n", "c": "1", "n0": "1", "explanation": "for n >= 1"}
        r = self.post(f"/api/exercise/{ex_id}/submit", {"answer": bad, "instance_id": "pf-i-1"}).get_json()
        self.assertFalse(r["correct"])
        self.assertNotIn("solution", r)                    # retry-style: no worked proof until solved
        self.assertIn("n₀", " ".join(r["messages"]))
        good = dict(bad, n0="10")
        r = self.post(f"/api/exercise/{ex_id}/submit", {"answer": good, "instance_id": "pf-i-1"}).get_json()
        self.assertTrue(r["correct"])
        self.assertTrue(r["solution"]["steps"])
        self.assertIn("limit", r["solution"])
        mistakes = self.c.get("/api/mistakes?track=proofs&status=all").get_json()
        m = next(x for x in mistakes if x["exercise_id"] == ex_id)
        self.assertEqual(m["category_label"], P.CATEGORIES["n0_too_small"])
        from engine import stats
        with self.app.test_request_context("/"):
            self.app.preprocess_request()
            mastery = {row["skill"]: row for row in stats.proof_mastery()}
        self.assertEqual(mastery["choose_n0"]["answered"], 1)
        self.assertEqual(mastery["choose_n0"]["accuracy"], 0)           # first attempt was wrong
        self.assertEqual(mastery["choose_c"]["accuracy"], 100)
        self.assertEqual(mastery["big_o"]["eventual"], 100)
        self.assertIn("Selecting n₀", self.c.get("/progress").get_data(as_text=True))

    def test_04_parts_and_fill_exercises_through_the_api(self):
        e = PROOFS["pf-d-finite"]
        r = self.post("/api/exercise/pf-d-finite/submit", {"answer": {"parts": {"flaw": e["parts"][0]["options"][1], "fail": "11"}}}).get_json()
        self.assertFalse(r["correct"])
        m = next(x for x in self.c.get("/api/mistakes?track=proofs&status=all").get_json() if x["exercise_id"] == "pf-d-finite")
        self.assertEqual(m["category_label"], P.CATEGORIES["proof_debug"])
        r = self.post("/api/exercise/pf-c-3n2/submit", {"answer": {"blanks": ["5", "5", "7", "1"]}}).get_json()
        self.assertTrue(r["correct"])                       # any c ≥ 5 is valid at that step
        self.assertIn("filled", r["solution"])

    def test_05_practice_test_hides_proof_feedback(self):
        s = self.post("/api/session", {"mode": "test", "count": 1, "track": "proofs", "type": "proof"}).get_json()
        n = self.post(f"/api/session/{s['id']}/next").get_json()
        r = self.post(f"/api/exercise/{n['exercise_id']}/submit",
                      {"answer": {"verdict": "false", "explanation": "x"}, "session_id": s["id"], "context": "test",
                       "instance_id": "pf-test-1"}).get_json()
        self.assertEqual(set(r), {"recorded", "attempt_no", "instance_id"})
        summ = self.post(f"/api/session/{s['id']}/end").get_json()
        self.assertTrue(summ["review"][0]["correct_answer"])

    def test_06_adaptive_and_sessions_include_proofs(self):
        weak = {r["topic"] for r in self.c.get("/api/stats").get_json()["weak"]}
        self.assertTrue(set(PROOF_TOPICS) <= weak)
        s = self.post("/api/session", {"mode": "adaptive", "count": 5, "topic": "proofs"}).get_json()
        self.assertGreater(s["pool_size"], 40)
        for _ in range(3):
            n = self.post(f"/api/session/{s['id']}/next").get_json()
            self.assertIn(n["exercise_id"], PROOFS)
        s = self.post("/api/session", {"mode": "practice", "count": 3, "track": "proofs", "subtopic": "pf_false"}).get_json()
        self.assertGreater(s["pool_size"], 5)

    def test_07_sandbox(self):
        r = self.post("/api/proofs/investigate", {"f": "log(n)", "g": "n^2", "rel": "O"}).get_json()
        self.assertTrue(r["ok"])
        self.assertTrue(r["truth"])
        self.assertEqual(r["limit"], "0")
        self.assertEqual([row["n"] for row in r["table"][:6]], [1, 2, 4, 8, 16, 32])
        self.assertEqual([row["f"] for row in r["table"][:6]], ["0", "1", "2", "3", "4", "5"])
        self.assertEqual([row["g"] for row in r["table"][:6]], ["1", "4", "16", "64", "256", "1,024"])
        self.assertTrue(r["suggested"])
        r = self.post("/api/proofs/investigate", {"f": "n^2", "g": "n", "rel": "O", "consts": {"c": "10", "n0": "1"}}).get_json()
        self.assertFalse(r["truth"])
        self.assertEqual(r["checks"][0]["first_fail"], 11)
        self.assertFalse(r["checks"][0]["ok"])
        r = self.post("/api/proofs/investigate", {"f": "3n^2+5n+2", "g": "n^2", "rel": "theta",
                                                  "consts": {"c1": "3", "c2": "10", "n0": "1"}}).get_json()
        self.assertTrue(all(ch["ok"] for ch in r["checks"]))
        for bad in [{"f": "__import__('os')", "g": "n"}, {"f": "n", "g": "0"}, {"f": "n", "g": "n", "consts": {"c": "-1", "n0": "1"}},
                    {"f": "n" * 500, "g": "n"}]:
            with self.subTest(bad=str(bad)[:40]):
                r = self.post("/api/proofs/investigate", dict(bad, rel="O"))
                self.assertEqual(r.status_code, 200)
                self.assertFalse(r.get_json()["ok"])
                self.assertTrue(r.get_json()["error"])

    def test_08_prove_a_t_n_exercise(self):
        v = self.c.get("/api/exercise/tn2-sum").get_json()
        self.assertTrue(v["provable"])
        pid = self.post("/api/proofs/from_tn/tn2-sum").get_json()["id"]
        self.assertEqual(pid, "pf-tn-tn2-sum")
        pv = self.c.get(f"/api/exercise/{pid}").get_json()
        self.assertEqual(pv["rel"], "theta")
        self.assertEqual(pv["tn_source"], "tn2-sum")
        self.assertEqual(pv["constants"], ["c1", "c2", "n0"])
        upper_only = {"verdict": "true", "inequality": "T(n) <= c2 n".replace("T(n)", "f(n)"), "c1": "1", "c2": "100",
                      "n0": "1", "explanation": "for n >= 1 each term <= its coefficient times n"}
        r = self.post(f"/api/exercise/{pid}/submit", {"answer": upper_only}).get_json()
        self.assertFalse(r["correct"])
        self.assertIn("both", " ".join(r["messages"]))
        both = dict(upper_only, inequality="c1 g(n) <= f(n) <= c2 g(n)")
        r = self.post(f"/api/exercise/{pid}/submit", {"answer": both}).get_json()
        self.assertTrue(r["correct"], r["messages"])
        multi = next(e for e in SEED if e["type"] == "tn" and not P.tn_provable(e))
        self.assertEqual(self.post(f"/api/proofs/from_tn/{multi['id']}", ok=False).status_code, 400)
        self.assertEqual(self.post("/api/proofs/from_tn/pf-o-log-n2", ok=False).status_code, 400)

    def test_09_generated_t_n_proofs_are_sound(self):
        for e in SEED:
            if e["type"] != "tn" or not P.tn_provable(e):
                continue
            pex = P.from_tn(e)
            f, g = P.exercise_fns(pex)
            with self.subTest(e["id"]):
                for side, k in SIDES["theta"]:
                    self.assertTrue(P.check_bound(f, g, P._const(pex["solution"][k]), P._const(pex["solution"]["n0"]), side)["ok"])

    def test_10_reset_clears_proof_mastery(self):
        self.post("/api/exercise/pf-o-n-n2/submit", {"answer": {"verdict": "false", "explanation": "x"}})
        self.post("/api/reset", {"confirm": "RESET"})
        from engine import stats
        with self.app.test_request_context("/"):
            self.app.preprocess_request()
            self.assertTrue(all(m["answered"] == 0 for m in stats.proof_mastery()))


if __name__ == "__main__":
    unittest.main()
