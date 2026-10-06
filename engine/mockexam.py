"""Mock exam generator and grader.

Builds a fresh, balanced exam from four question families, in the style of the course's
Discrete Mathematics / Algorithm Analysis problems - questions that have to be worked, not recognised:

    asym       prove / decide f ∈ O, Ω, Θ (g) with witnesses C and k          (engine.proofs checks them)
    panalysis  pseudocode → count the basic operation → T(n) → Big-O           (counts verified by running it)
    design     English problem → pseudocode → complexity OR a hand trace       (graded by tests in the sandbox)
    discrete   arithmetic sequences / series, closed forms, recurrences        (closed forms derived with SymPy)

Every generated question is validated before it is returned: asymptotic claims against lim f/g, model
witnesses with the proof checker, T(n) formulas against an instrumented run of the pseudocode, reference
algorithms against their test cases, and summation closed forms against the terms themselves.
Student answers are read only through the app's safe parser and the sandboxed pseudocode interpreter.
"""
from __future__ import annotations

import math
import random
import re

import sympy as sp

from engine import proofs as P
from engine import pseudo, tnmath
from engine.grading import norm_code
from engine.tnmath import ParseError

N = P.N
POINTS = 5
CATEGORIES = {"asym": "Asymptotic Analysis", "panalysis": "Pseudocode Analysis",
              "design": "Algorithm Design", "discrete": "Discrete Mathematics"}
ORDER = ["asym", "panalysis", "design", "discrete"]
REL_WORD = {"O": "O", "omega": "Ω", "theta": "Θ"}
SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
LADDER = ["1", "log2(n)", "n", "n log2(n)", "n^2", "n^3", "n^4", "2^n", "n!"]


# ============================================================================ helpers
def _expr(text, growth=True):
    return tnmath.parse(text, ("n",), growth=growth).expr


def _fn_text(expr, var="n"):
    t = P.show(expr)
    return t.replace("n", var).replace("ⁿ", "ˣ") if var != "n" else t


def _student_expr(text, var="n", growth=True):
    """A student's expression (in n, or in x when the question uses x) or None."""
    s = str(text or "").strip()[:200]
    if not s:
        return None
    s = re.sub(r"^\s*[A-Za-z]\s*\(\s*[nx]\s*\)\s*=", "", s)          # 'T(n) =' / 'f(x) ='
    s = s.replace("ⁿ", "^n").replace("ˣ", "^x")
    if var == "x":
        s = s.replace("x", "n")
    s = s.replace("₁", "1").replace("₂", "2") if "log" not in s else s
    try:
        return tnmath.parse(s, ("n",), growth=growth).expr
    except ParseError:
        return None


def _number(text):
    s = str(text or "").strip().replace(",", "")[:40]
    if not s:
        return None
    try:
        e = tnmath.parse(s, (), growth=False).expr
    except ParseError:
        return None
    return e if e.is_number else None


def _equiv(a, b):
    return a is not None and b is not None and P._equiv(sp.expand(a), sp.expand(b))


BOUND_RE = re.compile(r"(big[\s-]*o|big[\s-]*theta|big[\s-]*omega|theta|omega|[OΘΩϴ])\s*\(", re.I)


def extract_bound(text):
    """'T(n) ∈ O(n^2)' -> ('O', 'n^2').  'n log n' -> (None, 'n log n')."""
    s = str(text or "")[:200]
    last = None
    for m in BOUND_RE.finditer(s):
        last = m
    if not last:
        return None, s
    word = last.group(1).lower().replace(" ", "").replace("-", "")
    rel = "theta" if ("theta" in word or word in ("θ", "ϴ")) else ("omega" if ("omega" in word or word == "ω") else "O")
    depth, start = 1, last.end()
    for i in range(start, len(s)):
        depth += {"(": 1, ")": -1}.get(s[i], 0)
        if depth == 0:
            return rel, s[start:i]
    return rel, s[start:]


def same_class(a, g):
    if a is None:
        return False
    L = P.ratio_limit(a, g)
    return L is not None and L != sp.oo and bool(L > 0)


def _class_expr(text, var="n"):
    rel, inner = extract_bound(text)
    return rel, _student_expr(inner, var)


def _has_math(text, minlen=8):
    t = str(text or "").strip()
    return len(t) >= minlen and bool(P.MATH_RE.search(t))


def _item(label, earned, mx, note=""):
    return {"label": label, "earned": round(earned, 2), "max": mx, "note": note}


# ============================================================================ 1. asymptotic notation
def _poly_terms(rng):
    d = rng.choice([1, 2, 2, 3, 3, 4])
    a = rng.randint(2, 9)
    terms = [(a, f"n^{d}" if d > 1 else "n")]
    if d >= 2 and rng.random() < 0.8:
        terms.append((rng.randint(1, 9), f"n^{d - 1}" if d - 1 > 1 else "n"))
    if d >= 3 and rng.random() < 0.4:
        terms.append((rng.randint(1, 9), "n"))
    terms.append((rng.randint(1, 20), ""))
    return terms, f"n^{d}" if d > 1 else "n"


def _mixed_terms(rng):
    kind = rng.choice(["n2_nlog", "nlog_n", "n_log", "exp_poly", "fact_exp", "n3_n2log"])
    a, b, c = rng.randint(2, 9), rng.randint(1, 9), rng.randint(1, 15)
    return {
        "n2_nlog": ([(a, "n^2"), (b, "n log2(n)")] + ([(c, "")] if rng.random() < 0.5 else []), "n^2"),
        "nlog_n": ([(a, "n log2(n)"), (b, "n"), (c, "")], "n log2(n)"),
        "n_log": ([(a, "n"), (b, "log2(n)")], "n"),
        "exp_poly": ([(a, "2^n"), (b, "n^3")], "2^n"),
        "fact_exp": ([(1, "n!"), (b, "2^n")], "n!"),
        "n3_n2log": ([(a, "n^3"), (b, "n^2 log2(n)"), (c, "")], "n^3"),
    }[kind]


def _terms_text(terms):
    parts = []
    for coef, mono in terms:
        if not mono:
            parts.append(str(coef))
        elif coef == 1:
            parts.append(mono)
        else:
            parts.append(f"{coef}{mono}" if not mono.startswith(("log", "2^")) else f"{coef}·{mono}")
    return " + ".join(parts).replace("·", "*")


def _witnesses(f, g, rel, terms=None):
    """Simple, validated witnesses (C, k) in the course's form: f(n) ≤ C·g(n) whenever n > k."""
    out, lines = {}, []
    sides = {"O": ["upper"], "omega": ["lower"], "theta": ["lower", "upper"]}[rel]
    g_t = P.show(g)
    for side in sides:
        c = k = None
        if side == "upper" and terms:
            c = sp.Integer(sum(co for co, _ in terms))
            ks = []
            for co, mono in terms:
                t = _expr(mono) if mono else sp.Integer(1)
                n0 = P.smallest_n0(t, g, sp.Integer(1), "upper")
                ks.append(n0 if n0 is not None else None)
            if None not in ks:
                k = max(ks) - 1
                parts = [f"{P.show(co * (_expr(mono) if mono else sp.Integer(1)))} ≤ {co if co != 1 else ''}{'·' if co != 1 else ''}{g_t}"
                         for co, mono in terms]
                lines.append(f"Upper bound: for n > {k}: " + ", ".join(parts) + ".")
                lines.append(f"So f(n) ≤ ({' + '.join(str(co) for co, _ in terms)})·{g_t} = {c}·{g_t}.")
        if side == "lower" and terms:
            lead = sum(co for co, mono in terms if mono and same_class(_expr(mono), g))
            if lead:
                c, k = sp.Integer(lead), 0
                lines.append(f"Lower bound: every term of f(n) is ≥ 0 for n > 0, so f(n) ≥ {lead}·{g_t} (drop the other terms).")
        n0 = (k + 1) if k is not None else None
        if c is None or n0 is None or not P.check_bound(f, g, c, n0, side)["ok"]:
            sug = P.suggest_constants(f, g, "O" if side == "upper" else "omega")
            c, n0 = sug["c"], sug["n0"]
            k = int(n0) - 1
            lines.append(f"{'Upper' if side == 'upper' else 'Lower'} bound: checking values shows "
                         f"{'f(n) ≤ ' + P.show(c) + '·' + g_t if side == 'upper' else P.show(c) + '·' + g_t + ' ≤ f(n)'} "
                         f"for every n > {k} (each step from n to n + 1 preserves it).")
        assert P.check_bound(f, g, c, int(k) + 1, side)["ok"]
        key = "C" if rel != "theta" else ("C2" if side == "upper" else "C1")
        out[key] = c
        out.setdefault("k", 0)
        out["k"] = max(out["k"], int(k))
    return out, lines


