"""Tests for the Mock Exam mode: generation (balance, randomness, validation), grading with partial credit,
and the API (no answers leak before submission, autosave, flags, submission, history).

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

from engine import generator, mockexam as M, proofs as P, pseudo, tnmath  # noqa: E402


def inproc(src, tests, params, one_indexed):
    return pseudo.run_tests(src, tests, None, params, one_indexed=one_indexed)


def perfect_answer(q):
    """A full-credit answer built from the private key (what a strong student would write)."""
    k, cat, kind = q["key"], q["category"], q["kind"]
    if cat == "asym":
        V = k["var"]
        g = M._fn_text(M._expr(k["g"]), V)
        sym = M.REL_WORD[k["rel"]]
        a = {"reasoning": "for n > k each term <= its coefficient times g(n), so f(n) <= C g(n)", "conclusion": f"f({V}) is {sym}({g})"}
        a.update(k["witnesses"])
        if kind == "asym_prove":
            a["dominant"] = k["g"].replace("n", V) if V != "n" else k["g"]
            a["inequality"] = {"O": "f(n) <= C g(n)", "omega": "C g(n) <= f(n)", "theta": "C1 g(n) <= f(n) <= C2 g(n)"}[k["rel"]].replace("n", V)
        else:
            a["verdict"] = "True" if k["truth"] else "False"
            if not k["truth"]:
                a.update(reasoning="the ratio f/g grows without bound so no constant C works", conclusion="not true")
        return a
    if cat == "panalysis":
        return {"work": "inner loop runs n - i times; sum = n(n-1)/2", "T": k["T"], "bigo": "O(" + k["g_src"] + ")"}
    if cat == "design":
        a = {"code": k["ref"], "bigo": "O(" + k["classes"][0] + ")", "explain": "the loop runs n times, 1 comparison per iteration"}
        if k["follow"] == "trace":
            a["output"] = k["trace_output"]
        return a
    if kind == "seq":
        return {"d": str(k["d"]), "next": f"{k['next'][0]}, {k['next'][1]}", "nth": k["nth"], "a20": str(k["a20"])}
    if kind == "series":
        return {"count": k["count"], "closed": k["closed"], "simplified": tnmath.pretty(tnmath.parse(k["closed"], ("n",)).expr), "bigo": "Θ(n^2)"}
    if kind == "series_num":
        return {"count": str(k["count"]), "sum": str(k["sum"])}
    return {"terms": ", ".join(map(str, k["terms"])), "closed": k.get("closed", "")}


def first(exam_or_seed, pred, count=12, tries=60):
    for s in range(tries):
        for q in M.build_exam(count, s)["questions"]:
            if pred(q):
                return q
    raise AssertionError("no matching question generated")


# ============================================================================ generation
class TestGeneration(unittest.TestCase):
    def test_balanced_categories_and_count_option(self):
        for count, expected in [(12, {"asym": 3, "panalysis": 3, "design": 3, "discrete": 3}), (4, {c: 1 for c in M.ORDER}),
                                (20, {c: 5 for c in M.ORDER})]:
            ex = M.build_exam(count, 7)
            self.assertEqual(len(ex["questions"]), count)
            self.assertEqual(Counter(q["category"] for q in ex["questions"]), Counter(expected))
        ex = M.build_exam(14, 3)
        counts = Counter(q["category"] for q in ex["questions"]).values()
        self.assertEqual(max(counts) - min(counts), 1)
        self.assertEqual(len(M.build_exam(99, 1)["questions"]), 24)
        self.assertEqual(len(generator.mock_exam(8, 5)["questions"]), 8)

    def test_new_exam_each_time_but_reproducible_from_seed(self):
        a, b = M.build_exam(12, 1), M.build_exam(12, 2)
        self.assertNotEqual([q["text"] for q in a["questions"]], [q["text"] for q in b["questions"]])
        self.assertEqual([q["text"] for q in M.build_exam(12, 1)["questions"]], [q["text"] for q in a["questions"]])
        texts = [q["text"] for q in M.build_exam(12, None)["questions"]]
        self.assertEqual(len(texts), 12)

    def test_questions_validate_and_model_answers_earn_full_credit(self):
        kinds = Counter()
        for seed in range(25):
            for q in M.build_exam(12, seed)["questions"]:
                kinds[q["kind"]] += 1
                with self.subTest(seed=seed, kind=q["kind"], title=q["title"]):
                    full = M.grade_question(q, perfect_answer(q), inproc)
                    self.assertEqual(full["earned"], full["max"], [r for r in full["rubric"] if r["earned"] < r["max"]])
                    self.assertEqual(full["max"], M.POINTS)
                    blank = M.grade_question(q, {}, inproc)
                    self.assertEqual(blank["earned"], 0)
                    self.assertTrue(full["model"] and full["answer_key"])
        self.assertTrue({"asym_prove", "asym_decide", "panalysis", "design", "seq", "series", "series_num", "recur_add", "fib"} <= set(kinds))

    def test_show_that_claims_are_always_true(self):
        for seed in range(30):
            for q in M.build_exam(8, seed)["questions"]:
                if q["kind"] == "asym_prove":
                    k = q["key"]
                    self.assertTrue(P.relation_truth(M._expr(k["f"]), M._expr(k["g"]), k["rel"]))
                    self.assertTrue(q["text"].startswith("Show that"))
                if q["kind"] == "asym_decide":
                    self.assertIn("Decide", q["text"])

    def test_pseudocode_counts_match_a_real_run(self):
        import random
        for key in M.PANALYSIS_KEYS:
            t = M.PSEUDO_TEMPLATES_BY_KEY[key](random.Random(4))
            instr = M._render(t["name"], t["params"], t["lines"], instrumented=True)
            for nv in ([2, 4, 8] if t.get("big") else [4, 8, 16, 32]):
                with self.subTest(key=key, n=nv):
                    self.assertAlmostEqual(M.count_ops(instr, t["params"], nv), float(t["T"].subs(M.N, nv)))
            shown = M._render(t["name"], t["params"], t["lines"])
            self.assertIn("{basic operation}", shown)
            self.assertNotIn(" = ", shown.replace(":=", "").replace("if A[i] = A[j]", "").replace("A[i] + A[j] = 0", "")
                             .replace("A[mid] = x", ""))           # course notation: := for assignment

    def test_design_reference_solutions_pass_their_tests(self):
        import random
        for key in M.DESIGN_KEYS:
            q = M.gen_design(random.Random(9), key)        # gen_design asserts the model passes its tests
            self.assertIn("procedure", q["key"]["ref"])
            self.assertIn("A[1..n]", q["text"])

    def test_summation_closed_forms_are_correct(self):
        import random
        for s in range(40):
            q = M.gen_discrete(random.Random(s), "series")
            closed = tnmath.parse(q["key"]["closed"], ("n",)).expr
            r = q["key"]["rule"]
            for nv in range(1, 12):
                direct = sum(r["c"] * i + r["b"] for i in range(r["lo"], nv + r["hi_off"] + 1))
                self.assertEqual(closed.subs(M.N, nv), direct)
            self.assertIn("(number of terms)(first term + last term)/2", q["text"])

    def test_public_questions_hide_answers(self):
        for q in M.build_exam(12, 11)["questions"]:
            pub = json.dumps(M.public_question(q), ensure_ascii=False)
            self.assertNotIn('"key"', pub)
            for secret in ("witnesses", "model", "trace_output", "ref"):
                self.assertNotIn(f'"{secret}"', pub)


# ============================================================================ partial credit
class TestGrading(unittest.TestCase):
    def test_asymptotic_partial_credit(self):
        q = first(None, lambda q: q["kind"] == "asym_prove" and q["key"]["rel"] == "O" and q["key"]["g"] == "n^2")
        k = q["key"]
        good = perfect_answer(q)
        rev = dict(good, inequality="C g(n) <= f(n)".replace("n", k["var"]))
        r = M.grade_question(q, rev, inproc)
        self.assertEqual(r["earned"], 4)
        self.assertIn("reversed", " ".join(x["note"] for x in r["rubric"]))
        small = dict(good, C="1", k="0")                       # works only on a finite range (or not at all)
        r = M.grade_question(q, small, inproc)
        wit = next(x for x in r["rubric"] if x["label"].startswith("Appropriate witnesses"))
        self.assertEqual(wit["earned"], 0)
        self.assertEqual(r["earned"], 4)
        other = dict(good, C="1000", k="50")                    # any valid witnesses are accepted
        self.assertEqual(M.grade_question(q, other, inproc)["earned"], 5)

    def test_decide_question_needs_the_right_verdict(self):
        q = first(None, lambda q: q["kind"] == "asym_decide" and not q["key"]["truth"])
        r = M.grade_question(q, dict(perfect_answer(q), verdict="True"), inproc)
        self.assertEqual(r["earned"], 0)

    def test_pseudocode_analysis_partial_credit(self):
        q = first(None, lambda q: q["kind"] == "panalysis" and q["key"]["g"] == "n²")
        loose = dict(perfect_answer(q), bigo="O(n^3)")
        r = M.grade_question(q, loose, inproc)
        self.assertEqual(r["rubric"][0]["earned"], 1)            # valid but not tight
        lead = dict(perfect_answer(q), T="n^2/2")
        r = M.grade_question(q, lead, inproc)
        self.assertIn(r["rubric"][1]["earned"], (0.5, 1))
        r = M.grade_question(q, {"bigo": "Θ(n²)"}, inproc)
        self.assertEqual(r["earned"], 3)

    def test_design_is_forgiving_about_minor_differences(self):
        q = first(None, lambda q: q["kind"] == "design" and q["key"]["tmpl"] == "largest")
        zero_based = """procedure biggest(A)
    best := A[0]
    for i = 1 to length(A) - 1
        if A[i] > best
            best = A[i]
    return best"""
        a = dict(perfect_answer(q), code=zero_based)
        r = M.grade_question(q, a, inproc)
        self.assertEqual([x["earned"] for x in r["rubric"][:3]], [1, 1, 1])     # 0-indexed, no n parameter, = for := : fine
        buggy = q["key"]["ref"].replace("A[i] > max", "A[i] < max")
        r = M.grade_question(q, dict(perfect_answer(q), code=buggy), inproc)
        self.assertEqual(r["rubric"][1]["earned"], 1)            # structure right
        self.assertEqual(r["rubric"][2]["earned"], 0)            # output wrong
        broken = "procedure largest(A, n)\n    max := A[1]\n    for each value v in A\n        if v > max then max := v\n    return max"
        r = M.grade_question(q, dict(perfect_answer(q), code=broken), inproc)
        self.assertGreaterEqual(r["earned"], 2)

    def test_trace_question(self):
        q = first(None, lambda q: q["kind"] == "design" and q["key"]["follow"] == "trace")
        r = M.grade_question(q, dict(perfect_answer(q), output="123456"), inproc)
        trace = next(x for x in r["rubric"] if x["label"] == "Correct traced output")
        self.assertEqual(trace["earned"], 0)

    def test_discrete_partial_credit(self):
        q = first(None, lambda q: q["kind"] == "series")
        k = q["key"]
        r = M.grade_question(q, {"count": k["count"], "closed": k["closed"], "bigo": "O(n^2)"}, inproc)
        self.assertEqual(r["earned"], 4)                         # no simplified form given
        q = first(None, lambda q: q["kind"] == "seq")
        r = M.grade_question(q, dict(perfect_answer(q), nth="2^n"), inproc)
        self.assertEqual(r["earned"], 3)


# ============================================================================ API
class TestMockAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.pop("BIGO_DB", None)
        from app import create_app
        cls.app = create_app(db_path=os.path.join(tempfile.mkdtemp(), "mock.db"), env="testing")

    def setUp(self):
        self.c = self.app.test_client()

    def post(self, url, body=None, ok=True):
        r = self.c.post(url, data=json.dumps(body or {}), content_type="application/json")
        if ok:
            self.assertLess(r.status_code, 400, r.data[:300])
        return r

    def test_full_exam_flow(self):
        self.assertEqual(self.c.get("/mock").status_code, 200)
        eid = self.post("/api/mock", {"count": 8}).get_json()["id"]
        self.assertEqual(self.c.get(f"/mock/{eid}").status_code, 200)
        self.assertEqual(self.c.get("/mock/doesnotexist").status_code, 404)
        view = self.c.get(f"/api/mock/{eid}").get_json()
        self.assertFalse(view["submitted"])
        self.assertEqual(len(view["questions"]), 8)
        blob = json.dumps(view, ensure_ascii=False)
        for secret in ('"key"', '"model"', '"witnesses"', '"results"', '"answer_key"'):
            self.assertNotIn(secret, blob)
        q1, q2 = view["questions"][0], view["questions"][1]
        self.post(f"/api/mock/{eid}/answer", {"qid": q1["qid"], "answer": {"conclusion": "draft"}})
        self.post(f"/api/mock/{eid}/answer", {"qid": q2["qid"], "flagged": True})
        self.post(f"/api/mock/{eid}/answer", {"qid": q1["qid"], "answer": {"conclusion": "final answer"}})
        view = self.c.get(f"/api/mock/{eid}").get_json()
        self.assertEqual(view["answers"][q1["qid"]], {"conclusion": "final answer"})       # work is kept
        self.assertEqual(view["flags"], [q2["qid"]])
        self.assertEqual(self.post(f"/api/mock/{eid}/answer", {"qid": "q99", "answer": {}}, ok=False).status_code, 400)
        res = self.post(f"/api/mock/{eid}/submit").get_json()
        self.assertTrue(res["submitted"])
        r = res["results"]
        self.assertEqual([c["label"] for c in r["categories"]], list(M.CATEGORIES.values()))
        self.assertEqual(len(r["questions"]), 8)
        for qr in r["questions"]:
            self.assertTrue(qr["rubric"] and qr["model"] and qr["answer_key"])
        self.assertEqual(self.post(f"/api/mock/{eid}/answer", {"qid": q1["qid"], "answer": {"x": "late"}}, ok=False).status_code, 400)
        again = self.post(f"/api/mock/{eid}/submit").get_json()           # idempotent
        self.assertEqual(again["results"]["score"], r["score"])
        hist = self.c.get("/api/mock").get_json()
        self.assertEqual(hist[0]["id"], eid)
        self.assertIn("Mock exams", self.c.get("/progress").get_data(as_text=True))

    def test_design_answers_are_graded_in_the_sandbox(self):
        eid = self.post("/api/mock", {"count": 4}).get_json()["id"]
        view = self.c.get(f"/api/mock/{eid}").get_json()
        dq = next(q for q in view["questions"] if q["category"] == "design")
        with self.app.test_request_context("/"):
            self.app.preprocess_request()
            import db
            key = next(q for q in db.get_mock_exam(eid)["questions"] if q["qid"] == dq["qid"])["key"]
        ans = {"code": key["ref"], "bigo": "O(" + key["classes"][0] + ")", "explain": "loop over all n elements once 1",
               "output": key.get("trace_output", "")}
        self.post(f"/api/mock/{eid}/answer", {"qid": dq["qid"], "answer": ans})
        res = self.post(f"/api/mock/{eid}/submit").get_json()["results"]
        qr = next(r for r in res["questions"] if r["qid"] == dq["qid"])
        self.assertEqual(qr["earned"], qr["max"], qr["rubric"])

    def test_reset_clears_mock_exams(self):
        self.post("/api/mock", {"count": 4})
        self.post("/api/reset", {"confirm": "RESET"})
        self.assertEqual(self.c.get("/api/mock").get_json(), [])


if __name__ == "__main__":
    unittest.main()
