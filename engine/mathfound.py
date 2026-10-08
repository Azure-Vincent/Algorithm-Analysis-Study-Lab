"""Discrete Math Foundations: safe grading of algebra answers (equivalence + required form).

Student text is read only by tnmath's hand-written parser in algebra mode (no eval / sympify).
Two expressions are equivalent when they agree at several sample assignments of the variables,
evaluated by walking the parsed SymPy tree with mpmath - so 4x·log(x), x·4log(x), 4*x*log(x) and
x log(x⁴) are all the same answer, as are n(n + 1)/2, (n² + n)/2 and 0.5n² + 0.5n.

A part can also demand a FORM, checked on the parse tree (what the student actually wrote):
    expanded     a sum of distinct terms, optionally over a numeric denominator: (n² + n)/2, n²/2 + n/2
    factored     a product containing a bracketed sum: n(n + 1), 3n(n + 2)
    log_simple   no log of a power / product / quotient left: 4x log(x)
    combined     like terms combined (no two terms of the same kind): 5n² + 9n
    power        a single power: x⁵, 2^(2n)

Part kinds handled here: expr, work (shown working, line by line), theta (asymptotic class),
constant (a witness C checked against the definition with the proof checker).
"""
from __future__ import annotations

import random
import re

import mpmath
import sympy as sp

from engine import tnmath
from engine.tnmath import ParseError

VARS = ("n", "x", "y", "a", "b", "k", "m")

SKILLS = {     # stored in the shared skill-mastery table, so keys carry an m_ prefix (proof skills use plain keys)
    "m_exp": "Exponent Rules", "m_log": "Logarithm Rules", "m_poly": "Polynomial Simplification",
    "m_distribution": "Distribution", "m_factoring": "Factoring", "m_fractions": "Fractions",
    "m_aseq": "Arithmetic Sequences", "m_aseries": "Arithmetic Series", "m_gseq": "Geometric Sequences",
    "m_summations": "Summations", "m_ineq": "Inequalities", "m_growth": "Growth-Rate Simplification",
    "m_mixed": "Mixed Simplification",
}
TOPIC_SKILLS = {
    "math_algebra": ["m_distribution"], "math_exp": ["m_exp"], "math_log": ["m_log"], "math_poly": ["m_poly"],
    "math_factor": ["m_factoring"], "math_frac": ["m_fractions"], "math_aseq": ["m_aseq"],
    "math_aseries": ["m_aseries", "m_summations"], "math_gseq": ["m_gseq"], "math_growth": ["m_growth"],
    "math_ineq": ["m_ineq"], "math_tn": ["m_poly", "m_summations"], "math_mixed": ["m_mixed"],
}
CATEGORIES = {
    "math_algebra": "Algebra / distribution error", "math_exp": "Exponent rule misapplied",
    "math_log": "Logarithm rule misapplied", "math_poly": "Polynomial simplification error",
    "math_factor": "Factoring error", "math_frac": "Fraction simplification error",
    "math_aseq": "Arithmetic sequence error", "math_aseries": "Arithmetic series / summation error",
    "math_gseq": "Geometric sequence error", "math_growth": "Growth-rate simplification error",
    "math_ineq": "Inequality manipulation error", "math_tn": "T(n) algebra error",
    "math_mixed": "Mixed simplification error",
}
FORM_TEXT = {"expanded": "expanded (a sum of distinct terms)", "factored": "factored (a product containing a bracket)",
             "log_simple": "with no power, product or quotient left inside a log", "combined": "with like terms combined",
             "power": "as a single power", "split_exp": "with no sum or difference left in an exponent (e.g. 2·2ⁿ)",
             "positive_exp": "with positive exponents only", "monomial": "as a single term (one coefficient, each variable once)",
             "single_fraction": "as a single fraction"}


# ============================================================================ parsing / evaluation
def parse(text, growth=True):
    """(sympy expr, syntax tree) of an expression, or raise ParseError."""
    s = str(text or "").strip()
    s = re.sub(r"^\s*[A-Za-z]\s*\(\s*[a-z]\s*\)\s*=", "", s)          # 'T(n) =', 'f(x) ='
    s = s.lstrip("=→").strip()
    s = re.sub(r"([⁰¹²³⁴⁵⁶⁷⁸⁹)a-z0-9])ⁿ", r"\1^n", s).replace("ⁿ", "^n")   # 2ⁿ → 2^n
    s = re.sub(r"\blog_?2\s*\(", "log(", s)                                  # log_2(n) / log2(n) = log(n)
    if not s:
        raise ParseError("Enter an expression.")
    p = tnmath.parse(s[:200], VARS, algebra=True)
    return p.expr, p.tree