def gen_asym(rng, variant):
    var = rng.choice(["n", "n", "x"])
    terms, gtext = _poly_terms(rng) if variant in ("poly_O", "poly_omega", "poly_theta") or rng.random() < 0.45 \
        else _mixed_terms(rng)
    ftext = _terms_text(terms)
    f, g = _expr(ftext), _expr(gtext)
    f_t, V = _fn_text(f, var), var
    if variant == "decide":
        idx = LADDER.index(gtext)
        choice = rng.choice(["O_small", "O_big", "omega_big", "omega_small", "theta_other", "classic"])
        if choice == "classic":
            pick = rng.choice([("n^2", "n", "O"), ("n^3", "n^2", "O"), ("2^n", "n^3", "O"), ("n!", "2^n", "O"),
                               ("n", "n^2", "omega"), ("n log2(n)", "n", "theta"), ("n^2", "n^3", "O")])
            ftext, gq, rel = pick
            f = _expr(ftext)
            f_t = _fn_text(f, var)
            terms = None
        else:
            rel = {"O_small": "O", "O_big": "O", "omega_big": "omega", "omega_small": "omega", "theta_other": "theta"}[choice]
            step = -1 if choice in ("O_small", "omega_small") else 1
            if choice == "theta_other":
                step = rng.choice([-1, 1])
            j = min(max(idx + step, 0), len(LADDER) - 1)
            if j == idx:
                j = idx - 1 if idx > 0 else idx + 1
            gq = LADDER[j]
        gg = _expr(gq)
        truth = P.relation_truth(f, gg, rel)
        assert truth is not None
        g_t = _fn_text(gg, var)
        text = f"Is f({V}) = {f_t} ∈ {REL_WORD[rel]}({g_t})? Decide, and justify your answer mathematically: " \
               f"if it is true, give witnesses {'C₁, C₂ and k' if rel == 'theta' else 'C and k'}; if it is false, show that no witnesses can exist."
        key = {"f": ftext, "g": gq, "rel": rel, "truth": truth, "var": var, "terms": terms}
        model, wit = _asym_model(f, gg, rel, truth, terms, f_t, g_t, V)
        key.update(model=model, witnesses={k: str(v) for k, v in wit.items()})
        fields = [{"id": "verdict", "label": "Is the statement true?", "kind": "choice", "options": ["True", "False"]}]
        fields += _witness_fields(rel, optional=True)
        fields += [{"id": "reasoning", "label": "Justification (inequalities / why no witnesses exist)", "kind": "textarea"},
                   {"id": "conclusion", "label": "Conclusion", "kind": "text", "placeholder": f"e.g. f({V}) is {REL_WORD[rel]}({g_t}) / is not {REL_WORD[rel]}({g_t})"}]
        return {"category": "asym", "kind": "asym_decide", "title": f"Is f({V}) ∈ {REL_WORD[rel]}({g_t})?", "text": text,
                "fields": fields, "key": key}
    rel = {"poly_O": "O", "poly_omega": "omega", "poly_theta": "theta"}.get(variant, variant)
    assert P.relation_truth(f, g, rel)
    g_t = _fn_text(g, var)
    verb = {"O": "Show that", "omega": "Show that", "theta": "Show that"}[rel]
    need = {"O": f"Find witnesses C and k with |f({V})| ≤ C·|g({V})| whenever {V} > k.",
            "omega": f"Find witnesses C and k with |f({V})| ≥ C·|g({V})| whenever {V} > k.",
            "theta": f"Prove both an upper bound (witness C₂) and a lower bound (witness C₁) for {V} > k."}[rel]
    text = f"{verb} f({V}) = {f_t} is {REL_WORD[rel]}({g_t}). {need} Identify the dominant term, state the inequality, " \
           "justify it, and write your conclusion."
    model, wit = _asym_model(f, g, rel, True, terms, f_t, g_t, V)
    key = {"f": ftext, "g": gtext, "rel": rel, "truth": True, "var": var, "terms": terms, "model": model,
           "witnesses": {k: str(v) for k, v in wit.items()}}
    fields = [{"id": "dominant", "label": "Dominant term of f", "kind": "expr", "placeholder": "e.g. 8" + V + "^3"},
              {"id": "inequality", "label": "Inequality you will prove", "kind": "text",
               "placeholder": P.required_inequality(rel, f"f({V})", f"g({V})").replace("c₁", "C₁").replace("c₂", "C₂").replace("c·", "C·")}]
    fields += _witness_fields(rel)
    fields += [{"id": "reasoning", "label": "Reasoning (show the inequalities)", "kind": "textarea"},
               {"id": "conclusion", "label": "Conclusion", "kind": "text", "placeholder": f"f({V}) is {REL_WORD[rel]}({g_t})"}]
    return {"category": "asym", "kind": "asym_prove", "title": f"Show f({V}) is {REL_WORD[rel]}({g_t})", "text": text,
            "fields": fields, "key": key}


def _witness_fields(rel, optional=False):
    names = [("C1", "C₁"), ("C2", "C₂"), ("k", "k")] if rel == "theta" else [("C", "C"), ("k", "k")]
    return [{"id": i, "label": f"Witness {lab}" + (" (if true)" if optional else ""), "kind": "number"} for i, lab in names]


def _asym_model(f, g, rel, truth, terms, f_t, g_t, V):
    def v(t):
        return t.replace("n", V).replace("ⁿ", "ˣ") if V != "n" else t
    if truth:
        wit, lines = _witnesses(f, g, rel, terms)
        L = P.ratio_limit(f, g)
        head = {"O": f"Goal: |f({V})| ≤ C·|g({V})| for {V} > k.", "omega": f"Goal: C·|g({V})| ≤ |f({V})| for {V} > k.",
                "theta": f"Goal: C₁·g({V}) ≤ f({V}) ≤ C₂·g({V}) for {V} > k (upper AND lower bound)."}[rel]
        names = ", ".join(f"{k.replace('1', '₁').replace('2', '₂')} = {P.show(sp.nsimplify(val))}" for k, val in wit.items())
        dom = _dominant_text(f, terms)
        rel_word = {"O": "grows no faster than", "omega": "grows at least as fast as", "theta": "grows like"}[rel]
        if dom and same_class(_expr(dom[1]) if dom[1] else sp.Integer(1), g):
            rel_word = "grows like"
        dom_line = (f"Dominant term of f({V}) = {f_t}: {v(P.show(dom[0] * (_expr(dom[1]) if dom[1] else 1)))}, which {rel_word} {g_t}."
                    if dom else f"f({V}) = {f_t} {rel_word} {g_t}.")
        model = [dom_line, head] + [v(x) for x in lines] + \
                [f"Witnesses: {names}.", f"Conclusion: f({V}) is {REL_WORD[rel]}({g_t}).",
                 f"(Check by limits: lim f/g = {P.limit_text(L)}.)"]
        return model, wit
    L = P.ratio_limit(f, g)
    if rel == "O" or (rel == "theta" and L == sp.oo):
        model = [f"Suppose f({V}) ≤ C·g({V}) for all {V} > k.", f"Then f({V})/g({V}) ≤ C for all {V} > k.",
                 f"But f({V})/g({V}) → ∞ (lim f/g = ∞): it grows without bound and exceeds any fixed C.",
                 f"Contradiction - no witnesses exist, so f({V}) is not {REL_WORD[rel]}({g_t})."]
    else:
        model = [f"Suppose C·g({V}) ≤ f({V}) for all {V} > k, with C > 0.", f"Then f({V})/g({V}) ≥ C > 0 for all {V} > k.",
                 f"But f({V})/g({V}) → 0 (lim f/g = 0), so it eventually drops below C.",
                 f"Contradiction - no witnesses exist, so f({V}) is not {REL_WORD[rel]}({g_t})."]
    return model, {}


def _dominant_text(f, terms):
    """(coefficient, monomial text) of f's fastest-growing term, or None."""
    if not terms:
        return None
    best = None
    for co, mono in terms:
        e = _expr(mono) if mono else sp.Integer(1)
        if best is None or P.ratio_limit(e, _expr(best[1]) if best[1] else sp.Integer(1)) == sp.oo:
            best = (co, mono)
    return best


