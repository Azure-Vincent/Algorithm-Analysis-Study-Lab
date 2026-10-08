"""Safe parsing, comparison and asymptotic analysis of T(n) expressions.

Student input is NEVER passed to eval(), exec() or sympy.sympify() (which uses eval internally).
A small hand-written tokenizer and recursive-descent parser accepts only:

    numbers            3   2.5   1/2
    variables          n m k   (plus loop variables such as i, j when a guided step allows them)
    operators          + - * / ^ ( )   and implicit multiplication: 3n, n(n+1), 2 log n
    functions          log(x) = log2(x) = lg(x)  (base 2 throughout this section)
    unicode            n² n³  ×  ·  −  ÷   log₂

and builds SymPy objects directly from that tree, with limits on input length, token count,
nesting depth, number size and exponent size so no input can make the server do unbounded work.

growth=True (used by the Time Complexity Proofs section) additionally accepts the growth classes
beyond polynomials:  2^n (a numeric base 2..10 raised to n),  n!  and  sqrt(n) / √n.

algebra=True (Discrete Math Foundations; implies growth) also accepts symbolic exponents such as
x^(a+b), 2^(n+1), 2^(2n) and x^(-a) (exponents built from the allowed variables, at most degree 3),
and the extra logarithms ln(x) and log10(x). Plain log is still base 2.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction

import sympy as sp

MAX_LEN = 200
MAX_TOKENS = 120
MAX_DEPTH = 24
ALGEBRA_MAX_EXPONENT = 60     # algebra practice: x^15 is a legitimate (wrong) answer to grade
MAX_EXPONENT = 10
MAX_NUMBER_DIGITS = 12
MAX_DEGREE = 16          # caps the work done when expanding products like (n+1)^10 (n+1)^10 ...

BASE_VARS = ("n", "m", "k")
FUNCS = {"log2": "log", "log": "log", "lg": "log"}
GROWTH_FUNCS = {"sqrt": "sqrt"}
ALGEBRA_FUNCS = {"ln": "ln", "log10": "log10"}
LOG2 = sp.log(2)


class ParseError(ValueError):
    """Friendly, user-facing parse error."""


def symbol(name):
    return sp.Symbol(name, positive=True)


SYM = {v: symbol(v) for v in ("n", "m", "k", "i", "j", "t", "c", "c1", "c2", "x", "y", "a", "b")}


def log2(x):
    return sp.log(x) / LOG2


# ----------------------------------------------------------------------------- tokenizer
SUPERSCRIPTS = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}
REPLACE = [("×", "*"), ("·", "*"), ("∗", "*"), ("⋅", "*"), ("−", "-"), ("–", "-"), ("÷", "/"), ("⁄", "/"),
           ("log₂", "log2"), ("lg₂", "log2"), ("**", "^"), ("（", "("), ("）", ")"), ("{", "("), ("}", ")"),
           ("[", "("), ("]", ")"), ("√", "sqrt")]
_TOKEN = re.compile(r"\s*(?:(\d+(?:\.\d+)?)|([A-Za-z_][A-Za-z_0-9]*)|(\^[⁰¹²³⁴⁵⁶⁷⁸⁹]+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+)|([+\-*/^()=,!]))")


@dataclass
class Tok:
    kind: str      # num, name, op
    value: str


def _normalize(text):
    s = text.strip()
    for a, b in REPLACE:
        s = s.replace(a, b)
    return s


def tokenize(text, allowed_vars, growth=False, algebra=False):
    s = _normalize(text)
    if not s:
        raise ParseError("Enter an expression.")
    if len(s) > MAX_LEN:
        raise ParseError(f"That expression is too long (maximum {MAX_LEN} characters).")
    funcs = set(FUNCS) | (set(GROWTH_FUNCS) if growth else set()) | (set(ALGEBRA_FUNCS) if algebra else set())
    names = sorted(set(allowed_vars) | funcs, key=len, reverse=True)
    out, pos = [], 0
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m or m.end() == pos:
            ch = s[pos:].strip()[:1]
            raise ParseError(f"Unexpected character '{ch}'. Use numbers, {', '.join(allowed_vars)}, + - * / ^ ( ) and log().")
        pos = m.end()
        num, word, sup, op = m.groups()
        if num is not None:
            if len(num.replace(".", "")) > MAX_NUMBER_DIGITS:
                raise ParseError("That number is too large.")
            out.append(Tok("num", num))
        elif sup is not None:
            out.append(Tok("op", "^"))
            out.append(Tok("num", "".join(SUPERSCRIPTS[c] for c in sup.lstrip("^"))))
        elif word is not None:
            out.extend(_split_word(word, names, allowed_vars, funcs))
        else:
            out.append(Tok("op", op))
        if len(out) > MAX_TOKENS:
            raise ParseError("That expression is too long.")
    return out


def _split_word(word, names, allowed_vars, funcs=FUNCS):
    """Split run-together names like 'nlogn' or 'nm' into known names."""
    toks, w = [], word
    while w:
        for name in names:
            if w.lower().startswith(name):
                kind = "func" if name in funcs else "name"
                toks.append(Tok(kind, name))
                w = w[len(name):]
                break
        else:
            if w[0].isdigit():
                raise ParseError(f"Write numbers before variables (2n, n^2), not '{word}'.")
            bad = re.match(r"[A-Za-z_]+", w).group(0)
            raise ParseError(f"Unknown name '{bad}'. Use the variables {', '.join(allowed_vars)} and log().")
    return toks


# ----------------------------------------------------------------------------- parser
@dataclass
class Node:
    """Minimal syntax tree kept alongside the SymPy value (used for the 'simplified form' check)."""
    op: str                 # num, var, log, add, mul, div, pow, neg (growth mode: fact, sqrt)
    kids: tuple = ()
    value: object = None


class _Parser:
    def __init__(self, toks, growth=False):
        self.toks = toks
        self.i = 0
        self.depth = 0
        self.growth = growth
        self.algebra = False

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def take(self, value=None):
        t = self.peek()
        if t is None or (value is not None and t.value != value):
            raise ParseError("The expression seems incomplete." if t is None else f"Expected '{value}' near '{t.value}'.")
        self.i += 1
        return t

    def deeper(self):
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise ParseError("Too many nested parentheses.")

    def parse(self):
        node = self.expr()
        if self.peek() is not None:
            raise ParseError(f"Unexpected '{self.peek().value}'.")
        return node

    def expr(self):
        node = self.term()
        while self.peek() and self.peek().value in "+-" and self.peek().kind == "op":
            op = self.take().value
            right = self.term()
            node = Node("add", (node, right if op == "+" else Node("neg", (right,))))
        return node

    def starts_atom(self, t):
        return t is not None and (t.kind in ("num", "name", "func") or t.value == "(")

    def term(self):
        node = self.unary()
        while True:
            t = self.peek()
            if t and t.kind == "op" and t.value in "*/":
                op = self.take().value
                right = self.unary()
                node = Node("mul" if op == "*" else "div", (node, right))
            elif self.starts_atom(t):                       # implicit multiplication: 3n, n(n+1), 2 log n
                node = Node("mul", (node, self.power()))
            else:
                return node

    def unary(self):
        t = self.peek()
        if t and t.kind == "op" and t.value in "+-":
            self.take()
            self.deeper()
            inner = self.unary()
            self.depth -= 1
            return inner if t.value == "+" else Node("neg", (inner,))
        return self.power()

    def power(self):
        base = self.atom()
        t = self.peek()
        if self.growth and t and t.kind == "op" and t.value == "!":     # n!
            self.take()
            base = Node("fact", (base,))
            t = self.peek()
        if t and t.kind == "op" and t.value == "^":
            self.take()
            self.deeper()
            exp = self.unary()
            self.depth -= 1
            return Node("pow", (base, exp))
        return base

    def atom(self):
        t = self.peek()
        if t is None:
            raise ParseError("The expression seems incomplete.")
        if t.kind == "num":
            self.take()
            return Node("num", value=t.value)
        if t.kind == "name":
            self.take()
            return Node("var", value=t.value)
        if t.kind == "func":
            self.take()
            nxt = self.peek()
            if nxt is not None and nxt.value == "(":
                arg = self.atom()                              # parenthesised argument
            elif nxt is not None and nxt.kind in ("name", "num"):
                arg = self.atom()                              # log n
            else:
                raise ParseError(f"{t.value} needs an argument, e.g. {t.value}(n).")
            return Node({"sqrt": "sqrt", "ln": "ln", "log10": "log10"}.get(t.value, "log"), (arg,))
        if t.value == "(":
            self.take()
            self.deeper()
            inner = self.expr()
            self.depth -= 1
            self.take(")")
            return inner
        raise ParseError(f"Unexpected '{t.value}'.")


def _to_sympy(node, growth=False, algebra=False):
    op = node.op
    if op in ("ln", "log10"):
        arg = _to_sympy(node.kids[0], growth, algebra)
        if arg.is_number and arg <= 0:
            raise ParseError("log needs a positive argument.")
        return sp.log(arg) if op == "ln" else sp.log(arg) / sp.log(10)
    if op == "fact":
        arg = _to_sympy(node.kids[0], growth, algebra)
        if arg != SYM["n"]:
            raise ParseError("Factorial is only supported as n!.")
        return sp.factorial(arg)
    if op == "sqrt":
        arg = _to_sympy(node.kids[0], growth, algebra)
        if arg.is_number and arg < 0:
            raise ParseError("sqrt needs a non-negative argument.")
        return sp.sqrt(arg)
    if op == "num":
        return sp.Rational(Fraction(node.value))
    if op == "var":
        return SYM[node.value]
    if op == "neg":
        return -_to_sympy(node.kids[0], growth, algebra)
    if op == "add":
        return _to_sympy(node.kids[0], growth, algebra) + _to_sympy(node.kids[1], growth, algebra)
    if op == "mul":
        return _to_sympy(node.kids[0], growth, algebra) * _to_sympy(node.kids[1], growth, algebra)
    if op == "div":
        d = _to_sympy(node.kids[1], growth, algebra)
        if d == 0:
            raise ParseError("Division by zero.")
        return _to_sympy(node.kids[0], growth, algebra) / d
    if op == "log":
        arg = _to_sympy(node.kids[0], growth, algebra)
        if arg.is_number and arg <= 0:
            raise ParseError("log needs a positive argument.")
        return log2(arg)
    if op == "pow":
        base = _to_sympy(node.kids[0], growth, algebra)
        exp = _to_sympy(node.kids[1], growth, algebra)
        if not exp.is_number:
            if growth and base.is_number and 2 <= base <= 10 and exp == SYM["n"]:
                return base ** exp                                     # exponential growth: 2^n
            if algebra and _small_exponent(exp) and (not base.is_number or 0 < base <= 10):
                return base ** exp                                     # x^(a+b), 2^(n+1), 2^(2n)
            raise ParseError("Exponents must be numbers (like n^2)" + (", or 2^n" if growth else ", not variables") + ".")
        limit = ALGEBRA_MAX_EXPONENT if algebra else MAX_EXPONENT
        if abs(exp) > limit:
            raise ParseError(f"Exponents larger than {limit} aren't supported here.")
        if base.is_number and abs(base) > 10 ** 6 and exp > 1:
            raise ParseError("That number is too large.")
        return base ** exp
    raise ParseError("Unsupported expression.")


def _small_exponent(exp):
    """A symbolic exponent built from allowed variables: polynomial of degree ≤ 3 with small coefficients."""
    try:
        poly = sp.Poly(exp, *sorted(exp.free_symbols, key=str))
    except sp.PolynomialError:
        return False
    return poly.total_degree() <= 3 and all(abs(c) <= 100 for c in poly.coeffs())


def _number(node):
    """Value of a constant sub-tree (for exponents), else None."""
    if node.op == "num":
        return Fraction(node.value)
    if node.op == "neg":
        v = _number(node.kids[0])
        return -v if v is not None else None
    if node.op in ("mul", "div", "add"):
        a, b = _number(node.kids[0]), _number(node.kids[1])
        if a is None or b is None or (node.op == "div" and b == 0):
            return None
        return a * b if node.op == "mul" else (a / b if node.op == "div" else a + b)
    return None


def _degree_bound(node):
    """Upper bound on the total polynomial degree (logs count as 1), computed before expanding."""
    op = node.op
    if op == "num":
        return 0
    if op in ("var", "log", "fact", "sqrt", "ln", "log10"):
        return 1
    if op == "neg":
        return _degree_bound(node.kids[0])
    if op == "add":
        return max(_degree_bound(k) for k in node.kids)
    if op in ("mul", "div"):
        return sum(_degree_bound(k) for k in node.kids)
    if op == "pow":
        e = _number(node.kids[1])
        if e is None:
            return 0                              # rejected later with a clearer message
        return _degree_bound(node.kids[0]) * min(abs(float(e)), MAX_EXPONENT + 1)
    return 0


# ----------------------------------------------------------------------------- public API
WRAPPER_RE = re.compile(r"^\s*(big\s*-?\s*)?(θ|Θ|theta|ϴ|o|O|ω|Ω|omega)\s*\(", re.IGNORECASE)
PREFIX_RE = re.compile(r"^\s*T\s*(?:_?\s*(?:best|worst|avg|average))?\s*(?:\([^)]*\))?\s*=", re.IGNORECASE)


@dataclass
class Parsed:
    text: str
    expr: object
    tree: Node
    wrapper: str | None = None       # 'theta' / 'O' / 'omega' if the input was wrapped, e.g. Θ(n^2)


def strip_wrapper(text):
    """'Θ(n^2)' -> ('n^2', 'theta').  'O(n)' -> ('n', 'O')."""
    m = WRAPPER_RE.match(text or "")
    if not m or not text.rstrip().endswith(")"):
        return text, None
    word = m.group(2).lower()
    kind = "theta" if word in ("θ", "theta", "ϴ") else ("omega" if word in ("ω", "omega") else "O")
    inner = text[m.end():].rstrip()[:-1]
    return inner, kind


def parse(text, allowed_vars=BASE_VARS, allow_wrapper=False, growth=False, algebra=False):
    """Parse untrusted text into a SymPy expression. Raises ParseError with a friendly message."""
    if not isinstance(text, str):
        raise ParseError("Enter an expression.")
    raw = text
    text = PREFIX_RE.sub("", text, count=1)
    wrapper = None
    inner, kind = strip_wrapper(text)
    if kind:
        wrapper = kind
        text = inner
    elif "=" in text:
        raise ParseError("Write just the expression, e.g. 3n + 4 (or T(n) = 3n + 4).")
    growth = growth or algebra
    toks = tokenize(text, allowed_vars, growth, algebra)
    tree = _Parser(toks, growth).parse()
    if _degree_bound(tree) > MAX_DEGREE:
        raise ParseError("That expression is too complex - T(n) functions here have small powers.")
    expr = sp.expand(_to_sympy(tree, growth, algebra))
    if expr.has(sp.zoo, sp.oo, sp.nan):
        raise ParseError("That expression isn't defined.")
    if wrapper and not allow_wrapper:
        pass                                    # callers decide what a wrapper means
    return Parsed(raw, expr, tree, wrapper)


def sympify_trusted(text, allowed_vars=BASE_VARS + ("i", "j")):
    """Parse an expression written by the exercise authors (same safe parser)."""
    return parse(text, allowed_vars).expr


# ----------------------------------------------------------------------------- comparison
SAMPLE_POINTS = [
    {"n": 8, "m": 3, "k": 5, "i": 2, "j": 1},
    {"n": 32, "m": 7, "k": 11, "i": 5, "j": 3},
    {"n": 128, "m": 13, "k": 2, "i": 9, "j": 4},
    {"n": 1024, "m": 29, "k": 17, "i": 13, "j": 6},
    {"n": 4096, "m": 101, "k": 37, "i": 21, "j": 10},
    {"n": 2 ** 16, "m": 257, "k": 3, "i": 34, "j": 15},
    {"n": 2 ** 20, "m": 1009, "k": 61, "i": 55, "j": 21},
]


def _value(expr, point):
    subs = {SYM[v]: sp.Integer(val) for v, val in point.items()}
    return sp.N(expr.subs(subs), 60)


def equivalent(a, b):
    """True if two expressions are equal as functions (log means log2)."""
    diff = sp.expand(sp.expand_log(a - b, force=True))
    if diff == 0:
        return True
    try:
        for p in SAMPLE_POINTS:
            va, vb = _value(a, p), _value(b, p)
            if abs(va - vb) > sp.Float("1e-30", 60) * max(1, abs(vb)):
                return False
        return True
    except (TypeError, ValueError):
        return False


def is_simplified(parsed):
    """Simplest form = a sum of distinct monomials with no brackets left to expand."""
    terms = []

    def flatten(node):
        if node.op == "add":
            for k in node.kids:
                flatten(k)
        elif node.op == "neg" and node.kids[0].op == "add":
            terms.append(None)
        else:
            terms.append(node)

    flatten(parsed.tree)
    if None in terms:
        return False

    def monomial(node):
        if node.op in ("num", "var"):
            return True
        if node.op == "log":
            return node.kids[0].op in ("var", "num")
        if node.op in ("mul", "div", "neg"):
            return all(monomial(k) for k in node.kids)
        if node.op == "pow":
            return monomial(node.kids[0]) and node.kids[1].op in ("num", "neg")
        return False

    if not all(monomial(t) for t in terms):
        return False
    canonical = sp.Add.make_args(parsed.expr) if parsed.expr != 0 else ()
    return len(terms) == len(canonical)


def pretty(expr):
    """Readable text: 4*n**2 + 7*n + 3 -> 4n² + 7n + 3, log(n)/log(2) -> log₂ n."""
    expr = sp.expand(expr)
    L = {v: sp.Symbol(f"__L{v}") for v in ("n", "m", "k", "i", "j")}
    for v, s_ in L.items():
        expr = expr.subs(sp.log(SYM[v]), s_ * LOG2)
    expr = sp.expand(expr)
    if expr == 0:
        return "0"
    order = list("nmkij")

    def key(term):
        c, mono = _split_coeff(term)
        degs = [sp.degree(mono, SYM[v]) if mono.has(SYM[v]) else 0 for v in order]
        logs = [sp.degree(mono, L[v]) if mono.has(L[v]) else 0 for v in order]
        total = sum(degs) + sum(logs) * 0.01
        return (-total, [-d for d in degs])

    terms = sorted(sp.Add.make_args(expr), key=key)
    parts = []
    for idx, term in enumerate(terms):
        c, mono = _split_coeff(term)
        sign = "-" if c < 0 else "+"
        c = abs(c)
        body = _mono_text(mono, L)
        gap = " " if body.startswith(("log", "(log")) else ""
        if body == "1":
            txt = _num_text(c)
        elif c == 1:
            txt = body
        elif c.q != 1:
            txt = f"{_num_text(c.p)}{gap}{body}/{c.q}" if c.p != 1 else f"{body}/{c.q}"
        else:
            txt = f"{_num_text(c)}{gap}{body}"
        if idx == 0:
            parts.append(("-" if sign == "-" else "") + txt)
        else:
            parts.append(f" {sign} {txt}")
    return "".join(parts)


def _split_coeff(term):
    c, rest = term.as_coeff_Mul()
    return sp.Rational(c), rest


def _num_text(c):
    c = sp.Rational(c)
    return str(c.p) if c.q == 1 else f"{c.p}/{c.q}"


SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _mono_text(mono, L):
    if mono == 1:
        return "1"
    pieces = []
    for v in "nmkij":
        d = sp.degree(mono, SYM[v]) if mono.has(SYM[v]) else 0
        if d:
            pieces.append(v + (str(d).translate(SUP) if d != 1 else ""))
    for v in "nmkij":
        d = sp.degree(mono, L[v]) if mono.has(L[v]) else 0
        if d:
            pieces.append(("(log₂ " + v + ")" + str(d).translate(SUP)) if d != 1 else ("log₂ " + v))
    text = ""
    for p_ in pieces:
        text += (" " if text and (p_.startswith("log") or p_.startswith("(log")) else "") + p_
    return text or str(mono)


# ----------------------------------------------------------------------------- asymptotic analysis
@dataclass(frozen=True)
class Signature:
    """Growth of one monomial: per variable (power, power of log)."""
    parts: tuple            # ((var, power, logpower), ...) sorted, zeros omitted

    def dominates(self, other):
        mine = {v: (p, l) for v, p, l in self.parts}
        theirs = {v: (p, l) for v, p, l in other.parts}
        ge = all(mine.get(v, (0, 0)) >= theirs.get(v, (0, 0)) for v in set(mine) | set(theirs))
        return ge and mine != theirs

    def text(self):
        if not self.parts:
            return "1"
        out = ""
        for v, p, _ in self.parts:
            if p:
                out += v + (str(p).translate(SUP) if p != 1 else "")
        for v, _, l in self.parts:
            if l:
                out += (" " if out else "") + ("log " + v if l == 1 else f"(log {v}){str(l).translate(SUP)}")
        return out


def _terms_with_signatures(expr, variables=BASE_VARS):
    L = {v: sp.Symbol(f"__L{v}", positive=True) for v in variables}
    e = sp.expand(sp.expand_log(expr, force=True))
    for v in variables:
        e = e.subs(sp.log(SYM[v]), L[v] * LOG2)
    e = sp.expand(e)
    out = []
    for term in sp.Add.make_args(e):
        c, mono = term.as_coeff_Mul()
        parts = []
        for v in variables:
            p = sp.degree(mono, SYM[v]) if mono.has(SYM[v]) else 0
            lp = sp.degree(mono, L[v]) if mono.has(L[v]) else 0
            if p or lp:
                parts.append((v, int(p), int(lp)))
        out.append((sp.Rational(c) if c.is_Rational else c, Signature(tuple(parts))))
    return out


def dominant(expr, variables=BASE_VARS):
    """Set of growth signatures that aren't dominated by another term (positive terms only)."""
    terms = [(c, s) for c, s in _terms_with_signatures(expr, variables) if c > 0]
    sigs = {s for _, s in terms}
    return {s for s in sigs if not any(o.dominates(s) for o in sigs)}


def _sig_order(sig):
    return (-sum(p for _, p, _ in sig.parts), -sum(l for _, _, l in sig.parts), ["nmkij".index(v) for v, _, _ in sig.parts])


def theta_text(expr, variables=BASE_VARS):
    sigs = sorted(dominant(expr, variables), key=_sig_order)
    return " + ".join(s.text() for s in sigs) or "1"


def leading_coefficients(expr, variables=BASE_VARS):
    dom = dominant(expr, variables)
    return {s: sum(c for c, t in _terms_with_signatures(expr, variables) if t == s) for s in dom}


def degree_in(expr, var):
    dom = dominant(expr)
    return max(((p, l) for s in dom for v, p, l in s.parts if v == var), default=(0, 0))


def has_var(expr, var):
    return expr.has(SYM[var])