def _ev(e, env):
    if e.is_Integer:
        return mpmath.mpf(int(e))
    if e.is_Rational:
        return mpmath.mpf(int(e.p)) / int(e.q)
    if e.is_Float:
        return mpmath.mpf(str(e))
    if e.is_Symbol:
        return env[str(e)]
    if isinstance(e, sp.Add):
        return mpmath.fsum(_ev(a, env) for a in e.args)
    if isinstance(e, sp.Mul):
        out = mpmath.mpf(1)
        for a in e.args:
            out *= _ev(a, env)
        return out
    if isinstance(e, sp.Pow):
        return mpmath.power(_ev(e.base, env), _ev(e.exp, env))
    if isinstance(e, sp.log):
        v = _ev(e.args[0], env)
        if v <= 0:
            raise ValueError("log of a non-positive number")
        return mpmath.log(v)
    if isinstance(e, sp.factorial):
        return mpmath.factorial(_ev(e.args[0], env))
    raise ValueError(f"unsupported {type(e).__name__}")


def _points(seed=7, count=6):
    rng = random.Random(seed)
    pts = []
    for _ in range(count):
        vals = rng.sample(range(2, 14), len(VARS))
        env = {v: mpmath.mpf(val) for v, val in zip(VARS, vals)}
        env["n"] = mpmath.mpf(rng.choice([11, 17, 23, 31, 40]))
        pts.append(env)
    return pts


POINTS = _points()


def equivalent(a, b):
    """True if a and b agree at every sample point where both are defined (needs ≥ 3 such points)."""
    good = 0
    with mpmath.workdps(40):
        for env in POINTS:
            try:
                va, vb = _ev(a, env), _ev(b, env)
            except (ValueError, ZeroDivisionError, TypeError):
                continue
            if abs(va - vb) > mpmath.mpf("1e-18") * (1 + abs(vb)):
                return False
            good += 1
    return good >= 3


# ============================================================================ forms (checked on what was written)
def _strip_num_div(node):
    while node.op == "div" and tnmath._number(node.kids[1]) is not None:
        node = node.kids[0]
    return node


def _terms(node):
    if node.op == "add":
        return _terms(node.kids[0]) + _terms(node.kids[1])
    if node.op == "neg" and node.kids[0].op != "add":
        return _terms(node.kids[0])
    return [node]


def _has(node, ops):
    return node.op in ops or any(_has(k, ops) for k in node.kids)


def _like_key(term):
    """Monomial signature of a term (ignores numeric coefficients)."""
    e = sp.expand(tnmath._to_sympy(term, True, True))
    c, rest = e.as_coeff_Mul()
    return sp.srepr(rest)


def form_ok(form, tree, expr):
    if not form:
        return True
    if form in ("expanded", "combined"):
        body = _strip_num_div(tree)
        terms = []
        for t in _terms(body):
            t = _strip_num_div(t)
            if t.op != "neg" and _has(t, ("add",)):
                return False
            terms.append(t)
        keys = [_like_key(t) for t in terms]
        return len(keys) == len(set(keys))
    if form == "factored":
        body = _strip_num_div(tree)
        return body.op == "mul" and _has(body, ("add",))
    if form == "log_simple":
        def bad(node):
            if node.op in ("log", "ln", "log10"):
                arg = node.kids[0]
                if arg.op in ("pow", "mul", "div"):
                    return True
            return any(bad(k) for k in node.kids)
        return not bad(tree)
    if form == "power":
        return tree.op in ("pow", "var") and not (tree.kids and _has(tree.kids[0], ("mul", "pow", "div")))
    if form == "split_exp":
        def sum_exp(node):
            if node.op == "pow" and _has(node.kids[1], ("add", "neg")):
                return True
            return any(sum_exp(k) for k in node.kids)
        return not sum_exp(tree)
    if form == "positive_exp":
        def neg_exp(node):
            if node.op == "pow" and _has(node.kids[1], ("neg",)):
                return True
            return any(neg_exp(k) for k in node.kids)
        return not neg_exp(tree)
    if form == "monomial":
        seen, nums = set(), 0
        def factors(node):
            return factors(node.kids[0]) + factors(node.kids[1]) if node.op == "mul" else [node]
        for f in factors(tree):
            if tnmath._number(f) is not None:
                nums += 1
                continue
            base = f.kids[0] if f.op == "pow" and tnmath._number(f.kids[1]) is not None else f
            if base.op != "var" or base.value in seen:
                return False
            seen.add(base.value)
        return nums <= 1
    if form == "single_fraction":
        body = tree.kids[0] if tree.op == "neg" else tree
        return body.op == "div"
    raise ValueError(form)


# ============================================================================ part grading
def _show(text):
    return str(text)