def _witness_check(f, g, rel, ans):
    """Returns (score 0..1, note) for the witnesses in ans (C/k or C1/C2/k), course form n > k."""
    k = _number(ans.get("k"))
    if k is None or k < 0:
        return 0.0, "k must be a number ≥ 0."
    n0 = int(math.floor(float(k))) + 1
    sides = {"O": [("upper", "C")], "omega": [("lower", "C")], "theta": [("lower", "C1"), ("upper", "C2")]}[rel]
    good, notes = 0, []
    for side, name in sides:
        c = _number(ans.get(name))
        if c is None or c <= 0:
            notes.append(f"{name} must be a positive number.")
            continue
        res = P.check_bound(f, g, c, n0, side)
        if res["ok"]:
            good += 1
        elif not res["eventually"]:
            notes.append(f"With {name} = {P.show(c)} the inequality works for a while but fails for larger n "
                         f"(first failure at n = {res['first_fail']}) - it must hold for EVERY n > k.")
        else:
            notes.append(f"With {name} = {P.show(c)} the inequality fails at n = {res['first_fail']}, which is > k. Choose a larger k.")
    return good / len(sides), " ".join(notes) or "Witnesses satisfy the definition."


def grade_asym(q, ans):
    key = q["key"]
    V = key["var"]
    f, g = _expr(key["f"]), _expr(key["g"])
    rel, rub = key["rel"], []
    conclusion = str(ans.get("conclusion") or "")
    if q["kind"] == "asym_prove":
        dom = _student_expr(ans.get("dominant"), V)
        rub.append(_item("Correct asymptotic class (dominant term)", 1 if same_class(dom, g) else 0, 1,
                         "" if same_class(dom, g) else f"The dominant term grows like {P.show(g)}."))
        ineq = str(ans.get("inequality") or "").replace("|", "")
        ineq = ineq.replace("x", "n") if V == "x" else ineq
        ineq = re.sub(r"\bC\s*₁|\bC1\b", "c1", ineq)
        ineq = re.sub(r"\bC\s*₂|\bC2\b", "c2", ineq)
        try:
            status, _ = P.classify_inequality(ineq, f, g, rel, key["f"], key["g"]) if ineq.strip() else ("empty", {})
        except ParseError:
            status = "parse"
        note = {"ok": "", "reversed": "The inequality is reversed for this notation.",
                "one_sided": "Θ needs both inequalities: C₁·g ≤ f ≤ C₂·g.", "empty": "No inequality given.",
                "parse": "The inequality couldn't be read."}.get(status, "State f(n) ≤ C·g(n) (O) or C·g(n) ≤ f(n) (Ω).")
        rub.append(_item("Correct inequality / direction", 1 if status == "ok" else 0, 1, note))
        w, wnote = _witness_check(f, g, rel, ans)
        rub.append(_item("Appropriate witnesses (C, k)", w, 1, wnote))
        rub.append(_item("Valid mathematical reasoning", 1 if _has_math(ans.get("reasoning"), 15) else 0, 1,
                         "" if _has_math(ans.get("reasoning"), 15) else "Show the inequalities that bound each term; 'grows slower' alone is intuition."))
        crel, cexp = _class_expr(conclusion, V)
        ok = crel in (rel, None) and crel is not None and same_class(cexp, g)
        rub.append(_item("Correct conclusion", 1 if ok else 0, 1, "" if ok else f"Conclude: f is {REL_WORD[rel]}({P.show(g)})."))
        return rub
    truth = key["truth"]
    verdict = ans.get("verdict")
    vok = (verdict == "True") == truth and verdict in ("True", "False")
    rub.append(_item("Correct decision (true / false)", 2 if vok else 0, 2, "" if vok else f"The statement is {'true' if truth else 'false'}."))
    if truth:
        w, wnote = _witness_check(f, g, rel, ans) if vok else (0.0, "Witnesses only count with the right decision.")
        rub.append(_item("Appropriate witnesses", 2 * w, 2, wnote))
        rub.append(_item("Valid reasoning", 1 if vok and _has_math(ans.get("reasoning"), 15) else 0, 1, ""))
    else:
        rok = vok and bool(P.DISPROOF_RE.search(str(ans.get("reasoning") or "")))
        rub.append(_item("Shows no witnesses can exist", 2 if rok else 0, 2,
                         "" if rok else "Argue that f(n)/g(n) is unbounded (or → 0), so no fixed C works."))
        cok = vok and bool(re.search(r"\bnot\b|∉|\bfalse\b|\bno\b|isn'?t", conclusion, re.I))
        rub.append(_item("Correct conclusion", 1 if cok else 0, 1, ""))
    return rub


# ============================================================================ 2. pseudocode → time complexity
def _L(indent, text, role="s"):
    return (indent, text, role)


