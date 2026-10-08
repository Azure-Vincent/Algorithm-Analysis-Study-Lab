"""Tests for Discrete Math Foundations: safe parsing, equivalence-based grading, required forms, the exercise
bank (every answer, trap, model line and constant is checked), lessons, and the API integration with
progress, mastery, Review Mistakes and adaptive practice.

Run from the project root:
    python -m unittest discover -s tests -v
"""
import json
import os
import sys
import tempfile
import unittest
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from data import math_bank, math_lessons  # noqa: E402
from engine import mathfound as M, tnmath  # noqa: E402
from engine.catalog import MATH_TOPICS, MATH_TYPES  # noqa: E402
from engine.tnmath import ParseError  # noqa: E402


def eq(a, b):
    return M.equivalent(M.parse(a)[0], M.parse(b)[0])


def form(f, text):
    e, t = M.parse(text)
    return M.form_ok(f, t, e)


class ParserSafety(unittest.TestCase):
    def test_no_eval_in_math_modules(self):
        import ast
        for mod in ("engine/mathfound.py", "engine/tnmath.py"):
            with open(os.path.join(ROOT, mod), encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    f = node.func
                    name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
                    self.assertNotIn(name, ("eval", "exec", "sympify", "parse_expr", "__import__"), mod)

    def test_rejects_code_and_unknown_names(self):
        for text in ("__import__('os')", "os.system('ls')", "lambda: 1", "x.__class__", "open('f')", "z + 1", "2^(n^n)",
                     "x^(n^4)", "x^999", "", "   ", "1/0 +"):
            with self.assertRaises(ParseError, msg=text):
                M.parse(text)

    def test_algebra_mode_is_opt_in(self):
        with self.assertRaises(ParseError):
            tnmath.parse("2^(n+1)", ("n",))          # T(n) answers keep their stricter grammar
        self.assertEqual(str(tnmath.parse("2^(n+1)", ("n",), algebra=True).expr), "2*2**n")

    def test_input_conveniences(self):
        for a, b in [("x·4log(x)", "4x log(x)"), ("n²log(n⁵)", "5n^2 log(n)"), ("3 · 2ⁿ", "3*2^n"), ("log_2(n)", "log(n)"),
                     ("T(n) = 3n + 2", "3n+2"), ("n − 1", "n - 1"), ("log(√n)", "log(n)/2"), ("ln(2)n", "n ln(2)")]:
            self.assertTrue(eq(a, b), (a, b))


class Equivalence(unittest.TestCase):
    def test_spec_examples(self):
        for a in ("4x log(x)", "x*4log(x)", "4*x*log(x)", "x log(x^4)", "4 log(x) x"):
            self.assertTrue(eq(a, "4x log(x)"), a)
        for a in ("n(n+1)/2", "(n^2+n)/2", "0.5n^2+0.5n", "n^2/2 + n/2", "(n+1)n/2"):
            self.assertTrue(eq(a, "n(n + 1)/2"), a)
        for a in ("2^(2n)", "4^n", "2^n*2^n", "(2^n)^2"):
            self.assertTrue(eq(a, "(2^n)^2"), a)

    def test_non_equivalent(self):
        for a, b in [("log(4x)", "4log(x)"), ("n^2/2", "n(n+1)/2"), ("2^(n^2)", "2^(2n)"), ("log(n)^2", "2log(n)"),
                     ("n(n-1)/2", "n(n+1)/2"), ("2^n - 1", "2^(n-1)"), ("x^6", "x^5")]:
            self.assertFalse(eq(a, b), (a, b))

    def test_forms(self):
        self.assertTrue(form("expanded", "(n^2+n)/2"))
        self.assertTrue(form("expanded", "n^2/2 + n/2"))
        self.assertFalse(form("expanded", "n(n+1)/2"))
        self.assertTrue(form("factored", "3n(n+2)"))
        self.assertFalse(form("factored", "3n^2+6n"))
        self.assertTrue(form("log_simple", "4x log(x)"))
        self.assertFalse(form("log_simple", "x log(x^4)"))
        self.assertFalse(form("combined", "2n^2 + 3n^2 + 9n"))
        self.assertTrue(form("split_exp", "2*2^n"))
        self.assertFalse(form("split_exp", "2^(n+1)"))
        self.assertTrue(form("monomial", "9x^4y^2"))
        self.assertFalse(form("monomial", "x^2*x^2*9y^2"))
        self.assertTrue(form("positive_exp", "1/x^3"))
        self.assertFalse(form("positive_exp", "x^(-3)"))
        self.assertTrue(form("single_fraction", "(2n+1)/(n(n+1))"))
        self.assertFalse(form("single_fraction", "1/n + 1/(n+1)"))

    def test_grading_feedback(self):
        p = {"id": "a", "label": "L", "kind": "expr", "answer": "4x log(x)", "form": "log_simple",
             "traps": [["x*log(4x)", "exponent comes out"]]}
        self.assertTrue(M.grade_part(p, "x*4log(x)")["correct"])
        r = M.grade_part(p, "log(4x) x")
        self.assertFalse(r["correct"])
        self.assertEqual(r["why"], "exponent comes out")
        r = M.grade_part(p, "x log(x^4)")
        self.assertFalse(r["correct"])
        self.assertIn("Equal in value", r["why"])
        self.assertIn("Couldn't read", M.grade_part(p, "import os")["why"])
        self.assertFalse(M.grade_part(p, "")["correct"])

    def test_work_and_theta_and_constant(self):
        w = {"id": "w", "label": "W", "kind": "work", "start": "n(n-1)/2 + n", "model": ["n^2/2 + n/2"]}
        self.assertTrue(M.grade_part(w, "(n^2 - n)/2 + n\nn^2/2 + n/2")["correct"])
        r = M.grade_part(w, "(n^2 - n)/2 + n\n(n^2 - n + n)/2")
        self.assertFalse(r["correct"])
        self.assertIn("Line 2", r["why"])
        self.assertIn("at least 2", M.grade_part(w, "n^2/2 + n/2")["why"])
        t = {"id": "t", "label": "T", "kind": "theta", "answer": "n log(n)"}
        self.assertTrue(M.grade_part(t, "Θ(n log n)")["correct"])
        self.assertTrue(M.grade_part(t, "n*log(n)")["correct"])
        self.assertIn("Θ", M.grade_part(t, "O(n log n)")["why"])
        self.assertFalse(M.grade_part(t, "Θ(n^2)")["correct"])
        c = {"id": "c", "label": "C", "kind": "constant", "f": "3n + 5", "g": "n", "n0": 5, "answer": "4"}
        self.assertTrue(M.grade_part(c, "4")["correct"])
        self.assertTrue(M.grade_part(c, "10")["correct"])
        self.assertFalse(M.grade_part(c, "3")["correct"])


class Bank(unittest.TestCase):
    EX = math_bank.EXERCISES

    def test_size_and_coverage(self):
        self.assertGreaterEqual(len(self.EX), 100)
        self.assertEqual(len({e["id"] for e in self.EX}), len(self.EX))
        topics = Counter(e["topic"] for e in self.EX)
        self.assertEqual(set(topics), set(MATH_TOPICS))
        self.assertTrue(all(n >= 7 for n in topics.values()), topics)
        self.assertEqual({e["type"] for e in self.EX}, set(MATH_TYPES))
        self.assertGreaterEqual(topics["math_log"], 15, "logarithm rules get heavy practice")
        self.assertGreaterEqual(sum(1 for e in self.EX if e["type"] == "math_valid" and e["topic"] == "math_log"), 6)

    def test_varied_not_coefficient_clones(self):
        # exercises with the same shape after replacing every digit would be clones
        import re
        shapes = Counter(re.sub(r"\d+", "#", e["formula"] or e["title"]) for e in self.EX)
        self.assertLessEqual(max(shapes.values()), 2, shapes.most_common(3))

    def test_every_answer_trap_and_model(self):
        for e in self.EX:
            self.assertGreaterEqual(len(e["hints"]), 2, e["id"])
            self.assertTrue(e["steps"], e["id"])
            for p in e["parts"]:
                k = p["kind"]
                with self.subTest(ex=e["id"], part=p["id"]):
                    if k in ("expr", "theta", "constant"):
                        self.assertTrue(M.grade_part(p, p["answer"])["correct"])
                    if k == "expr":
                        for trap, msg in p.get("traps", []):
                            self.assertTrue(msg)
                            self.assertFalse(eq(trap, p["answer"]), f"trap {trap!r} equals the answer")
                    elif k == "work":
                        self.assertTrue(M.grade_part(p, "\n".join(p["model"]))["correct"])
                        final = next(q for q in e["parts"] if q["kind"] == "expr")
                        self.assertTrue(eq(p["start"], final["answer"]))
                    elif k == "choice":
                        self.assertIn(p["answer"], p["options"])
                    elif k == "order":
                        self.assertEqual(sorted(p["answer"]), sorted(p["options"]))

    def test_staged_and_rule_first(self):
        staged = [e for e in self.EX if e["staged"]]
        self.assertGreaterEqual(len(staged), 5)
        for e in staged:
            self.assertGreaterEqual(len(e["parts"]), 3)
        for e in self.EX:
            if e["type"] == "math_rule":
                self.assertEqual(e["parts"][0]["kind"], "choice", e["id"])

    def test_skills_are_known(self):
        for topic, skills in M.TOPIC_SKILLS.items():
            self.assertIn(topic, MATH_TOPICS)
            self.assertTrue(set(skills) <= set(M.SKILLS))
        from engine.proofs import SKILLS as PROOF_SKILLS
        self.assertFalse(set(M.SKILLS) & set(PROOF_SKILLS), "math skill keys must not collide with proof skills")
        self.assertEqual(set(M.SKILLS.values()), {
            "Exponent Rules", "Logarithm Rules", "Polynomial Simplification", "Distribution", "Factoring", "Fractions",
            "Arithmetic Sequences", "Arithmetic Series", "Geometric Sequences", "Summations", "Inequalities",
            "Growth-Rate Simplification", "Mixed Simplification"})


class Lessons(unittest.TestCase):
    def test_every_topic_has_a_complete_lesson(self):
        ids = {e["id"] for e in math_bank.EXERCISES}
        self.assertEqual({l["topic"] for l in math_lessons.LESSONS}, set(MATH_TOPICS))
        for l in math_lessons.LESSONS:
            self.assertTrue(l["intro"] and l["meaning"] and l["rules"] and l["application_text"], l["topic"])
            self.assertEqual(len(l["examples"]), 2)
            for key in ("guided", "independent", "application"):
                self.assertIn(l[key], ids, (l["topic"], key))
        names = [s[0] for s in math_lessons.RULES_SHEET]
        for needed in ("Exponents", "Logarithms", "Summations", "Arithmetic sequences & series"):
            self.assertIn(needed, names)


def fresh_db(name):
    return os.path.join(tempfile.mkdtemp(), name + ".db")


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        cls.app = create_app(db_path=fresh_db("mathfound"), env="testing")

    def setUp(self):
        self.c = self.app.test_client()

    def submit(self, ex_id, parts, inst, context="free"):
        return self.c.post(f"/api/exercise/{ex_id}/submit", json={"answer": {"parts": parts}, "instance_id": inst, "context": context}).get_json()

    def test_pages(self):
        for url in ("/math", "/learn/math", "/learn/math/rules", "/learn/math/math_exp", "/learn/math/math_tn",
                    "/progress", "/review", "/", "/exercise/mf_exp_steps1"):
            self.assertEqual(self.c.get(url).status_code, 200, url)
        self.assertEqual(self.c.get("/learn/math/unknown").status_code, 404)
        page = self.c.get("/learn/math/math_log").get_data(as_text=True)
        for section in ("Worked examples", "Guided practice", "Independent practice", "Algorithm analysis application"):
            self.assertIn(section, page)
        self.assertIn("Discrete math", self.c.get("/learn").get_data(as_text=True))

    def test_public_view_hides_answers(self):
        for ex in math_bank.EXERCISES[::7]:
            v = self.c.get(f"/api/exercise/{ex['id']}").get_json()
            for p in v["parts"]:
                for key in ("answer", "why", "traps", "model"):
                    self.assertNotIn(key, p, (ex["id"], key))
            self.assertNotIn("steps", v)

    def test_wrong_answer_goes_to_review_with_category_and_mastery(self):
        r = self.submit("mf_log_xlogx4", {"p1": "x log(4x)"}, "m-1")
        self.assertFalse(r["correct"])
        self.assertIn("multiplier", r["parts"][0]["why"])
        self.assertTrue(r["locked"])
        self.assertTrue(r["solution"]["steps"])
        mist = [m for m in self.c.get("/api/mistakes?track=math").get_json() if m["exercise_id"] == "mf_log_xlogx4"]
        self.assertEqual(mist[0]["category_label"], "Logarithm rule misapplied")
        ok = self.submit("mf_log_xlogx4", {"p1": "4*x*log(x)"}, "m-2")
        self.assertTrue(ok["correct"])
        from engine import stats
        with self.app.app_context():
            log = next(m for m in stats.math_mastery() if m["skill"] == "m_log")
            self.assertEqual(log["answered"], 2)
            self.assertIn("math_log", stats.math_rule_accuracy())

    def test_staged_check_part(self):
        r = self.c.post("/api/exercise/mf_exp_steps1/check_part", json={"part": "p2", "value": "x^15"}).get_json()
        self.assertFalse(r["correct"])
        self.assertIn("ADDS", r["why"])
        r = self.c.post("/api/exercise/mf_exp_steps1/check_part", json={"part": "p2", "value": "x^3*x^5"}).get_json()
        self.assertFalse(r["correct"], "same value but not simplified to a single power")
        self.assertTrue(self.c.post("/api/exercise/mf_exp_steps1/check_part", json={"part": "p2", "value": "x^8"}).get_json()["correct"])

    def test_malformed_answers_do_not_crash(self):
        r = self.c.post("/api/exercise/mf_poly_work1/submit", json={"answer": {"parts": {"p1": {"x": 1}, "p2": ["a"]}}})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.get_json()["correct"])

    def test_practice_test_gives_no_feedback(self):
        r = self.submit("mf_frac_expand1", {"p1": "n(n+1)/2"}, "t-1", context="test")
        self.assertEqual(set(r), {"recorded", "attempt_no", "instance_id"})

    def test_sessions_include_math(self):
        s = self.c.post("/api/session", json={"mode": "adaptive", "topic": "math"}).get_json()
        self.assertEqual(s["pool_size"], len(math_bank.EXERCISES))
        nxt = self.c.post(f"/api/session/{s['id']}/next", json={}).get_json()
        self.assertTrue(nxt["exercise_id"].startswith("mf_"))
        s = self.c.post("/api/session", json={"mode": "practice", "track": "math", "subtopic": "math_gseq"}).get_json()
        self.assertEqual(s["pool_size"], sum(1 for e in math_bank.EXERCISES if e["topic"] == "math_gseq"))


if __name__ == "__main__":
    unittest.main()
