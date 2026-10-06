"""Time Complexity Proofs: checking c / n₀ choices against the formal definitions of O, Ω and Θ.

    f(n) ∈ O(g(n))  ⇔  ∃ c > 0, n₀ > 0 :  0 ≤ f(n) ≤ c·g(n)          for every n ≥ n₀
    f(n) ∈ Ω(g(n))  ⇔  ∃ c > 0, n₀ > 0 :  0 ≤ c·g(n) ≤ f(n)          for every n ≥ n₀
    f(n) ∈ Θ(g(n))  ⇔  ∃ c₁, c₂ > 0, n₀ > 0 :  0 ≤ c₁·g(n) ≤ f(n) ≤ c₂·g(n)   for every n ≥ n₀

Student text only ever goes through tnmath's hand-written parser (growth mode adds 2^n, n!, √n);
nothing is passed to eval(), exec() or sympify(). Numbers are computed by walking the parsed SymPy
tree with mpmath, so 2^n and n! can be compared at very large n without overflow.

How a proposed (c, n₀) is checked: every integer n from n₀ up to n₀ + 400 is tested, then points
spaced 10 % apart up to 10⁶, then powers of ten up to 10¹⁰⁰. Whether the inequality holds for ALL
large n is decided from lim f(n)/g(n) (SymPy's limit). Finite testing is reported as evidence only;
the worked proofs give the actual argument.
"""
from __future__ import annotations

import math
import re
import mpmath
import sympy as sp

from engine import tnmath
from engine.tnmath import ParseError

N = tnmath.SYM["n"]
CSYMS = {name: tnmath.SYM[name] for name in ("c", "c1", "c2")}
EXPR_VARS = ("n",)
INEQ_VARS = ("n", "c", "c1", "c2")
REL_SYMBOL = {"O": "O", "omega": "Ω", "theta": "Θ"}
REL_NAME = {"O": "Big O", "omega": "Big Ω", "theta": "Big Θ"}
MAX_CONST = 10 ** 9
DENSE = 400

SKILLS = {
    "big_o": "Big O proofs", "big_omega": "Big Ω proofs", "big_theta": "Big Θ proofs",
    "choose_c": "Selecting c", "choose_n0": "Selecting n₀",
    "poly": "Polynomial bounds", "growth": "Growth comparisons", "disprove": "Disproving bounds",
}
REL_SKILL = {"O": "big_o", "omega": "big_omega", "theta": "big_theta"}
TOPIC_SKILL = {"pf_poly": "poly", "pf_growth": "growth", "pf_false": "disprove", "pf_tn": "poly"}

CATEGORIES = {
    "wrong_verdict": "Decided true/false incorrectly",
    "reversed": "Reversed the inequality",
    "missing_c": "Inequality without the constant c",
    "bad_inequality": "Required inequality written incorrectly",
    "finite_range": "Constant only works on a finite range of n",
    "n0_too_small": "n₀ too small for the chosen c",
    "negative": "f(n) negative for some n ≥ n₀",
    "bad_constant": "Constant not positive / not a number",
    "one_sided": "Θ needs both an upper and a lower bound",
    "intuition_only": "Intuition given instead of a proof",
    "disproof_reason": "Disproof doesn't explain why no c works",
    "proof_blank": "Proof step filled in incorrectly",
    "proof_debug": "Didn't spot the flaw in the proof",
    "limits": "Ratio / limit reasoning",
}


# ============================================================================ parsing
def _clean(text):
    s = str(text or "")
    for a, b in (("c₁", "c1"), ("c₂", "c2"), ("C₁", "c1"), ("C₂", "c2"), ("≤", "<="), ("≥", ">="),
                 ("=<", "<="), ("=>", ">="), ("⩽", "<="), ("⩾", ">=")):
        s = s.replace(a, b)
    return s


def parse_fn(text, what="f(n)"):
    """A function of n for a proof (polynomials, logs, √n, 2^n, n!)."""
    try:
        expr = tnmath.parse(_clean(text), EXPR_VARS, growth=True).expr
    except ParseError as e:
        raise ParseError(f"{what}: {e}") from None
    return expr


def parse_number(text, name):
    """A positive constant such as 5, 1/2 or 0.25."""
    s = _clean(text).strip()
    if not s:
        raise ParseError(f"Enter a value for {name}.")
    try:
        expr = tnmath.parse(s, (), growth=False).expr
    except ParseError as e:
        raise ParseError(f"{name}: {e}") from None
    if not expr.is_number:
        raise ParseError(f"{name} must be a number.")
    if expr <= 0:
        raise ParseError(f"{name} must be positive ({name} > 0).")
    if expr > MAX_CONST:
        raise ParseError(f"{name} is larger than this checker accepts (at most {MAX_CONST:,}).")
    return sp.nsimplify(expr)


# ============================================================================ numbers (no eval)
def _ev(e, n):
    if e.is_Integer:
        return mpmath.mpf(int(e))
    if e.is_Rational:
        return mpmath.mpf(int(e.p)) / int(e.q)
    if e.is_Float:
        return mpmath.mpf(str(e))
    if e.is_Symbol:
        if e == N:
            return n
        raise ValueError(f"unexpected symbol {e}")
    if isinstance(e, sp.Add):
        return mpmath.fsum(_ev(a, n) for a in e.args)
    if isinstance(e, sp.Mul):
        out = mpmath.mpf(1)
        for a in e.args:
            out *= _ev(a, n)
        return out
    if isinstance(e, sp.Pow):
        return mpmath.power(_ev(e.base, n), _ev(e.exp, n))
    if isinstance(e, sp.log):
        a = _ev(e.args[0], n)
        if a <= 0:
            raise ValueError("log of a non-positive number")
        return mpmath.log(a)
    if isinstance(e, sp.factorial):
        return mpmath.factorial(_ev(e.args[0], n))
    raise ValueError(f"unsupported expression {type(e).__name__}")