def _pseudo_templates():
    """Each: rng -> dict(lines, T, g, pow2, derive, op). T is the exact count of the basic operation."""
    n = N
    lg = sp.log(n) / sp.log(2)

    def const(r):
        K = r.randint(3, 6)
        return dict(name="FirstSum", params="A, n", lines=[_L(1, "total := 0", "d"), _L(1, f"for i := 1 to {K}"),
                    _L(2, "total := total + A[i]", "op"), _L(1, "return total", "d")], T=sp.Integer(K), g=sp.Integer(1),
                    derive=[f"The loop runs i = 1, …, {K}: {K} times, no matter how large n is (assume n ≥ {K}).",
                            f"T(n) = {K}", "A constant number of operations ⇒ T(n) ∈ O(1)."], note=f"Assume n ≥ {K}.")

    def single(r):
        a, hi = r.choice([(1, "n"), (2, "n"), (1, "n - 1")])
        T = (n if hi == "n" else n - 1) - a + 1
        body = r.choice(["sum := sum + A[i]", "if A[i] < 0 then count := count + 1", "print(A[i])"])
        return dict(name="Scan", params="A, n", lines=[_L(1, "sum := 0", "d"), _L(1, "count := 0", "d"), _L(1, f"for i := {a} to {hi}"),
                    _L(2, body, "op")], T=sp.expand(T), g=n,
                    derive=[f"i takes the values {a}, {a + 1}, …, {hi}: that is {hi} − {a} + 1 = {tnmath.pretty(sp.expand(T))} iterations.",
                            f"T(n) = {tnmath.pretty(sp.expand(T))}", "Dominant term n ⇒ T(n) ∈ O(n)."])

    def down(r):
        return dict(name="Backwards", params="A, n", lines=[_L(1, "for i := n downto 1"), _L(2, "print(A[i])", "op")], T=n, g=n,
                    derive=["i = n, n − 1, …, 1: n iterations.", "T(n) = n", "T(n) ∈ O(n)."])

    def step2(r):
        return dict(name="EveryOther", params="A, n", lines=[_L(1, "sum := 0", "d"), _L(1, "i := 1"), _L(1, "while i ≤ n"),
                    _L(2, "sum := sum + A[i]", "op"), _L(2, "i := i + 2")], T=n / 2, g=n, note="Assume n is even.",
                    derive=["i = 1, 3, 5, …, n − 1: i grows by 2 each time.", "Number of iterations = n/2.", "T(n) = n/2",
                            "The constant 1/2 is dropped ⇒ T(n) ∈ O(n)."])

    def consec(r):
        if r.random() < 0.5:
            return dict(name="TwoPasses", params="A, n", lines=[_L(1, "for i := 1 to n"), _L(2, "count := count + 1", "op"),
                        _L(1, "for j := 1 to n"), _L(2, "count := count + 1", "op")], T=2 * n, g=n,
                        derive=["First loop: n iterations. Second loop (after it, not inside): n iterations.",
                                "Consecutive loops add: T(n) = n + n = 2n", "T(n) ∈ O(n)."])
        return dict(name="PassThenPairs", params="A, n", lines=[_L(1, "for i := 1 to n"), _L(2, "count := count + 1", "op"),
                    _L(1, "for i := 1 to n"), _L(2, "for j := 1 to n"), _L(3, "count := count + 1", "op")], T=n ** 2 + n, g=n ** 2,
                    derive=["First loop: n. Then a nested pair of loops: n · n = n².", "T(n) = n² + n",
                            "Dominant term n² ⇒ T(n) ∈ O(n²)."])

    def nested(r):
        return dict(name="AllPairs", params="A, n", lines=[_L(1, "count := 0", "d"), _L(1, "for i := 1 to n"), _L(2, "for j := 1 to n"),
                    _L(3, "if A[i] = A[j] then count := count + 1", "op"), _L(1, "return count", "d")], T=n ** 2, g=n ** 2,
                    derive=["The inner loop runs n times for each of the n outer iterations.", "T(n) = n · n = n²", "T(n) ∈ O(n²)."])

    def tri_bubble(r):
        return dict(name="Sort", params="A, n", lines=[_L(1, "for i := 1 to n - 1"), _L(2, "for j := 1 to n - i"),
                    _L(3, "if A[j] > A[j + 1] then interchange A[j] and A[j + 1]", "op")], T=n * (n - 1) / 2, g=n ** 2,
                    derive=["For a fixed i the inner loop runs n − i times.", "T(n) = (n − 1) + (n − 2) + … + 2 + 1",
                            "= n(n − 1)/2   (arithmetic series: (number of terms)(first + last)/2 = (n − 1)(n − 1 + 1)/2)",
                            "= (n² − n)/2", "Dominant term n²/2 ⇒ T(n) ∈ O(n²)."])

    def tri_insert(r):
        return dict(name="Insert", params="A, n", lines=[_L(1, "for j := 2 to n"), _L(2, "for i := 1 to j - 1"),
                    _L(3, "if A[i] > A[j] then count := count + 1", "op")], T=n * (n - 1) / 2, g=n ** 2,
                    derive=["For a fixed j the inner loop runs j − 1 times.", "T(n) = 1 + 2 + … + (n − 1)", "= n(n − 1)/2 = (n² − n)/2",
                            "T(n) ∈ O(n²)."])

    def tri_pairs(r):
        return dict(name="DistinctPairs", params="A, n", lines=[_L(1, "for i := 1 to n"), _L(2, "for j := i + 1 to n"),
                    _L(3, "if A[i] + A[j] = 0 then count := count + 1", "op")], T=n * (n - 1) / 2, g=n ** 2,
                    derive=["For a fixed i, j runs from i + 1 to n: n − i times.", "T(n) = (n − 1) + (n − 2) + … + 1 + 0",
                            "= n(n − 1)/2 = (n² − n)/2", "T(n) ∈ O(n²)."])

    def tri_upto(r):
        return dict(name="Prefixes", params="A, n", lines=[_L(1, "for i := 1 to n"), _L(2, "for j := 1 to i"),
                    _L(3, "sum := sum + A[j]", "op")], T=n * (n + 1) / 2, g=n ** 2,
                    derive=["For a fixed i the inner loop runs i times.", "T(n) = 1 + 2 + … + n", "= n(n + 1)/2 = (n² + n)/2",
                            "T(n) ∈ O(n²)."])

    def doubling(r):
        return dict(name="Doubling", params="n", lines=[_L(1, "i := 1"), _L(1, "while i < n"), _L(2, "count := count + 1", "op"),
                    _L(2, "i := 2 · i")], T=lg, g=lg, note="Assume n is a power of 2.",
                    derive=["i takes the values 1, 2, 4, …, 2^(t−1) and stops once i = n.", "After t iterations i = 2ᵗ, so 2ᵗ = n gives t = log₂ n.",
                            "T(n) = log₂ n", "T(n) ∈ O(log n)."])

    def halving(r):
        return dict(name="Halving", params="n", lines=[_L(1, "i := n"), _L(1, "while i > 1"), _L(2, "count := count + 1", "op"),
                    _L(2, "i := ⌊i / 2⌋")], T=lg, g=lg, note="Assume n is a power of 2.",
                    derive=["i = n, n/2, n/4, …, 2 - each iteration halves i until it reaches 1.", "n/2ᵗ = 1 gives t = log₂ n.",
                            "T(n) = log₂ n", "T(n) ∈ O(log n)."])

    def nlogn(r):
        if r.random() < 0.5:
            lines = [_L(1, "for i := 1 to n"), _L(2, "j := 1"), _L(2, "while j < n"), _L(3, "count := count + 1", "op"), _L(3, "j := 2 · j")]
            d = ["The outer loop runs n times.", "For each i, the inner while loop doubles j from 1 until it reaches n: log₂ n times."]
        else:
            lines = [_L(1, "i := n"), _L(1, "while i > 1"), _L(2, "for j := 1 to n"), _L(3, "count := count + 1", "op"), _L(2, "i := ⌊i / 2⌋")]
            d = ["The outer loop halves i from n down to 1: log₂ n iterations.", "Each of them runs the inner loop n times."]
        return dict(name="LogLinear", params="n", lines=lines, T=n * lg, g=n * lg, note="Assume n is a power of 2.",
                    derive=d + ["Nested loops multiply: T(n) = n · log₂ n", "T(n) ∈ O(n log n)."])

    def lin_log(r):
        return dict(name="ScanThenHalve", params="A, n", lines=[_L(1, "for i := 1 to n"), _L(2, "sum := sum + A[i]", "op"),
                    _L(1, "i := n"), _L(1, "while i > 1"), _L(2, "count := count + 1", "op"), _L(2, "i := ⌊i / 2⌋")], T=n + lg, g=n,
                    note="Assume n is a power of 2.",
                    derive=["First loop: n iterations. Then a separate halving loop: log₂ n iterations.", "T(n) = n + log₂ n",
                            "n dominates log₂ n ⇒ T(n) ∈ O(n)."])

    def matrix(r):
        return dict(name="MatrixMultiply", params="A, B, n", lines=[_L(1, "for i := 1 to n"), _L(2, "for j := 1 to n"),
                    _L(3, "C[i][j] := 0", "d"), _L(3, "for k := 1 to n"), _L(4, "C[i][j] := C[i][j] + A[i][k] · B[k][j]", "op"),
                    _L(1, "return C", "d")], T=n ** 3, g=n ** 3, big=True,
                    derive=["Three nested loops, each running n times, independent of each other.", "T(n) = n · n · n = n³",
                            "T(n) ∈ O(n³)."])

    return [("const", const, 1), ("single", single, 1), ("down", down, 1), ("step2", step2, 2), ("consec", consec, 2),
            ("nested", nested, 2), ("tri_bubble", tri_bubble, 3), ("tri_insert", tri_insert, 3), ("tri_pairs", tri_pairs, 3),
            ("tri_upto", tri_upto, 3), ("doubling", doubling, 2), ("halving", halving, 2), ("nlogn", nlogn, 3),
            ("lin_log", lin_log, 3), ("matrix", matrix, 3)]


PSEUDO_TEMPLATES = _pseudo_templates()


def _render(name, params, lines, instrumented=False):
    out = [f"procedure {name}({params})"]
    if instrumented:
        out.append("    ops := 0")
    else:                                    # no variable is used before it has a value
        body = " ".join(t for _, t, _ in lines)
        for acc in ("count", "sum", "total"):
            if re.search(rf"\b{acc}\b", body) and not any(t.strip() == f"{acc} := 0" for _, t, _ in lines):
                out.append(f"    {acc} := 0")
    for ind, text, role in lines:
        if instrumented:
            if role == "d":
                continue
            if role == "op":
                text = "ops := ops + 1"
        elif role == "op":
            text += "      {basic operation}"
        out.append("    " * ind + text)
    if instrumented:
        out.append("    return ops")
    return "\n".join(out)


def count_ops(code_instr, params, nval):
    """Run the instrumented (trusted, generated) code and return the operation count."""
    names = [p.strip() for p in params.split(",")]
    args = [list(range(nval)) if p != "n" else nval for p in names]
    old = pseudo._state.limit
    pseudo._state.limit = 5_000_000
    try:
        prog = pseudo.Program(code_instr)
        fn = prog.find_entry()
        res = prog.call(fn, [pseudo.to_plist(a) for a in args])
    finally:
        pseudo._state.limit = old
    return int(pseudo.normalize(res))


def gen_panalysis(rng, key):
    tmpl = dict(PSEUDO_TEMPLATES_BY_KEY[key](rng))
    code = _render(tmpl["name"], tmpl["params"], tmpl["lines"])
    instr = _render(tmpl["name"], tmpl["params"], tmpl["lines"], instrumented=True)
    pow2 = "power of 2" in tmpl.get("note", "")
    samples = [2, 4, 8, 16] if tmpl.get("big") else ([4, 8, 16, 32, 64] if pow2 or "even" in tmpl.get("note", "") else [6, 7, 10, 13, 16])
    for nv in samples:                                   # validate the closed form against an actual run
        assert abs(count_ops(instr, tmpl["params"], nv) - float(sp.N(tmpl["T"].subs(N, nv), 30))) < 1e-9, (key, nv)
    assert same_class(tmpl["T"], tmpl["g"])
    T_t, g_t = tnmath.pretty(sp.expand(tmpl["T"])), P.show(tmpl["g"])
    text = ("Let T(n) be the number of times the line marked {basic operation} is executed. "
            "Count the iterations of each loop in the workspace, write T(n) as a sum if needed, simplify it to a closed form, "
            "and give the tightest Big-O class." + (f" {tmpl['note']}" if tmpl.get("note") else ""))
    fields = [{"id": "work", "label": "Workspace: derive the operation count", "kind": "textarea",
               "placeholder": "e.g. inner loop runs n − i times\nT(n) = (n − 1) + (n − 2) + … + 1 = n(n − 1)/2 = (n² − n)/2"},
              {"id": "T", "label": "T(n) in closed form", "kind": "expr", "placeholder": "e.g. n(n - 1)/2"},
              {"id": "bigo", "label": "Big-O class", "kind": "text", "placeholder": "e.g. O(n^2)"}]
    key_data = {"T": str(sp.expand(tmpl["T"])).replace("**", "^"), "T_text": T_t, "g": g_t, "g_src": _src(tmpl["g"]),
                "model": tmpl["derive"] + [f"T(n) = {T_t} ∈ O({g_t})."]}
    return {"category": "panalysis", "kind": "panalysis", "title": f"Analyze {tmpl['name']}", "text": text, "code": code,
            "fields": fields, "key": key_data}