def grade_expr_part(p, value):
    given = str(value or "").strip()
    res = {"id": p["id"], "label": p["label"], "kind": p["kind"], "given": given or "(no answer)", "expected": _show(p["answer"])}
    if not given:
        res.update(correct=False, why="No answer given.")
        return res
    try:
        expr, tree = parse(given)
    except ParseError as e:
        res.update(correct=False, why=f"Couldn't read that: {e}")
        return res
    target, _ = parse(p["answer"])
    if not equivalent(expr, target):
        why = None
        for trap, msg in p.get("traps", []):
            try:
                if equivalent(expr, parse(trap)[0]):
                    why = msg
                    break
            except ParseError:
                continue
        res.update(correct=False, why=why or "That isn't equal to the correct expression.")
        return res
    if not form_ok(p.get("form"), tree, expr):
        res.update(correct=False, why=f"Equal in value, but not written {FORM_TEXT[p['form']]} - which is what this step asks for.")
        return res
    res.update(correct=True)
    return res


def grade_work_part(p, value):
    """Shown working: every non-empty line must equal the starting expression; at least min_lines lines."""
    text = str(value or "")[:3000]
    lines = [ln.strip().lstrip("=→⇒").strip() for ln in text.splitlines() if ln.strip()]
    res = {"id": p["id"], "label": p["label"], "kind": "work", "given": text.strip() or "(no work shown)",
           "expected": " → ".join(p.get("model", [])) or "intermediate steps"}
    need = p.get("min_lines", 2)
    if len(lines) < need:
        res.update(correct=False, why=f"Show at least {need} intermediate step{'s' if need > 1 else ''}, one per line.")
        return res
    start, _ = parse(p["start"])
    for i, ln in enumerate(lines, start=1):
        try:
            e, _ = parse(ln)
        except ParseError as err:
            res.update(correct=False, why=f"Line {i} couldn't be read ({err}).")
            return res
        if not equivalent(e, start):
            res.update(correct=False, why=f"Line {i} ('{ln}') is not equal to the previous steps - a rule was misapplied there.")
            return res
    res.update(correct=True, why="Every step is a valid transformation.")
    return res


def grade_theta_part(p, value):
    from engine import mockexam
    given = str(value or "").strip()
    res = {"id": p["id"], "label": p["label"], "kind": "theta", "given": given or "(no answer)", "expected": f"Θ({p['answer']})"}
    rel, inner = mockexam.extract_bound(given)
    try:
        e = tnmath.parse(re.sub(r"\bx\b", "n", inner)[:200], ("n",), growth=True).expr if inner.strip() else None
        g = tnmath.parse(re.sub(r"\bx\b", "n", p["answer"]), ("n",), growth=True).expr
    except ParseError as err:
        res.update(correct=False, why=f"Couldn't read that: {err}")
        return res
    ok = mockexam.same_class(e, g)
    if ok and rel in ("O", "omega"):
        res.update(correct=False, why="Right growth class, but the question asks for Θ (a tight bound), not O or Ω.")
    else:
        res.update(correct=ok, why=None if ok else f"Keep only the dominant term and drop its constant: Θ({p['answer']}).")
    return res


def grade_constant_part(p, value):
    from engine import proofs
    res = {"id": p["id"], "label": p["label"], "kind": "constant", "given": str(value or "").strip() or "(no answer)",
           "expected": f"any valid C, e.g. {p['answer']}"}
    try:
        c = proofs.parse_number(str(value or ""), "C")
    except ParseError as e:
        res.update(correct=False, why=str(e))
        return res
    f, g = proofs.parse_fn(p["f"]), proofs.parse_fn(p["g"])
    r = proofs.check_bound(f, g, c, p["n0"], p.get("side", "upper"))
    if r["ok"]:
        res.update(correct=True, why=f"C = {value} works for every n ≥ {p['n0']}.")
    elif not r["eventually"]:
        res.update(correct=False, why=f"With C = {value} the inequality fails for large n (first at n = {r['first_fail']}).")
    else:
        res.update(correct=False, why=f"With C = {value} the inequality fails at n = {r['first_fail']} ≥ {p['n0']}. Choose a larger C.")
    return res


GRADERS = {"expr": grade_expr_part, "work": grade_work_part, "theta": grade_theta_part, "constant": grade_constant_part}


def grade_part(p, value):
    return GRADERS[p["kind"]](p, value)


# ============================================================================ skills / mistakes
def skills_for(ex, result):
    by_id = {r["id"]: r["correct"] for r in result.get("parts", [])}
    out = {s: result["correct"] for s in ex.get("skills") or TOPIC_SKILLS.get(ex["topic"], [])}
    for p in ex.get("parts", []):
        if p.get("skill"):
            out[p["skill"]] = out.get(p["skill"], True) and by_id.get(p["id"], False)
    return out


def category_label(cat):
    return CATEGORIES.get(cat) if cat else None