def value(expr, n):
    """expr evaluated at n (an int or mpf), as an mpf. Raises ValueError where undefined."""
    with mpmath.workdps(40):
        return _ev(expr, mpmath.mpf(n))


def fmt_num(v):
    """Readable number: exact for moderate values, scientific beyond."""
    if v is None:
        return "undefined"
    v = mpmath.mpf(v)
    if v == 0:
        return "0"
    if abs(v) < 1e15 and abs(v) >= 1e-4:
        if abs(v - mpmath.nint(v)) < 1e-9 * max(1, abs(v)):
            return f"{int(mpmath.nint(v)):,}"
        return mpmath.nstr(v, 6)
    exp = int(mpmath.floor(mpmath.log10(abs(v))))
    mant = v / mpmath.power(10, exp)
    return f"{'-' if v < 0 else ''}{mpmath.nstr(abs(mant), 4)}×10^{exp}"


def log10_or_none(v):
    try:
        return float(mpmath.log10(v)) if v > 0 else None
    except (ValueError, TypeError):
        return None


def show(expr):
    """Display text for a function: 4n² + 3n + 7, log₂ n, n log₂ n, 2ⁿ, n!."""
    try:
        if not expr.has(sp.factorial) and not any(isinstance(a, sp.Pow) and not a.exp.is_number
                                                    for a in sp.preorder_traversal(expr)) \
                and not expr.has(sp.sqrt(N)):
            return tnmath.pretty(expr)
    except Exception:  # noqa: BLE001 - fall back to the generic printer below
        pass
    s = sp.sstr(sp.expand(expr))
    s = s.replace("log(n)/log(2)", "log₂ n").replace("factorial(n)", "n!").replace("sqrt(n)", "√n")
    s = re.sub(r"(\d+)\*\*n", lambda m: m.group(1) + "ⁿ", s)
    s = re.sub(r"\*\*(\d+)", lambda m: m.group(1).translate(tnmath.SUP), s)
    return s.replace("*", "·")


# ============================================================================ asymptotics
_LIMITS = {}


def ratio_limit(f, g):
    """lim f(n)/g(n) as n → ∞: 0, a positive number, sp.oo, or None if it can't be decided.
    Cached by SymPy's printed form of the already-parsed trees (nothing is ever re-parsed from text)."""
    key = (sp.srepr(f), sp.srepr(g))
    if key not in _LIMITS:
        try:
            L = sp.limit(sp.simplify(f / g), N, sp.oo)
            if L.has(sp.AccumBounds) or L.is_extended_real is False or L.has(sp.nan, sp.zoo) or (L != sp.oo and not L.is_number):
                L = None
        except Exception:  # noqa: BLE001 - SymPy may not decide every limit
            L = None
        if len(_LIMITS) > 2000:
            _LIMITS.clear()
        _LIMITS[key] = L
    return _LIMITS[key]


def limit_text(L):
    if L is None:
        return "can't be determined automatically"
    if L == sp.oo:
        return "∞"
    return show(sp.nsimplify(L)) if L.is_Rational else fmt_num(L)


def relation_truth(f, g, rel):
    """True/False from the limit of f/g (None if the limit can't be decided)."""
    L = ratio_limit(f, g)
    if L is None:
        return None
    if rel == "O":
        return bool(L != sp.oo)
    if rel == "omega":
        return bool(L == sp.oo or L > 0)
    return bool(L != sp.oo and L > 0)


def limit_conclusion(L, f_txt, g_txt):
    if L is None:
        return "The limit of the ratio can't be decided here - use the definition directly."
    if L == 0:
        return f"lim {f_txt}/{g_txt} = 0, so {f_txt} grows strictly slower: {f_txt} ∈ O({g_txt}), but not Ω({g_txt}) or Θ({g_txt})."
    if L == sp.oo:
        return f"lim {f_txt}/{g_txt} = ∞, so {f_txt} grows strictly faster: {f_txt} ∈ Ω({g_txt}), but not O({g_txt}) or Θ({g_txt})."
    return (f"lim {f_txt}/{g_txt} = {limit_text(L)}, a positive constant, so {f_txt} ∈ Θ({g_txt}) "
            f"(and therefore both O({g_txt}) and Ω({g_txt})).")


# ============================================================================ checking c and n₀
def sample_points(n0):
    start = max(1, math.ceil(float(n0)))
    pts = list(range(start, start + DENSE + 1))
    x = float(pts[-1])
    while x < 1e6:
        x *= 1.1
        pts.append(int(x))
    x = 10 ** math.ceil(math.log10(max(x, 10)))
    while x <= 1e30:
        pts.append(int(x))
        x *= 10
    pts += [10 ** 40, 10 ** 60, 10 ** 100]
    return sorted(set(pts))


def _sides(side, fv, cgv):
    """(lhs, rhs) of the inequality being tested: upper f ≤ c·g, lower c·g ≤ f."""
    return (fv, cgv) if side == "upper" else (cgv, fv)