def _src(expr):
    """Re-parseable text for a growth class built here (n, n^2, log2(n), n log2(n), 1)."""
    s = str(sp.simplify(expr)).replace("**", "^").replace("log(n)/log(2)", "log2(n)").replace("*", " ")
    return s


PSEUDO_TEMPLATES_BY_KEY = {k: f for k, f, _ in PSEUDO_TEMPLATES}


def grade_panalysis(q, ans):
    key = q["key"]
    T = tnmath.parse(key["T"], ("n",)).expr
    g = _expr(key["g_src"])
    rub = []
    rel, cexp = _class_expr(ans.get("bigo"), "n")
    if same_class(cexp, g) and rel in ("O", "theta", None):
        rub.append(_item("Correct time complexity", 3, 3))
    elif cexp is not None and P.relation_truth(T, cexp, "O"):
        rub.append(_item("Correct time complexity", 1, 3, f"O({P.show(cexp)}) is a valid upper bound but not the tightest: O({key['g']})."))
    else:
        rub.append(_item("Correct time complexity", 0, 3, f"The tightest class is O({key['g']})."))
    st = _student_expr(ans.get("T"), "n", growth=False)
    if _equiv(st, T):
        rub.append(_item("Correct operation count T(n)", 1, 1))
    elif st is not None and P.ratio_limit(st, T) == 1:
        rub.append(_item("Correct operation count T(n)", 0.5, 1, f"Right dominant term; the exact count is {key['T_text']}."))
    else:
        rub.append(_item("Correct operation count T(n)", 0, 1, f"T(n) = {key['T_text']}."))
    rub.append(_item("Derivation shown in the workspace", 1 if _has_math(ans.get("work"), 10) else 0, 1,
                     "" if _has_math(ans.get("work"), 10) else "Count the loop iterations (and sum them) in the workspace."))
    return rub


# ============================================================================ 3. English → pseudocode → analysis
def _arr(r, lo=-9, hi=20, nmin=1, nmax=8):
    return [r.randint(lo, hi) for _ in range(r.randint(nmin, nmax))]


def _design_templates():
    T = []

    titles = {"largest": "Largest element", "smallest": "Smallest element", "negatives": "Count the negative values",
              "sum_even": "Sum of the even numbers", "greater_k": "Count values greater than k",
              "multiples": "Sum of the multiples of d", "position": "Position of the first occurrence",
              "sorted_search": "Search a sorted list", "pairs_equal": "Count equal pairs", "pair_sum": "Is there a pair with sum t?",
              "increasing": "Is the list increasing?", "count_x": "Count occurrences of x"}

    def add(key, text, name, extra, ref, py, classes, needs_if=True, arrays=None, extra_gen=None, expl=""):
        T.append(dict(key=key, title=titles[key], text=text, name=name, extra=extra, ref=ref, py=py, classes=classes,
                      needs_if=needs_if, arrays=arrays, extra_gen=extra_gen, expl=expl))

    add("largest", "Write an algorithm that finds the largest element in a list of n integers A[1..n] (n ≥ 1). Return it.",
        "largest", [], """procedure largest(A, n)
    max := A[1]
    for i := 2 to n
        if A[i] > max then max := A[i]
    return max""", lambda A: max(A), ["n"], expl="One pass over the list: n − 1 comparisons ⇒ O(n).")
    add("smallest", "Write an algorithm that returns the smallest element of a list A[1..n] of n integers (n ≥ 1).",
        "smallest", [], """procedure smallest(A, n)
    min := A[1]
    for i := 2 to n
        if A[i] < min then min := A[i]
    return min""", lambda A: min(A), ["n"], expl="One pass, n − 1 comparisons ⇒ O(n).")
    add("negatives", "Write an algorithm that counts how many negative values occur in an array A[1..n] and returns that count.",
        "countNegatives", [], """procedure countNegatives(A, n)
    count := 0
    for i := 1 to n
        if A[i] < 0 then count := count + 1
    return count""", lambda A: sum(1 for a in A if a < 0), ["n"], expl="Each of the n elements is checked once ⇒ O(n).")
    add("sum_even", "Write an algorithm that returns the sum of all even numbers in a list A[1..n].", "sumEven", [], """procedure sumEven(A, n)
    sum := 0
    for i := 1 to n
        if A[i] mod 2 = 0 then sum := sum + A[i]
    return sum""", lambda A: sum(a for a in A if a % 2 == 0), ["n"], expl="One test and at most one addition per element ⇒ O(n).")
    add("greater_k", "Write an algorithm that returns how many elements of A[1..n] are greater than a given value k.", "countGreater", ["k"],
        """procedure countGreater(A, n, k)
    count := 0
    for i := 1 to n
        if A[i] > k then count := count + 1
    return count""", lambda A, k: sum(1 for a in A if a > k), ["n"], extra_gen=lambda r: [r.randint(0, 10)],
        expl="One comparison per element ⇒ O(n).")
    add("multiples", "Write an algorithm that returns the sum of the elements of A[1..n] that are multiples of a given number d.",
        "sumMultiples", ["d"], """procedure sumMultiples(A, n, d)
    sum := 0
    for i := 1 to n
        if A[i] mod d = 0 then sum := sum + A[i]
    return sum""", lambda A, d: sum(a for a in A if a % d == 0), ["n"], extra_gen=lambda r: [r.choice([3, 4, 5])],
        expl="One test per element ⇒ O(n).")
    add("position", "Write an algorithm that returns the position of the first occurrence of a value x in A[1..n], or 0 if x does not occur.",
        "position", ["x"], """procedure position(A, n, x)
    for i := 1 to n
        if A[i] = x then return i
    return 0""", lambda A, x: next((i + 1 for i, a in enumerate(A) if a == x), 0), ["n"],
        extra_gen=None, expl="Worst case (x absent): all n elements are compared ⇒ O(n).")
    add("sorted_search", "Write an algorithm that determines whether a target value x occurs in a sorted list A[1..n] "
        "(increasing order). Return true or false.", "search", ["x"], """procedure search(A, n, x)
    low := 1
    high := n
    while low ≤ high
        mid := ⌊(low + high) / 2⌋
        if A[mid] = x then return true
        else if A[mid] < x then low := mid + 1
        else high := mid - 1
    return false""", lambda A, x: x in A, ["log2(n)", "n"], arrays="sorted",
        expl="Binary search halves the range each time ⇒ O(log n). (A linear scan also works, but is O(n).)")
    add("pairs_equal", "Write an algorithm that compares every pair of elements A[i], A[j] with i < j and returns how many pairs are equal.",
        "equalPairs", [], """procedure equalPairs(A, n)
    count := 0
    for i := 1 to n - 1
        for j := i + 1 to n
            if A[i] = A[j] then count := count + 1
    return count""", lambda A: sum(1 for i in range(len(A)) for j in range(i + 1, len(A)) if A[i] == A[j]), ["n^2"],
        arrays="small", expl="(n − 1) + (n − 2) + … + 1 = n(n − 1)/2 comparisons ⇒ O(n²).")
    add("pair_sum", "Write an algorithm that compares every pair of distinct positions i < j and returns true if some pair "
        "has A[i] + A[j] = t, and false otherwise.", "hasPairSum", ["t"], """procedure hasPairSum(A, n, t)
    for i := 1 to n - 1
        for j := i + 1 to n
            if A[i] + A[j] = t then return true
    return false""", lambda A, t: any(A[i] + A[j] == t for i in range(len(A)) for j in range(i + 1, len(A))), ["n^2"],
        extra_gen=lambda r: [r.randint(0, 15)], expl="Worst case checks all n(n − 1)/2 pairs ⇒ O(n²).")
    add("increasing", "Write an algorithm that returns true if A[1..n] is in increasing order (A[1] ≤ A[2] ≤ … ≤ A[n]) and false otherwise.",
        "isIncreasing", [], """procedure isIncreasing(A, n)
    for i := 1 to n - 1
        if A[i] > A[i + 1] then return false
    return true""", lambda A: all(A[i] <= A[i + 1] for i in range(len(A) - 1)), ["n"], arrays="mostly_sorted",
        expl="At most n − 1 neighbouring comparisons ⇒ O(n).")
    add("count_x", "Write an algorithm that counts how many times a value x occurs in A[1..n].", "occurrences", ["x"],
        """procedure occurrences(A, n, x)
    count := 0
    for i := 1 to n
        if A[i] = x then count := count + 1
    return count""", lambda A, x: sum(1 for a in A if a == x), ["n"], arrays="small", expl="One comparison per element ⇒ O(n).")
    return T


DESIGN_TEMPLATES = _design_templates()
DESIGN_BY_KEY = {t["key"]: t for t in DESIGN_TEMPLATES}


def _make_array(r, kind):
    if kind == "sorted":
        return sorted(r.sample(range(-5, 40), r.randint(1, 9)))
    if kind == "small":
        return [r.randint(0, 4) for _ in range(r.randint(2, 7))]
    if kind == "mostly_sorted":
        a = sorted(_arr(r, 0, 20, 2, 8))
        if r.random() < 0.5 and len(a) > 2:
            i = r.randrange(len(a) - 1)
            a[i], a[i + 1] = a[i + 1], a[i]
        return a
    return _arr(r)


def _design_tests(t, r):
    tests = []
    for i in range(7):
        A = _make_array(r, t["arrays"])
        if t["key"] == "negatives" and i == 0:
            A = [abs(x) + 1 for x in A]
        extra = t["extra_gen"](r) if t["extra_gen"] else []
        if t["key"] in ("position", "count_x", "sorted_search"):
            extra = [r.choice(A) if (i % 2 == 0 and A) else 99]
        tests.append({"A": A, "extra": extra, "expect": t["py"](A, *extra)})
    return tests


def gen_design(rng, key):
    t = DESIGN_BY_KEY[key]
    tests = _design_tests(t, rng)
    params = ["A", "n"] + t["extra"]
    run = [{"args": [c["A"], len(c["A"])] + c["extra"], "expect": c["expect"]} for c in tests]
    res = pseudo.run_tests(t["ref"], run, None, params, one_indexed=True)     # the model answer must pass its tests
    assert res["passed"] == res["total"], (key, res)
    follow = rng.choice(["complexity", "trace"])
    sig = f"procedure {t['name']}({', '.join(params)})"
    text = t["text"] + f" Use the class notation, e.g. {sig}, with A[1..n] indexed from 1."
    fields = [{"id": "code", "label": "Your pseudocode", "kind": "code", "placeholder": sig + "\n    "}]
    key_data = {"tmpl": key, "tests": tests, "params": params, "classes": t["classes"], "follow": follow, "ref": t["ref"],
                "expl": t["expl"], "needs_if": t["needs_if"]}
    if follow == "complexity":
        text += " Then determine the worst-case time complexity of YOUR algorithm and explain it (count the loop iterations)."
        fields += [{"id": "bigo", "label": "Time complexity of your algorithm", "kind": "text", "placeholder": "e.g. O(n)"},
                   {"id": "explain", "label": "Explanation", "kind": "textarea"}]
    else:
        A = _make_array(rng, t["arrays"])
        while len(A) < 5:
            A.append(rng.randint(0, 9) if t["arrays"] != "sorted" else (A[-1] + rng.randint(1, 4) if A else 1))
        if t["arrays"] == "sorted":
            A = sorted(set(A))
        extra = t["extra_gen"](rng) if t["extra_gen"] else []
        if key in ("position", "count_x", "sorted_search"):
            extra = [rng.choice(A)]
        out = t["py"](A, *extra)
        inp = f"A = {A}" + "".join(f", {nm} = {v}" for nm, v in zip(t["extra"], extra)) + f"  (n = {len(A)})"
        text += f" Then trace your pseudocode by hand on the input {inp} and state its output."
        fields += [{"id": "output", "label": f"Output for {inp}", "kind": "text"},
                   {"id": "explain", "label": "Trace work (variable values as the loop runs)", "kind": "textarea"}]
        key_data.update(trace_input=inp, trace_output=pseudo.fmt(out))
    return {"category": "design", "kind": "design", "title": t["title"], "text": text, "fields": fields, "key": key_data}


def _norm_out(s):
    s = str(s or "").strip().lower().strip(".")
    s = {"yes": "true", "no": "false", "t": "true", "f": "false"}.get(s, s)
    n = _number(s)
    return pseudo.fmt(n) if n is not None else s


def grade_design(q, ans, runner=None):
    """runner(src, tests, params, one_indexed) -> result (the sandbox in the app; in-process in tests)."""
    from engine.sandbox import run_tests as sandbox_run
    run_fn = runner or (lambda src, tests, params, oi: sandbox_run(src, tests, None, params, one_indexed=oi))
    key = q["key"]
    code = str(ans.get("code") or "")[:6000]
    best = None
    if code.strip():
        with_n = key["params"]
        without_n = [p for p in with_n if p != "n"]
        for params in (with_n, without_n):
            tests = [{"args": [c["A"]] + ([len(c["A"])] if "n" in params else []) + c["extra"], "expect": c["expect"]}
                     for c in key["tests"]]
            for oi in (True, False):                     # A[1..n] as in class, or 0-indexed - minor differences are fine
                r = run_fn(code, tests, params, oi)
                if best is None or r.get("passed", 0) > best.get("passed", 0) or (not best.get("runnable") and r.get("runnable")):
                    best = r
                if best.get("passed") == best.get("total"):
                    break
            if best and best.get("passed") == best.get("total"):
                break
    best = best or {"runnable": False, "passed": 0, "total": len(key["tests"]), "error": "No pseudocode written."}
    ratio = best.get("passed", 0) / max(1, best.get("total", 1))
    nc = norm_code(code)
    has_loop = bool(re.search(r"\b(for|while)\b", nc))
    has_if = bool(re.search(r"\bif\b", nc))
    has_out = bool(re.search(r"\breturn\b|\bprint\b|\boutput\b", nc))
    rub = []
    idea_ok = ratio >= 0.5 or (not best.get("runnable") and has_loop and (has_if or not key["needs_if"]) and has_out)
    rub.append(_item("Correct algorithmic idea", 1 if idea_ok else 0, 1,
                     f"Your algorithm passed {best.get('passed', 0)} of {best.get('total')} test inputs." if best.get("runnable")
                     else f"Couldn't run it ({best.get('error') or 'error'}); graded on structure."))
    struct = has_loop and (has_if or not key["needs_if"]) and has_out
    rub.append(_item("Correct loop / conditional structure", 1 if struct else 0, 1,
                     "" if struct else "Expected a loop over the list" + (", a condition" if key["needs_if"] else "") + " and a returned result."))
    rub.append(_item("Correct output on every test", 1 if ratio == 1 else 0, 1,
                     "" if ratio == 1 else _first_failure(best)))
    if key["follow"] == "complexity":
        rel, cexp = _class_expr(ans.get("bigo"), "n")
        ok = any(same_class(cexp, _expr(c)) for c in key["classes"])
        rub.append(_item("Correct time complexity", 1 if ok else 0, 1, "" if ok else "Expected " + " or ".join(
            f"O({P.show(_expr(c))})" for c in key["classes"]) + "."))
        ex = str(ans.get("explain") or "")
        eok = len(ex.strip()) >= 15 and bool(re.search(r"loop|iteration|times|pass|compar|n\b|\d|half|halv", ex, re.I))
        rub.append(_item("Reasonable explanation", 1 if eok else 0, 1, "" if eok else "Explain how many times the loop body runs."))
    else:
        ok = _norm_out(ans.get("output")) == _norm_out(key["trace_output"])
        rub.append(_item("Correct traced output", 1 if ok else 0, 1, "" if ok else f"The output is {key['trace_output']}."))
        ex = str(ans.get("explain") or "")
        eok = len(ex.strip()) >= 10 and bool(re.search(r"\d", ex))
        rub.append(_item("Trace work shown", 1 if eok else 0, 1, "" if eok else "Show the variable values step by step."))
    return rub


def _first_failure(res):
    if not res.get("runnable"):
        return res.get("error") or "The pseudocode couldn't be run."
    for t in res.get("results", []):
        if not t.get("ok"):
            return f"Input {t.get('input')}: expected {t.get('expected')}, got {t.get('error') or t.get('got')}."
    return ""


# ============================================================================ 4. discrete mathematics
def _series_text(c, b, lo, hi_off):
    """Terms c·i + b for i = lo .. n + hi_off, shown as 'a₁ + a₂ + a₃ + … + (last)'."""
    i = sp.Symbol("i")
    first = [c * k + b for k in range(lo, lo + 3)]
    last = sp.expand(c * (N + hi_off) + b)
    last_t = tnmath.pretty(last)
    return " + ".join(str(x) for x in first) + " + … + " + (f"({last_t})" if (" + " in last_t or " - " in last_t) else last_t), last, i