def check_bound(f, g, c, n0, side):
    """Test 0 ≤ f ≤ c·g (side='upper') or 0 ≤ c·g ≤ f (side='lower') for n ≥ n₀.

    Returns ok, eventually (holds for all large n, from the limit), the first failing n with its values,
    an example n where it holds, and whether a failure is caused by f(n) < 0."""
    first_fail = holds_at = None
    neg = False
    fail_vals = None
    last_dense_fail = None
    with mpmath.workdps(40):
        c_m = mpmath.mpf(str(sp.N(c, 40)))
        tol = mpmath.mpf("1e-25")
        for n in sample_points(n0):
            nm = mpmath.mpf(n)
            try:
                fv, gv = _ev(f, nm), _ev(g, nm)
            except ValueError:
                fv = gv = None
            if fv is None:
                bad, is_neg = True, False
            else:
                cgv = c_m * gv
                lhs, rhs = _sides(side, fv, cgv)
                is_neg = fv < -tol or cgv < -tol
                bad = is_neg or lhs > rhs + tol * (1 + abs(rhs))
            if bad:
                if first_fail is None:
                    first_fail = n
                    neg = is_neg
                    fail_vals = (fv, None if fv is None else c_m * gv)
                if n <= math.ceil(float(n0)) + DENSE:
                    last_dense_fail = n
            elif first_fail is None:
                holds_at = n                    # the last tested n where it still held, before any failure
    eventually = bool(_eventually(f, g, c, side, first_fail, last_dense_fail, n0))
    ok = bool(first_fail is None and eventually)
    return {"ok": ok, "eventually": eventually, "first_fail": first_fail, "negative": bool(neg),
            "fail_f": fmt_num(fail_vals[0]) if fail_vals and fail_vals[0] is not None else None,
            "fail_cg": fmt_num(fail_vals[1]) if fail_vals and fail_vals[1] is not None else None,
            "holds_at": holds_at, "last_dense_fail": last_dense_fail}


def _eventually(f, g, c, side, first_fail, last_dense_fail, n0):
    L = ratio_limit(f, g)
    if L is not None:
        if side == "upper":
            if L == sp.oo:
                return False
            if L != c:
                return bool(L < c)
        else:
            if L == sp.oo:
                return True
            if L != c:
                return bool(c < L)
    # equal to the limit (or undecidable): trust the largest tested points
    with mpmath.workdps(40):
        c_m = mpmath.mpf(str(sp.N(c, 40)))
        for n in (10 ** 30, 10 ** 60, 10 ** 100):
            try:
                fv, gv = _ev(f, mpmath.mpf(n)), _ev(g, mpmath.mpf(n))
            except ValueError:
                return False
            lhs, rhs = _sides(side, fv, c_m * gv)
            if lhs > rhs + mpmath.mpf("1e-25") * (1 + abs(rhs)):
                return False
    return True


def smallest_n0(f, g, c, side, limit=5000):
    """Smallest integer n₀ ≤ limit from which the bound holds at every tested point (or None)."""
    res = check_bound(f, g, c, 1, side)
    if res["ok"]:
        return 1
    if not res["eventually"]:
        return None
    last = 0
    with mpmath.workdps(40):
        c_m = mpmath.mpf(str(sp.N(c, 40)))
        for n in range(1, limit + 1):
            try:
                fv, gv = _ev(f, mpmath.mpf(n)), _ev(g, mpmath.mpf(n))
                lhs, rhs = _sides(side, fv, c_m * gv)
                bad = fv < 0 or lhs > rhs + mpmath.mpf("1e-25") * (1 + abs(rhs))
            except ValueError:
                bad = True
            if bad:
                last = n
    cand = last + 1
    return cand if check_bound(f, g, c, cand, side)["ok"] else None


def suggest_constants(f, g, rel):
    """One valid (simple) choice of constants for a true claim, found by search."""
    L = ratio_limit(f, g)
    out = {}
    sides = {"O": ["upper"], "omega": ["lower"], "theta": ["lower", "upper"]}[rel]
    n0s = []
    for side in sides:
        if side == "upper":
            if L is None or L == sp.oo:
                return None
            c = sp.Integer(max(1, math.floor(float(L)) + 1)) if L != 0 else sp.Integer(1)
        else:
            if L is None or L == 0:
                return None
            if L == sp.oo:
                c = sp.Integer(1)
            else:
                c = sp.Integer(math.floor(float(L))) if float(L) >= 2 else sp.Rational(1, 2) * sp.nsimplify(L)
                c = sp.nsimplify(c)
                if c <= 0:
                    c = sp.Rational(1, 2)
        n0 = None
        for _ in range(8):
            n0 = smallest_n0(f, g, c, side)
            if n0 is not None:
                break
            c = c * 2 if side == "upper" else c / 2
        if n0 is None:
            return None
        key = "c" if rel != "theta" else ("c2" if side == "upper" else "c1")
        out[key] = c
        n0s.append(n0)
    out["n0"] = sp.Integer(max(n0s))
    return out


# ============================================================================ the required inequality (step 1)
REL_SPLIT = re.compile(r"(<=|>=|<|>)")


def _equiv(a, b):
    """a ≡ b as functions of n (and of the constant symbols) - checked at sample values, never eval'd."""
    syms = sorted((a.free_symbols | b.free_symbols) - {N}, key=str)
    for nv in (3, 7, 19, 50):
        for cv in (2, 5):
            sub = {s: sp.Integer(cv + i) for i, s in enumerate(syms)}
            try:
                va, vb = value(a.subs(sub), nv), value(b.subs(sub), nv)
            except ValueError:
                return False
            if abs(va - vb) > mpmath.mpf("1e-20") * (1 + abs(vb)):
                return False
    return True


def _scaled(big, g):
    """If big = k·g with k a constant symbol (c, c1, c2) or a positive number, return k; else None."""
    syms = big.free_symbols - {N}
    if len(syms) == 1:
        k = next(iter(syms))
        return k if _equiv(big, k * g) else None
    if not syms:
        try:
            ratio = value(big, 11) / value(g, 11)
        except (ValueError, ZeroDivisionError):
            return None
        k = sp.nsimplify(float(ratio), rational=True)
        return k if k > 0 and _equiv(big, k * g) else None
    return None


def parse_inequality(text, f, g, f_src, g_src):
    """Split '0 ≤ f(n) ≤ c·g(n)' (or 'A and B') into relations (small, big) between parsed expressions."""
    s = _clean(text)
    s = re.sub(r"\bf\s*\(\s*n\s*\)", "(" + f_src + ")", s)
    s = re.sub(r"\bg\s*\(\s*n\s*\)", "(" + g_src + ")", s)
    pieces = [p for p in re.split(r"\band\b|;|,(?![^()]*\))", s) if p.strip()]
    if not pieces:
        raise ParseError("Write the inequality, e.g. f(n) ≤ c·g(n).")
    rels = []
    for piece in pieces:
        parts = REL_SPLIT.split(piece)
        if len(parts) < 3:
            raise ParseError("Use ≤ (or <=) to write the inequality, e.g. log₂ n ≤ c·n².")
        exprs = []
        for i in range(0, len(parts), 2):
            try:
                exprs.append(tnmath.parse(parts[i], INEQ_VARS, growth=True).expr)
            except ParseError as e:
                raise ParseError(f"In '{parts[i].strip()}': {e}") from None
        for i in range(1, len(parts), 2):
            a, b = exprs[i // 2], exprs[i // 2 + 1]
            small, big = (a, b) if parts[i] in ("<=", "<") else (b, a)
            if small == 0 or big == 0:
                continue                                    # the 0 ≤ … part of the definition
            rels.append((small, big, parts[i] in ("<", ">")))
    return rels


def classify_inequality(text, ex_f, ex_g, rel, f_src, g_src):
    """Return (status, info). status: ok | reversed | missing_c | one_sided | bad_inequality."""
    rels = parse_inequality(text, ex_f, ex_g, f_src, g_src)
    upper = lower = None
    reversed_ = False
    for small, big, strict in rels:
        if _equiv(small, ex_f):
            k = _scaled(big, ex_g)
            if k is not None:
                upper = k
                continue
        if _equiv(big, ex_f):
            k = _scaled(small, ex_g)
            if k is not None:
                lower = k
                continue
        # the wrong way round for what is being proved?
        if rel in ("O", "omega"):
            if _equiv(big, ex_f) or _equiv(small, ex_f):
                reversed_ = True
    need = {"O": ("upper",), "omega": ("lower",), "theta": ("lower", "upper")}[rel]
    have = {"upper": upper, "lower": lower}
    if all(have[s] is not None for s in need):
        bad = [s for s in need if not isinstance(have[s], sp.Symbol)]
        return "ok", {"numeric": bad, "upper": have["upper"], "lower": have["lower"]}
    if rel == "O" and lower is not None:
        return "reversed", {}
    if rel == "omega" and upper is not None:
        return "reversed", {}
    if rel == "theta" and (upper is not None or lower is not None):
        return "one_sided", {"has": "upper" if upper is not None else "lower"}
    if reversed_:
        return "missing_c", {}
    return "bad_inequality", {}


def required_inequality(rel, f_txt, g_txt):
    if rel == "O":
        return f"0 ≤ {f_txt} ≤ c·{g_txt}"
    if rel == "omega":
        return f"0 ≤ c·{g_txt} ≤ {f_txt}"
    return f"0 ≤ c₁·{g_txt} ≤ {f_txt} ≤ c₂·{g_txt}"


def definition(rel):
    return {
        "O": "f(n) ∈ O(g(n)) if there exist constants c > 0 and n₀ > 0 such that 0 ≤ f(n) ≤ c·g(n) for every n ≥ n₀.",
        "omega": "f(n) ∈ Ω(g(n)) if there exist constants c > 0 and n₀ > 0 such that 0 ≤ c·g(n) ≤ f(n) for every n ≥ n₀.",
        "theta": "f(n) ∈ Θ(g(n)) if there exist constants c₁ > 0, c₂ > 0 and n₀ > 0 such that 0 ≤ c₁·g(n) ≤ f(n) ≤ c₂·g(n) for every n ≥ n₀.",
    }[rel]


# ============================================================================ exercises
def exercise_fns(ex):
    return parse_fn(ex["f"]), parse_fn(ex["g"], "g(n)")


def ratio_text(f_t, g_t):
    wrap = lambda t: f"({t})" if (" + " in t or " - " in t) else t
    return f"{wrap(f_t)} / {wrap(g_t)}"


def claim_text(ex):
    return f"{ex['f_text']} ∈ {REL_SYMBOL[ex['rel']]}({ex['g_text']})"


def intuition_table(f, g, ns=(1, 2, 4, 8, 16, 32, 64, 128)):
    rows = []
    for n in ns:
        try:
            fv, gv = value(f, n), value(g, n)
            ratio = fmt_num(fv / gv) if gv != 0 else "–"
        except ValueError:
            fv = gv = None
            ratio = "–"
        rows.append({"n": n, "f": fmt_num(fv), "g": fmt_num(gv), "ratio": ratio})
    return rows


def public_view(ex):
    base = {k: ex.get(k) for k in ("id", "track", "type", "topic", "level", "difficulty", "title", "prompt")}
    base["hint_count"] = len(ex.get("hints", []))
    base["rel"] = ex.get("rel")
    base["rel_symbol"] = REL_SYMBOL.get(ex.get("rel"), "")
    base["claim"] = claim_text(ex) if ex.get("f") else ex.get("claim", "")
    base["definition"] = definition(ex["rel"]) if ex.get("rel") else ""
    if ex["type"] == "proof":
        f, g = exercise_fns(ex)
        base.update(f_text=ex["f_text"], g_text=ex["g_text"], f_src=ex["f"], g_src=ex["g"],
                    constants=["c1", "c2", "n0"] if ex["rel"] == "theta" else ["c", "n0"],
                    required=required_inequality(ex["rel"], "f(n)", "g(n)"),
                    table=intuition_table(f, g), tn_source=ex.get("tn_source"))
    elif ex["type"] == "proof_fill":
        base.update(template=ex["template"], blank_count=len(ex["blanks"]))
    return base


def _const(v):
    """A stored constant ("5", "1/2", 3) as an exact SymPy number - through the safe parser, never sympify."""
    return parse_number(str(v), "constant")


def _const_text(v):
    return show(_const(v)) if v is not None else "?"


def worked_steps(ex):
    """The worked proof, one reasoning step per line."""
    f_t, g_t, rel = ex["f_text"], ex["g_text"], ex["rel"]
    sol = ex.get("solution") or {}
    why = list(ex.get("why", []))
    if not ex["truth"]:
        return why + [f"So the claim {claim_text(ex)} is false: no constants satisfy the definition. ∎"]
    if rel == "O":
        c, n0 = _const_text(sol["c"]), _const_text(sol["n0"])
        return ([f"We need constants c > 0 and n₀ > 0 such that 0 ≤ {f_t} ≤ c·{g_t} for every n ≥ n₀.",
                 f"Choose c = {c} and n₀ = {n0}."] + why +
                [f"Therefore {f_t} ≤ {c}·{g_t} for every n ≥ {n0} (and {f_t} ≥ 0 there).",
                 f"So {f_t} ∈ O({g_t}). ∎"])
    if rel == "omega":
        c, n0 = _const_text(sol["c"]), _const_text(sol["n0"])
        return ([f"We need constants c > 0 and n₀ > 0 such that 0 ≤ c·{g_t} ≤ {f_t} for every n ≥ n₀.",
                 f"Choose c = {c} and n₀ = {n0}."] + why +
                [f"Therefore {c}·{g_t} ≤ {f_t} for every n ≥ {n0}.",
                 f"So {f_t} ∈ Ω({g_t}). ∎"])
    c1, c2, n0 = _const_text(sol["c1"]), _const_text(sol["c2"]), _const_text(sol["n0"])
    return ([f"We need c₁ > 0, c₂ > 0 and n₀ > 0 with 0 ≤ c₁·{g_t} ≤ {f_t} ≤ c₂·{g_t} for every n ≥ n₀ - "
             "an upper bound (O) AND a lower bound (Ω).",
             f"Choose c₁ = {c1}, c₂ = {c2} and n₀ = {n0}."] + why +
            [f"Lower bound: {c1}·{g_t} ≤ {f_t} for every n ≥ {n0}, so {f_t} ∈ Ω({g_t}).",
             f"Upper bound: {f_t} ≤ {c2}·{g_t} for every n ≥ {n0}, so {f_t} ∈ O({g_t}).",
             f"Both bounds hold, so {f_t} ∈ Θ({g_t}). ∎"])


def solution_payload(ex):
    t = ex["type"]
    out = {"steps": ex.get("steps", []), "note": ex.get("note")}
    if t == "proof":
        f, g = exercise_fns(ex)
        L = ratio_limit(f, g)
        out.update(steps=worked_steps(ex), truth=ex["truth"], claim=claim_text(ex),
                   constants={k: _const_text(v) for k, v in (ex.get("solution") or {}).items()},
                   intuition=ex.get("intuition", ""), limit=limit_conclusion(L, ex["f_text"], ex["g_text"]),
                   required=required_inequality(ex["rel"], ex["f_text"], ex["g_text"]))
    elif t == "proof_fill":
        filled = ex["template"]
        for i, b in enumerate(ex["blanks"]):
            filled = filled.replace(f"[[{i}]]", b.get("show") or b["accept"][0])
        out.update(filled=filled, blanks=[b.get("show") or b["accept"][0] for b in ex["blanks"]])
    return out


def correct_text(ex):
    t = ex["type"]
    if t == "proof":
        if not ex["truth"]:
            return f"{claim_text(ex)} is FALSE"
        return f"{claim_text(ex)} is TRUE; e.g. " + ", ".join(f"{k} = {_const_text(v)}" for k, v in ex["solution"].items())
    if t == "proof_fill":
        return "; ".join(f"blank {i + 1}: {b.get('show') or b['accept'][0]}" for i, b in enumerate(ex["blanks"]))
    return ""


def explanation_text(ex):
    if ex["type"] == "proof":
        return "\n".join(worked_steps(ex))
    return "\n".join(ex.get("steps", []))


def category_label(cat):
    return CATEGORIES.get(cat) if cat else None


# ---------------------------------------------------------------------------- grading: prove / disprove
MATH_RE = re.compile(r"(<=|>=|≤|≥|<|>|=|\d|\bfor (all|every|each)\b)", re.I)
DISPROOF_RE = re.compile(r"(\b(no|any|every|all|fixed|single|whatever)\b[^.]*\b(c|constant)s?\b|ratio|unbounded|infinit|∞|"
                         r"without (a )?bound|grows?|exceed|larger than c|bigger than c|greater than c|>\s*c\b|"
                         r"\blim|→|->|contradict)", re.I)


def _side_feedback(res, side, k_name, kv, n0v, ex):
    f_t, g_t = ex["f_text"], ex["g_text"]
    pair = (f"{f_t} = {res['fail_f']}", f"{kv}·{g_t} = {res['fail_cg']}")
    lhs, rhs = pair if side == "upper" else (pair[1], pair[0])
    if res["negative"]:
        return ("negative", f"{f_t} is negative at n = {res['first_fail']}, but the definition needs 0 ≤ {f_t} "
                            f"for every n ≥ n₀. Choose a larger n₀.")
    if not res["eventually"]:
        where = f"Your value of {k_name} works for n = {res['holds_at']}, but fails for larger values" if res["holds_at"] \
            else f"With {k_name} = {kv} the inequality fails for the tested values"
        at = f" (at n = {res['first_fail']}: {lhs} > {rhs})" if res["first_fail"] and res["fail_f"] else ""
        tip = "a larger" if side == "upper" else "a smaller"
        return ("finite_range", f"{where}{at}. Remember: the inequality must hold for EVERY n ≥ n₀. "
                                f"Try {tip} {k_name}" + (" - or ask whether the claim is true at all." if side == "upper" else "."))
    return ("n0_too_small", f"With {k_name} = {kv}, the inequality fails at n = {res['first_fail']} "
                            f"({lhs} > {rhs}), which is ≥ your n₀ = {n0v}. "
                            f"It does hold for all large n, so choose a larger n₀.")


def grade_proof(ex, answer):
    f, g = exercise_fns(ex)
    rel, truth = ex["rel"], ex["truth"]
    f_t, g_t = ex["f_text"], ex["g_text"]
    a = answer or {}
    verdict = a.get("verdict")
    if verdict not in ("true", "false"):
        skills = {REL_SKILL[rel]: False}
        return {"correct": False, "messages": ["First decide: can the claim be proven (true) or not (false)?"],
                "steps": {"verdict": {"correct": False}}, "category": "wrong_verdict", "skills": skills,
                "answer_text": "(no decision)", "correct_text": correct_text(ex)}
    said_true = verdict == "true"
    msgs, category = [], None
    steps = {}
    skills = {REL_SKILL[rel]: False}
    topic_skill = TOPIC_SKILL.get(ex["topic"])
    explanation = str(a.get("explanation") or "").strip()[:2000]

    if said_true != truth:
        L = ratio_limit(f, g)
        if truth:
            msgs.append(f"This claim is actually TRUE - suitable constants exist. Look at how {ratio_text(f_t, g_t)} behaves as n grows.")
        else:
            msgs.append(f"This claim is FALSE: {ratio_text(f_t, g_t)} {'grows without bound' if L == sp.oo else 'shrinks to 0'} as n grows, "
                        f"so no fixed constant can make the required inequality hold for every n ≥ n₀.")
        category = "wrong_verdict"
        steps["verdict"] = {"correct": False}
        correct = False
        if not truth:
            skills["disprove"] = False
    elif not truth:
        steps["verdict"] = {"correct": True}
        ok = bool(explanation) and bool(DISPROOF_RE.search(explanation))
        steps["explanation"] = {"correct": ok}
        if not ok:
            category = "disproof_reason"
            msgs.append(f"Right, it's false - but explain WHY no fixed c works. For example: the ratio {ratio_text(f_t, g_t)} grows "
                        f"without bound, so {f_t} ≤ c·{g_t} fails as soon as n is large enough, whatever c you pick.")
        correct = ok
        skills["disprove"] = ok
    else:
        steps["verdict"] = {"correct": True}
        correct = True
        # step 1 - the required inequality
        try:
            status, info = classify_inequality(str(a.get("inequality") or "")[:300], f, g, rel, ex["f"], ex["g"])
        except ParseError as e:
            status, info = "parse", {"error": str(e)}
        steps["inequality"] = {"correct": status == "ok", "status": status}
        if status != "ok":
            correct = False
            if status == "parse":
                category = "bad_inequality"
                msgs.append(f"Step 1 couldn't be read: {info['error']}")
            elif status == "reversed":
                category = "reversed"
                need = f"{f_t} ≤ c·{g_t}" if rel == "O" else f"c·{g_t} ≤ {f_t}"
                msgs.append(f"You reversed the {REL_NAME[rel]} inequality. To prove f(n) ∈ {REL_SYMBOL[rel]}(g(n)), you need: {need}.")
            elif status == "one_sided":
                category = "one_sided"
                have = "an upper bound" if info["has"] == "upper" else "a lower bound"
                msgs.append(f"Step 1 only states {have}, but Θ requires both an upper and a lower bound: "
                            f"c₁·{g_t} ≤ {f_t} ≤ c₂·{g_t}.")
            elif status == "missing_c":
                category = "missing_c"
                msgs.append(f"Write the inequality with the constant: {required_inequality(rel, f_t, g_t)}.")
            else:
                category = "bad_inequality"
                msgs.append(f"Step 1 should state the inequality the definition requires: {required_inequality(rel, f_t, g_t)}.")
        elif info.get("numeric"):
            msgs.append("Step 1 is usually written with the symbol c (the constant you are about to choose) - accepted.")
        # steps 2/3 - constants
        names = ["c1", "c2", "n0"] if rel == "theta" else ["c", "n0"]
        consts, const_err = {}, None
        for nm in names:
            try:
                consts[nm] = parse_number(a.get(nm, ""), {"c1": "c₁", "c2": "c₂", "n0": "n₀"}.get(nm, nm))
            except ParseError as e:
                const_err = str(e)
                break
        if const_err:
            correct = False
            category = category or "bad_constant"
            msgs.append(const_err)
            steps["constants"] = {"correct": False}
            skills["choose_c"] = False
        else:
            checks = {}
            sides = {"O": [("upper", "c")], "omega": [("lower", "c")], "theta": [("lower", "c1"), ("upper", "c2")]}[rel]
            c_ok_all, n0_ok_all = True, True
            for side, k in sides:
                res = check_bound(f, g, consts[k], consts["n0"], side)
                checks[side] = res
                kname = {"c": "c", "c1": "c₁", "c2": "c₂"}[k]
                if not res["ok"]:
                    cat, msg = _side_feedback(res, side, kname, _const_text(consts[k]), _const_text(consts["n0"]), ex)
                    category = category or cat
                    msgs.append(msg)
                    if cat == "finite_range":
                        c_ok_all = False
                    else:
                        n0_ok_all = False
            if rel == "theta":
                lo_ok, up_ok = checks["lower"]["ok"], checks["upper"]["ok"]
                if lo_ok != up_ok:
                    have = "an upper" if up_ok else "a lower"
                    msgs.append(f"You have proven {have} bound, but Θ requires both an upper and lower bound.")
                    category = category or "one_sided"
            steps["constants"] = {"correct": c_ok_all and n0_ok_all, "c_ok": c_ok_all, "n0_ok": n0_ok_all if c_ok_all else None,
                                  "sides": {s: {"ok": r["ok"], "first_fail": r["first_fail"]} for s, r in checks.items()}}
            skills["choose_c"] = c_ok_all
            if c_ok_all:
                skills["choose_n0"] = n0_ok_all
            correct = correct and c_ok_all and n0_ok_all
        # step 4 - the explanation
        exp_ok = bool(explanation) and bool(MATH_RE.search(explanation))
        steps["explanation"] = {"correct": exp_ok}
        if not exp_ok:
            correct = False
            category = category or "intuition_only"
            msgs.append("Step 4 needs a mathematical reason the inequality holds for every n ≥ n₀ (for example "
                        "'for n ≥ 1, log₂ n ≤ n ≤ n²'). Saying one function 'grows slower' is intuition, not a proof.")
    skills[REL_SKILL[rel]] = correct
    if topic_skill and topic_skill != "disprove":
        skills[topic_skill] = correct
    if correct:
        msgs.insert(0, "Proof accepted: your constants satisfy the definition." if truth else "Disproof accepted.")
    parts = [f"verdict: {verdict}"]
    if said_true and truth:
        parts += [f"step 1: {a.get('inequality', '')}"] + [f"{k} = {a.get(k, '')}" for k in
                                                          (["c1", "c2", "n0"] if rel == "theta" else ["c", "n0"])]
    if explanation:
        parts.append(f"reason: {explanation[:300]}")
    return {"correct": correct, "messages": msgs, "steps": steps, "category": None if correct else category,
            "skills": skills, "answer_text": "; ".join(parts), "correct_text": correct_text(ex)}


# ---------------------------------------------------------------------------- grading: construction blanks
def _blank_ok(spec, given):
    s = _clean(given).strip()
    if not s:
        return False
    try:
        val = tnmath.parse(s, ("n", "c"), growth=True).expr
    except ParseError:
        return False
    if "range" in spec:
        if not val.is_number:
            return False
        lo, hi = spec["range"]
        return bool((val > lo if spec.get("lo_open", True) else val >= lo) and val <= hi)
    for acc in spec["accept"]:
        try:
            if _equiv(val, tnmath.parse(acc, ("n", "c"), growth=True).expr):
                return True
        except ParseError:
            continue
    return False


def grade_fill(ex, answer):
    given = list((answer or {}).get("blanks", []))
    given += [""] * (len(ex["blanks"]) - len(given))
    per = []
    skills = {}
    for i, spec in enumerate(ex["blanks"]):
        ok = _blank_ok(spec, str(given[i])[:200])
        per.append({"index": i, "given": given[i], "correct": ok})
        if spec.get("skill"):
            skills[spec["skill"]] = skills.get(spec["skill"], True) and ok
    correct = all(p["correct"] for p in per)
    skills[REL_SKILL[ex["rel"]]] = correct
    if TOPIC_SKILL.get(ex["topic"]):
        skills[TOPIC_SKILL[ex["topic"]]] = correct
    if ex.get("disprove"):
        skills["disprove"] = correct
    wrong = sum(1 for p in per if not p["correct"])
    msgs = ["Every step of the proof is filled in correctly."] if correct else \
        [f"{wrong} blank{'s' if wrong > 1 else ''} {'are' if wrong > 1 else 'is'} not right yet (marked in red). "
         "Each line must follow from the one before it."]
    return {"correct": correct, "blanks": per, "messages": msgs, "skills": skills,
            "category": None if correct else "proof_blank",
            "answer_text": "; ".join(f"blank {p['index'] + 1}: {p['given'] or '(empty)'}" for p in per),
            "correct_text": correct_text(ex)}


def parts_skills(ex, result):
    """Skills for parts-based proof exercises (debugging, ratio / limit method)."""
    by_id = {p["id"]: p["correct"] for p in result["parts"]}
    skills = {}
    for p in ex["parts"]:
        if p.get("skill"):
            skills[p["skill"]] = skills.get(p["skill"], True) and by_id.get(p["id"], False)
    if ex.get("rel"):
        skills[REL_SKILL[ex["rel"]]] = result["correct"]
    if TOPIC_SKILL.get(ex["topic"]):
        skills[TOPIC_SKILL[ex["topic"]]] = result["correct"]
    return skills


# ============================================================================ sandbox / visual checker
def investigate(f_text, g_text, rel, consts=None, nmax=40):
    f = parse_fn(f_text)
    g = parse_fn(g_text, "g(n)")
    if rel not in REL_SYMBOL:
        raise ParseError("Choose O, Ω or Θ.")
    for n in (2, 3, 10, 100):
        try:
            if value(g, n) <= 0:
                raise ParseError("g(n) must be positive for large n (e.g. n², log n, 2ⁿ).")
            if value(f, 10 ** 6) < 0:
                raise ParseError("f(n) must be non-negative for large n.")
        except ValueError:
            raise ParseError("These functions aren't defined for every n ≥ 2.") from None
    f_t, g_t = show(f), show(g)
    L = ratio_limit(f, g)
    truth = relation_truth(f, g, rel)
    out = {"f_text": f_t, "g_text": g_t, "claim": f"{f_t} ∈ {REL_SYMBOL[rel]}({g_t})",
           "table": intuition_table(f, g, (1, 2, 4, 8, 16, 32, 64, 128, 256, 1024)),
           "limit": limit_text(L), "limit_conclusion": limit_conclusion(L, f_t, g_t), "truth": truth,
           "required": required_inequality(rel, f_t, g_t), "definition": definition(rel)}
    if truth:
        sug = suggest_constants(f, g, rel)
        out["suggested"] = {k: _const_text(v) for k, v in sug.items()} if sug else None
    nmax = max(5, min(int(nmax or 40), 200))
    ns = list(range(1, nmax + 1))

    def series(expr, k=sp.Integer(1)):
        vals = []
        for n in ns:
            try:
                vals.append(log10_or_none(value(expr, n) * mpmath.mpf(str(sp.N(k, 40)))))
            except ValueError:
                vals.append(None)
        return vals

    out["n"] = ns
    out["f_log10"] = series(f)
    if consts:
        names = ["c1", "c2", "n0"] if rel == "theta" else ["c", "n0"]
        cv = {nm: parse_number(consts.get(nm, ""), {"c1": "c₁", "c2": "c₂", "n0": "n₀"}.get(nm, nm)) for nm in names}
        checks = []
        for side, k in ({"O": [("upper", "c")], "omega": [("lower", "c")], "theta": [("lower", "c1"), ("upper", "c2")]}[rel]):
            res = check_bound(f, g, cv[k], cv["n0"], side)
            kname = {"c": "c", "c1": "c₁", "c2": "c₂"}[k]
            checks.append({"side": side, "k": kname, "k_value": _const_text(cv[k]), "ok": res["ok"],
                           "eventually": res["eventually"], "first_fail": res["first_fail"],
                           "fail_f": res["fail_f"], "fail_cg": res["fail_cg"], "negative": res["negative"],
                           "series": series(g, cv[k])})
        out["checks"] = checks
        out["n0"] = _const_text(cv["n0"])
    return out


# ============================================================================ proofs from T(n) exercises
def tn_provable(tn_ex):
    return tn_ex.get("cases") == ["all"] and tn_ex.get("vars") == ["n"]


def from_tn(tn_ex):
    """A Θ proof exercise for the T(n) the student derived in T(n) Analysis."""
    sol = tn_ex["solution"]["all"]
    f = parse_fn(sol["T_text"])
    g = parse_fn(sol["theta"], "g(n)")
    f_t, g_t = show(f), show(g)
    cons = suggest_constants(f, g, "theta")
    if not cons:
        raise ParseError("No simple constants found for this T(n).")
    c1, c2, n0 = (_const_text(cons[k]) for k in ("c1", "c2", "n0"))
    terms = " + ".join(show(t) for t in sp.Add.make_args(sp.expand(f)))
    return {
        "id": "pf-tn-" + tn_ex["id"], "track": "proofs", "type": "proof", "topic": "pf_tn", "level": 3,
        "title": f"Prove the complexity: {tn_ex['title']}", "rel": "theta", "truth": True,
        "f": sol["T_text"], "g": sol["theta"], "f_text": f_t, "g_text": g_t, "tn_source": tn_ex["id"],
        "prompt": (f"In T(n) Analysis you derived T(n) = {f_t} for \"{tn_ex['title']}\". Your hypothesis is "
                   f"T(n) ∈ Θ({g_t}). Prove it: show T(n) ∈ O({g_t}) (upper bound, c₂) AND T(n) ∈ Ω({g_t}) "
                   "(lower bound, c₁) for every n ≥ n₀."),
        "solution": {k: str(cons[k]) for k in ("c1", "c2", "n0")},
        "why": [f"T(n) = {terms}.",
                f"Lower bound: for n ≥ {n0} every term is non-negative, so T(n) is at least {c1}·{g_t}.",
                f"Upper bound: for n ≥ {n0} each term is at most its own coefficient times {g_t} "
                f"(lower-order terms grow no faster than {g_t}), so T(n) ≤ {c2}·{g_t}."],
        "intuition": f"The dominant term of T(n) grows like {g_t}; constants and lower-order terms don't change the class.",
        "hints": [f"Write both inequalities: c₁·{g_t} ≤ T(n) ≤ c₂·{g_t}.",
                  f"For the lower bound, drop the lower-order terms (they are ≥ 0): T(n) ≥ (leading coefficient)·{g_t}.",
                  f"For the upper bound, replace every term by (its coefficient)·{g_t} - valid once n is large enough."],
        "tags": ["proofs", "big_theta", "tn"],
    }