def gen_discrete(rng, key):
    if key == "seq":
        a, d = rng.randint(-5, 12), rng.choice([2, 3, 4, 5, 6, 7, -2, -3])
        terms = [a + d * k for k in range(4)]
        nth = sp.expand(a + d * (N - 1))
        text = (f"Consider the arithmetic sequence {', '.join(map(str, terms))}, … (first term a₁ = {a}). "
                "(a) Find the common difference. (b) Find the next two terms. (c) Find a formula for the nth term aₙ. "
                f"(d) Find a₂₀.")
        a20 = a + d * 19
        return {"category": "discrete", "kind": "seq", "title": "Arithmetic sequence", "text": text,
                "fields": [{"id": "d", "label": "(a) Common difference d", "kind": "number"},
                           {"id": "next", "label": "(b) Next two terms", "kind": "text", "placeholder": "e.g. 11, 13"},
                           {"id": "nth", "label": "(c) aₙ =", "kind": "expr", "placeholder": "in terms of n"},
                           {"id": "a20", "label": "(d) a₂₀ =", "kind": "number"}],
                "key": {"d": d, "next": [a + 4 * d, a + 5 * d], "nth": str(nth).replace("**", "^"), "a20": a20,
                        "model": [f"Each term is the previous one plus d = {d} (a constant difference ⇒ arithmetic, not geometric).",
                                  f"Next terms: {terms[-1]} + {d} = {a + 4 * d}, then {a + 5 * d}.",
                                  f"aₙ = a₁ + (n − 1)d = {a} + (n − 1)({d}) = {tnmath.pretty(nth)}.",
                                  f"a₂₀ = {a} + 19·({d}) = {a20}."]}}
    if key == "series":
        forms = [(1, 0, 1, 0), (1, 0, 1, -1), (2, 0, 1, 0), (2, 1, 1, 0), (2, -1, 1, 0), (3, 2, 1, 0),
                 (rng.randint(2, 6), rng.randint(-3, 5), 1, 0)]
        c, b, lo, hi_off = rng.choice(forms)
        if c * lo + b <= 0:
            b = 1 - c * lo + rng.randint(0, 3)
        text_series, last, i = _series_text(c, b, lo, hi_off)
        count = sp.expand(N + hi_off - lo + 1)
        closed = sp.factor(sp.summation(c * i + b, (i, lo, N + hi_off)))
        expanded = sp.expand(closed)
        first = c * lo + b
        assert sp.expand(count * (first + last) / 2 - expanded) == 0         # (terms)(first + last)/2 agrees
        for nv in range(1, 7):                                                 # and the terms themselves
            assert sum(c * k + b for k in range(lo, nv + hi_off + 1)) == expanded.subs(N, nv)
        text = (f"Evaluate the arithmetic series S = {text_series}. (a) How many terms are there? (b) Use "
                "S = (number of terms)(first term + last term)/2 to find a closed form. (c) Simplify it to a polynomial in n. "
                "(d) Give the asymptotic class of S as a function of n.")
        return {"category": "discrete", "kind": "series", "title": "Arithmetic series", "text": text,
                "fields": [{"id": "count", "label": "(a) Number of terms", "kind": "expr"},
                           {"id": "closed", "label": "(b) Closed form", "kind": "expr", "placeholder": "e.g. n(n + 1)/2"},
                           {"id": "simplified", "label": "(c) Simplified polynomial", "kind": "expr", "placeholder": "e.g. (n^2 + n)/2"},
                           {"id": "bigo", "label": "(d) Asymptotic class", "kind": "text", "placeholder": "e.g. Θ(n^2)"},
                           {"id": "work", "label": "Work", "kind": "textarea"}],
                "key": {"count": str(count).replace("**", "^"), "closed": str(expanded).replace("**", "^"),
                        "rule": {"c": c, "b": b, "lo": lo, "hi_off": hi_off},
                        "model": [f"Terms: first = {first}, last = {tnmath.pretty(last)}, common difference {c}.",
                                  f"Number of terms = {tnmath.pretty(count)}.",
                                  f"S = ({tnmath.pretty(count)})({first} + {tnmath.pretty(last)})/2 = {sp.sstr(closed).replace('**', '^').replace('*', '')}",
                                  f"= {tnmath.pretty(expanded)}", "Dominant term n²·(constant) ⇒ S ∈ Θ(n²)."]}}
    if key == "series_num":
        a, d = rng.randint(1, 12), rng.randint(2, 7)
        m = rng.randint(12, 30)
        last = a + d * (m - 1)
        total = m * (a + last) // 2
        assert total == sum(a + d * k for k in range(m))
        text = (f"Find the sum {a} + {a + d} + {a + 2 * d} + … + {last}. First determine how many terms there are, "
                "then use S = (number of terms)(first + last)/2.")
        return {"category": "discrete", "kind": "series_num", "title": "Sum of an arithmetic series", "text": text,
                "fields": [{"id": "count", "label": "Number of terms", "kind": "number"},
                           {"id": "sum", "label": "Sum", "kind": "number"}, {"id": "work", "label": "Work", "kind": "textarea"}],
                "key": {"count": m, "sum": total,
                        "model": [f"Common difference d = {d}; last = a₁ + (m − 1)d ⇒ {last} = {a} + (m − 1)·{d} ⇒ m = {m}.",
                                  f"S = {m}·({a} + {last})/2 = {total}."]}}
    if key == "recur_add":
        a0, c, b = rng.randint(0, 5), rng.choice([1, 2, 3]), rng.randint(0, 4)
        seq = [a0]
        for k in range(1, 6):
            seq.append(seq[-1] + c * k + b)
        k = sp.Symbol("k")
        closed = sp.expand(a0 + sp.summation(c * k + b, (k, 1, N)))
        assert all(closed.subs(N, j) == seq[j] for j in range(6))
        step = f"{c}n" if c != 1 else "n"
        step += f" + {b}" if b else ""
        text = (f"A sequence is defined recursively by a₀ = {a0} and aₙ = aₙ₋₁ + {step} for n ≥ 1. "
                "(a) Compute a₁, a₂, a₃ and a₄. (b) Unroll the recursion into a summation and find a closed form for aₙ.")
        return {"category": "discrete", "kind": "recur_add", "title": "Recursive definition", "text": text,
                "fields": [{"id": "terms", "label": "(a) a₁, a₂, a₃, a₄", "kind": "text", "placeholder": "e.g. 3, 7, 13, 21"},
                           {"id": "closed", "label": "(b) aₙ =", "kind": "expr"}, {"id": "work", "label": "Work", "kind": "textarea"}],
                "key": {"terms": seq[1:5], "closed": str(closed).replace("**", "^"),
                        "model": [f"a₁ … a₄ = {', '.join(map(str, seq[1:5]))}.",
                                  f"aₙ = a₀ + Σ_(k=1..n) ({step.replace('n', 'k')}) = {a0} + " +
                                  (f"{c}·n(n + 1)/2" if c != 1 else "n(n + 1)/2") + (f" + {b}n" if b else ""),
                                  f"= {tnmath.pretty(closed)}"]}}
    if key == "fib":
        p, q = rng.randint(0, 3), rng.randint(1, 4)
        mult = rng.choice([1, 1, 2])
        seq = [p, q]
        for _ in range(5):
            seq.append(seq[-1] + mult * seq[-2])
        rule = "fₙ = fₙ₋₁ + fₙ₋₂" if mult == 1 else "fₙ = fₙ₋₁ + 2fₙ₋₂"
        text = f"Let f₀ = {p}, f₁ = {q} and {rule} for n ≥ 2. Compute f₂, f₃, f₄, f₅ and f₆, showing each step."
        return {"category": "discrete", "kind": "fib", "title": "Fibonacci-style recurrence", "text": text,
                "fields": [{"id": "terms", "label": "f₂, f₃, f₄, f₅, f₆", "kind": "text"}, {"id": "work", "label": "Work", "kind": "textarea"}],
                "key": {"terms": seq[2:7],
                        "model": [f"f{j}".translate(SUB) + f" = {seq[j - 1]} + {'2·' if mult == 2 else ''}{seq[j - 2]} = {seq[j]}"
                                  for j in range(2, 7)]}}
    raise KeyError(key)


def _int_list(text):
    out = []
    for tok in re.split(r"[,\s;]+", str(text or "").strip()):
        if tok:
            v = _number(tok)
            out.append(v)
    return out


def grade_discrete(q, ans):
    k, kind, rub = q["key"], q["kind"], []
    if kind == "seq":
        d = _number(ans.get("d"))
        rub.append(_item("Common difference", 1 if d == k["d"] else 0, 1))
        nx = _int_list(ans.get("next"))
        rub.append(_item("Next two terms", 1 if nx[:2] == k["next"] and len(nx) >= 2 else 0, 1, f"{k['next'][0]}, {k['next'][1]}"))
        ok = _equiv(_student_expr(ans.get("nth"), "n", False), tnmath.parse(k["nth"], ("n",)).expr)
        rub.append(_item("Formula for aₙ", 2 if ok else 0, 2, "" if ok else "aₙ = a₁ + (n − 1)d."))
        rub.append(_item("a₂₀", 1 if _number(ans.get("a20")) == k["a20"] else 0, 1))
    elif kind == "series":
        cnt = tnmath.parse(k["count"], ("n",)).expr
        closed = tnmath.parse(k["closed"], ("n",)).expr
        rub.append(_item("Number of terms", 1 if _equiv(_student_expr(ans.get("count"), "n", False), cnt) else 0, 1))
        cl = _student_expr(ans.get("closed"), "n", False)
        rub.append(_item("Closed form", 2 if _equiv(cl, closed) else 0, 2, "" if _equiv(cl, closed) else "Use (terms)(first + last)/2."))
        simp = str(ans.get("simplified") or "")
        sexp = _student_expr(simp, "n", False)
        sok = False
        if _equiv(sexp, closed):
            try:
                sok = tnmath.is_simplified(tnmath.parse(re.sub(r"^\s*\((.*)\)\s*/\s*(\d+)\s*$", r"\1", simp), ("n",))) or \
                    tnmath.is_simplified(tnmath.parse(simp, ("n",)))
            except ParseError:
                sok = False
        rub.append(_item("Simplified polynomial", 1 if sok else 0, 1, "" if sok else f"= {tnmath.pretty(closed)}"))
        rel, cexp = _class_expr(ans.get("bigo"), "n")
        rub.append(_item("Asymptotic class", 1 if same_class(cexp, N ** 2) else 0, 1, "Θ(n²)"))
    elif kind == "series_num":
        rub.append(_item("Number of terms", 2 if _number(ans.get("count")) == k["count"] else 0, 2))
        rub.append(_item("Sum", 3 if _number(ans.get("sum")) == k["sum"] else 0, 3))
    elif kind == "recur_add":
        got = _int_list(ans.get("terms"))
        right = sum(1 for a, b in zip(got, k["terms"]) if a == b)
        rub.append(_item("a₁ … a₄", right / 2, 2, f"{', '.join(map(str, k['terms']))}"))
        ok = _equiv(_student_expr(ans.get("closed"), "n", False), tnmath.parse(k["closed"], ("n",)).expr)
        rub.append(_item("Closed form via the summation", 3 if ok else 0, 3, "" if ok else "Unroll: aₙ = a₀ + Σ (added terms)."))
    elif kind == "fib":
        got = _int_list(ans.get("terms"))
        right = sum(1 for a, b in zip(got, k["terms"]) if a == b)
        rub.append(_item("f₂ … f₆", right, 5, f"{', '.join(map(str, k['terms']))}"))
    return rub


# ============================================================================ the exam
ASYM_VARIANTS = ["poly_O", "poly_omega", "poly_theta", "O", "omega", "theta", "decide", "decide"]
PANALYSIS_KEYS = [k for k, _, _ in PSEUDO_TEMPLATES]
DESIGN_KEYS = [t["key"] for t in DESIGN_TEMPLATES]
DISCRETE_KEYS = ["seq", "series", "series", "series_num", "recur_add", "fib"]


def _pick(rng, pool, k):
    """k distinct picks when possible, then repeats - shuffled."""
    pool = list(pool)
    out = []
    while len(out) < k:
        rng.shuffle(pool)
        out += pool[: k - len(out)]
    return out


def build_exam(count=12, seed=None):
    """A balanced, validated exam: questions with private grading keys."""
    count = max(4, min(int(count), 24))
    seed = seed if seed is not None else random.randrange(10 ** 9)
    rng = random.Random(seed)
    per = {c: count // 4 for c in ORDER}
    for c in rng.sample(ORDER, count % 4):
        per[c] += 1
    qs = []
    for v in _pick(rng, ASYM_VARIANTS, per["asym"]):
        qs.append(_retry(lambda r, v=v: gen_asym(r, v), rng))
    keys = _pick(rng, PANALYSIS_KEYS, per["panalysis"])
    keys.sort(key=lambda k: dict((kk, lvl) for kk, _, lvl in PSEUDO_TEMPLATES)[k])
    for k in keys:
        qs.append(_retry(lambda r, k=k: gen_panalysis(r, k), rng))
    for k in _pick(rng, DESIGN_KEYS, per["design"]):
        qs.append(_retry(lambda r, k=k: gen_design(r, k), rng))
    for k in _pick(rng, DISCRETE_KEYS, per["discrete"]):
        qs.append(_retry(lambda r, k=k: gen_discrete(r, k), rng))
    for i, q in enumerate(qs, start=1):
        q["qid"] = f"q{i}"
        q["number"] = i
        q["points"] = POINTS
        q["category_label"] = CATEGORIES[q["category"]]
    return {"seed": seed, "count": count, "questions": qs}


def _retry(make, rng, tries=8):
    last = None
    for _ in range(tries):
        try:
            return make(random.Random(rng.randrange(10 ** 9)))
        except (AssertionError, ParseError, ValueError, TypeError, ZeroDivisionError) as e:   # regenerate on a failed check
            last = e
    raise RuntimeError(f"could not generate a valid question: {last!r}")


def public_question(q):
    return {k: q.get(k) for k in ("qid", "number", "category", "category_label", "kind", "title", "text", "code", "fields", "points")}


def grade_question(q, ans, runner=None):
    ans = ans if isinstance(ans, dict) else {}
    cat = q["category"]
    if cat == "asym":
        rub = grade_asym(q, ans)
    elif cat == "panalysis":
        rub = grade_panalysis(q, ans)
    elif cat == "design":
        rub = grade_design(q, ans, runner)
    else:
        rub = grade_discrete(q, ans)
    earned = round(sum(r["earned"] for r in rub), 2)
    mx = sum(r["max"] for r in rub)
    return {"qid": q["qid"], "earned": earned, "max": mx, "correct": earned >= mx, "rubric": rub,
            "model": model_solution(q), "answer_key": answer_key(q)}


def model_solution(q):
    k = q["key"]
    if q["category"] == "design":
        lines = ["Model algorithm:", k["ref"], k["expl"]]
        if k["follow"] == "trace":
            lines.append(f"Trace on {k['trace_input']}: output {k['trace_output']}.")
        return lines
    return k["model"]


def answer_key(q):
    k = q["key"]
    if q["category"] == "asym":
        if q["kind"] == "asym_decide" and not k["truth"]:
            return "False - no witnesses exist."
        w = ", ".join(f"{n} = {v}" for n, v in k["witnesses"].items())
        return ("True; " if q["kind"] == "asym_decide" else "") + f"e.g. {w} (any valid witnesses earn full credit)"
    if q["category"] == "panalysis":
        return f"T(n) = {k['T_text']} ∈ O({k['g']})"
    if q["category"] == "design":
        out = "Any correct algorithm; time complexity " + " / ".join(f"O({P.show(_expr(c))})" for c in k["classes"])
        return out + (f"; traced output {k['trace_output']}" if k["follow"] == "trace" else "")
    kind = q["kind"]
    if kind == "seq":
        return f"d = {k['d']}; next {k['next'][0]}, {k['next'][1]}; aₙ = {tnmath.pretty(tnmath.parse(k['nth'], ('n',)).expr)}; a₂₀ = {k['a20']}"
    if kind == "series":
        return f"{tnmath.pretty(tnmath.parse(k['count'], ('n',)).expr)} terms; S = {tnmath.pretty(tnmath.parse(k['closed'], ('n',)).expr)} ∈ Θ(n²)"
    if kind == "series_num":
        return f"{k['count']} terms; sum = {k['sum']}"
    if kind == "recur_add":
        return f"{', '.join(map(str, k['terms']))}; aₙ = {tnmath.pretty(tnmath.parse(k['closed'], ('n',)).expr)}"
    return ", ".join(map(str, k["terms"]))


def grade_exam(exam, answers, runner=None):
    results, by_cat = [], {c: [0.0, 0] for c in ORDER}
    for q in exam["questions"]:
        r = grade_question(q, (answers or {}).get(q["qid"]), runner)
        results.append(r)
        by_cat[q["category"]][0] += r["earned"]
        by_cat[q["category"]][1] += r["max"]
    total = sum(r["earned"] for r in results)
    mx = sum(r["max"] for r in results)
    return {"score": round(100 * total / mx, 1) if mx else 0.0, "earned": round(total, 2), "max": mx,
            "categories": [{"category": c, "label": CATEGORIES[c], "earned": round(e, 2), "max": m,
                            "percent": round(100 * e / m, 1) if m else None} for c, (e, m) in by_cat.items() if m],
            "questions": results}
