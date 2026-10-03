"""T(n) Analysis: the operation-counting model, exercise derivation, simulation, and grading.

COUNTING MODEL (used for every T(n) exercise, solution, hint and grade)
------------------------------------------------------------------------
One primitive operation is counted for each of:
    =                      assignment (also writing an array element:  A[i] = x)
    + - * / mod div        arithmetic operator
    < <= > >= == !=        comparison
    and or not             logical operator
    i++  i--               increment / decrement (one operation)
    return                 returning (plus whatever the returned expression costs)
    f(...)                 calling a function or procedure (plus its arguments)
Free (cost 0): reading a variable or constant, indexing an array (A[i]), else, the procedure header.

Loops are written with all three parts visible, for (init; condition; update). For a loop whose body
runs I times each time the loop is reached:  init runs once, the condition is checked I + 1 times
(the final, failed check ends the loop), and the update runs I times.

T(n) is the number of primitive operations under this model - a model of running time, not a count
of CPU instructions. Its purpose is to show how an algorithm's structure produces its growth.
"""
from __future__ import annotations

import ast
import copy
import re
from dataclasses import dataclass, field

import sympy as sp

from engine import tnmath
from engine.tnmath import SYM, ParseError

MODEL_RULES = [
    ("=", "assignment (also storing into an array element, A[i] = x)", 1),
    ("+  -  *  /  mod  div", "each arithmetic operator", 1),
    ("<  <=  >  >=  ==  !=", "each comparison", 1),
    ("and  or  not", "each logical operator", 1),
    ("i++  i--", "increment / decrement", 1),
    ("return", "returning a value (plus the cost of the returned expression)", 1),
    ("f(...)", "calling a function or procedure (plus its arguments)", 1),
    ("x, 5, A[i]", "reading a variable, a constant or an array element", 0),
]

CASE_LABELS = {"all": "", "best": "best", "worst": "worst"}


# ============================================================================ statements
@dataclass
class Stmt:
    kind: str                      # assign, call, return, for, while, if
    a: str = ""                    # target / expr / var
    b: str = ""                    # expr / cond
    c: str = ""                    # cond (for)
    d: str = ""                    # update (for)
    body: list = field(default_factory=list)
    orelse: list = field(default_factory=list)
    iters: str = ""                # per-entry iteration count for while / multiplicative for loops


def assign(target, expr):
    return Stmt("assign", target, expr)


def call(expr):
    return Stmt("call", expr)


def ret(expr=""):
    return Stmt("return", expr)


def loop(var, start, cond, update, *body, iters=""):
    """for (var = start; cond; update)"""
    return Stmt("for", var, start, cond, update, list(body), iters=iters)


def while_(cond, *body, iters=""):
    return Stmt("while", "", cond, body=list(body), iters=iters)


def if_(cond, then, orelse=()):
    return Stmt("if", "", cond, body=list(then), orelse=list(orelse))


# ============================================================================ expression handling
def _to_python(expr):
    s = re.sub(r"\bmod\b", "%", expr)
    s = re.sub(r"\bdiv\b", "//", s)
    s = re.sub(r"\btrue\b", "True", s)
    s = re.sub(r"\bfalse\b", "False", s)
    return s


def _parse_py(expr):
    return ast.parse(_to_python(expr), mode="eval").body


def op_count(expr, proc_name=None):
    """Primitive operations needed to evaluate an expression under the counting model."""
    if not expr:
        return 0
    return _ops(_parse_py(expr))


def _ops(node):
    if isinstance(node, ast.BinOp):
        return 1 + _ops(node.left) + _ops(node.right)
    if isinstance(node, ast.Compare):
        return len(node.ops) + _ops(node.left) + sum(_ops(c) for c in node.comparators)
    if isinstance(node, ast.BoolOp):
        return len(node.values) - 1 + sum(_ops(v) for v in node.values)
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
            return 0                                             # a negative literal like -1
        return 1 + _ops(node.operand)
    if isinstance(node, ast.Call):
        return 1 + sum(_ops(a) for a in node.args)
    if isinstance(node, ast.Subscript):
        return _ops(node.value) + _ops(node.slice)
    if isinstance(node, (ast.Name, ast.Constant)):
        return 0
    if isinstance(node, ast.List):
        return sum(_ops(e) for e in node.elts)
    raise ValueError(f"unsupported expression node {type(node).__name__}")


def ops_breakdown(expr):
    """Human-readable list of the operations in an expression, e.g. ['+', '<']."""
    out = []

    def walk(node):
        if isinstance(node, ast.BinOp):
            out.append({ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Mod: "mod",
                        ast.FloorDiv: "div"}.get(type(node.op), "op"))
            walk(node.left)
            walk(node.right)
        elif isinstance(node, ast.Compare):
            for o in node.ops:
                out.append({ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==",
                            ast.NotEq: "!="}.get(type(o), "cmp"))
            walk(node.left)
            for c in node.comparators:
                walk(c)
        elif isinstance(node, ast.BoolOp):
            out.extend(["and" if isinstance(node.op, ast.And) else "or"] * (len(node.values) - 1))
            for v in node.values:
                walk(v)
        elif isinstance(node, ast.UnaryOp):
            if not (isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant)):
                out.append("not" if isinstance(node.op, ast.Not) else "-")
            walk(node.operand)
        elif isinstance(node, ast.Call):
            out.append(f"call {node.func.id}()" if isinstance(node.func, ast.Name) else "call")
            for a in node.args:
                walk(a)
        elif isinstance(node, ast.Subscript):
            walk(node.value)
            walk(node.slice)

    if expr:
        walk(_parse_py(expr))
    return out


# ============================================================================ rows
@dataclass
class Row:
    key: str
    line: int
    text: str           # statement text shown in the table
    cost: int
    role: str           # stmt, init, cond, update, return, call, if
    loop: int | None    # index of the loop this row controls (init/cond/update)
    depth: int          # loop nesting depth of the row
    ops: list           # names of the counted operations


@dataclass
class LoopInfo:
    idx: int
    line: int
    header: str
    kind: str                       # for / while
    var: str | None
    per_entry: object = None        # iterations each time the loop is reached (sympy)
    entries: object = None          # how many times the loop is reached in total
    cond_key: str = ""
    init_key: str = ""
    update_key: str = ""
    body_keys: list = field(default_factory=list)
    inner: list = field(default_factory=list)
    parent: int | None = None
    range: tuple | None = None      # (var, lo, hi) for unit-step loops


class Program:
    """Rendered code + rows + loops for one exercise."""

    def __init__(self, name, params, body):
        self.name, self.params, self.body = name, params, body
        self.lines, self.rows, self.loops = [], [], []
        self.lines.append(f"procedure {name}({', '.join(params)})")
        self._stmt_rows = {}
        self._emit(body, 1, None, 0)

    def _add_row(self, line, text, cost, role, loop, depth, ops):
        r = Row(f"r{len(self.rows) + 1}", line, text, cost, role, loop, depth, ops)
        self.rows.append(r)
        return r

    def _emit(self, block, indent, loop_idx, depth):
        pad = "    " * indent
        for st in block:
            line = len(self.lines) + 1
            k = st.kind
            if k == "assign":
                self.lines.append(f"{pad}{st.a} = {st.b}")
                target_ops = op_count(st.a) if "[" in st.a else 0
                r = self._add_row(line, f"{st.a} = {st.b}", 1 + op_count(st.b) + target_ops, "stmt", None, depth,
                                  ["="] + ops_breakdown(st.b) + (ops_breakdown(st.a) if "[" in st.a else []))
                self._stmt_rows[id(st)] = [r.key]
                self._note_body(loop_idx, r.key)
            elif k == "call":
                self.lines.append(f"{pad}{st.a}")
                r = self._add_row(line, st.a, op_count(st.a), "call", None, depth, ops_breakdown(st.a))
                self._stmt_rows[id(st)] = [r.key]
                self._note_body(loop_idx, r.key)
            elif k == "return":
                text = f"return {st.a}".rstrip()
                self.lines.append(f"{pad}{text}")
                r = self._add_row(line, text, 1 + op_count(st.a), "return", None, depth, ["return"] + ops_breakdown(st.a))
                self._stmt_rows[id(st)] = [r.key]
                self._note_body(loop_idx, r.key)
            elif k == "for":
                header = f"for ({st.a} = {st.b}; {st.c}; {st.d})"
                self.lines.append(f"{pad}{header}")
                li = LoopInfo(len(self.loops), line, header, "for", st.a, parent=loop_idx)
                self.loops.append(li)
                if loop_idx is not None:
                    self.loops[loop_idx].inner.append(li.idx)
                init = self._add_row(line, f"{st.a} = {st.b}", 1 + op_count(st.b), "init", li.idx, depth, ["="] + ops_breakdown(st.b))
                cond = self._add_row(line, st.c, op_count(st.c), "cond", li.idx, depth, ops_breakdown(st.c))
                upd_cost, upd_ops = _update_cost(st.d)
                upd = self._add_row(line, st.d, upd_cost, "update", li.idx, depth, upd_ops)
                li.init_key, li.cond_key, li.update_key = init.key, cond.key, upd.key
                self._stmt_rows[id(st)] = [init.key, cond.key, upd.key]
                self._note_body(loop_idx, init.key, cond.key, upd.key)
                self._emit(st.body, indent + 1, li.idx, depth + 1)
            elif k == "while":
                header = f"while ({st.b})"
                self.lines.append(f"{pad}{header}")
                li = LoopInfo(len(self.loops), line, header, "while", None, parent=loop_idx)
                self.loops.append(li)
                if loop_idx is not None:
                    self.loops[loop_idx].inner.append(li.idx)
                cond = self._add_row(line, st.b, op_count(st.b), "cond", li.idx, depth, ops_breakdown(st.b))
                li.cond_key = cond.key
                self._stmt_rows[id(st)] = [cond.key]
                self._note_body(loop_idx, cond.key)
                self._emit(st.body, indent + 1, li.idx, depth + 1)
            elif k == "if":
                self.lines.append(f"{pad}if ({st.b})")
                r = self._add_row(line, st.b, op_count(st.b), "if", None, depth, ops_breakdown(st.b))
                self._stmt_rows[id(st)] = [r.key]
                self._note_body(loop_idx, r.key)
                self._emit(st.body, indent + 1, loop_idx, depth)
                if st.orelse:
                    self.lines.append(f"{pad}else")
                    self._emit(st.orelse, indent + 1, loop_idx, depth)
            else:
                raise ValueError(k)

    def _note_body(self, loop_idx, *keys):
        idx = loop_idx
        while idx is not None:
            self.loops[idx].body_keys.extend(keys)
            idx = self.loops[idx].parent

    @property
    def code(self):
        return "\n".join(self.lines)

    def row(self, key):
        return next(r for r in self.rows if r.key == key)


def _update_cost(update):
    u = update.strip()
    if re.fullmatch(r"[A-Za-z_]\w*\s*(\+\+|--)", u):
        return 1, ["++" if "++" in u else "--"]
    m = re.fullmatch(r"([A-Za-z_]\w*)\s*=\s*(.+)", u)
    if m:
        return 1 + op_count(m.group(2)), ["="] + ops_breakdown(m.group(2))
    raise ValueError(f"unsupported loop update {update!r}")


# ============================================================================ symbolic execution counts
def _e(text):
    return tnmath.sympify_trusted(str(text))


def derive_counts(prog):
    """Execution counts for programs without data-dependent branches (no if / early return)."""
    counts = {}

    def total(per_pass, ctx):
        s = per_pass
        for kind, *rest in reversed(ctx):
            if kind == "range":
                v, lo, hi = rest
                s = sp.summation(s, (SYM[v], lo, hi))
            else:
                s = s * rest[0]
        return sp.expand(s)

    loop_iter = iter(prog.loops)
    row_iter = iter(prog.rows)

    def walk(block, ctx):
        for st in block:
            if st.kind in ("assign", "call", "return"):
                counts[next(row_iter).key] = total(sp.Integer(1), ctx)
            elif st.kind == "for":
                li = next(loop_iter)
                init, cond, upd = next(row_iter), next(row_iter), next(row_iter)
                per, rng = _for_iterations(st)
                li.per_entry = per
                li.entries = total(sp.Integer(1), ctx)
                li.range = rng
                counts[init.key] = li.entries
                counts[cond.key] = total(per + 1, ctx)
                counts[upd.key] = total(per, ctx)
                walk(st.body, ctx + ([("range",) + rng] if rng else [("mult", per)]))
            elif st.kind == "while":
                li = next(loop_iter)
                cond = next(row_iter)
                per = _e(st.iters)
                li.per_entry = per
                li.entries = total(sp.Integer(1), ctx)
                counts[cond.key] = total(per + 1, ctx)
                walk(st.body, ctx + [("mult", per)])
            else:
                raise ValueError("derive_counts can't handle data-dependent branches; give explicit counts")

    walk(prog.body, [])
    return counts


def _for_iterations(st):
    """Iterations per entry and (var, lo, hi) for unit-step loops."""
    var = st.a
    start = _e(st.b)
    upd = st.d.strip()
    m = re.fullmatch(rf"{var}\s*(<=|<|>=|>)\s*(.+)", st.c.strip())
    if st.iters:
        return _e(st.iters), None
    if not m:
        raise ValueError(f"can't derive iterations of {st.c!r}; give iters=")
    op, bound = m.group(1), _e(m.group(2))
    if upd == f"{var}++":
        hi = bound - 1 if op == "<" else bound if op == "<=" else None
        if hi is None:
            raise ValueError("increasing loop needs < or <=")
        return sp.expand(hi - start + 1), (var, start, hi)
    if upd == f"{var}--":
        lo = bound + 1 if op == ">" else bound if op == ">=" else None
        if lo is None:
            raise ValueError("decreasing loop needs > or >=")
        return sp.expand(start - lo + 1), (var, lo, start)
    raise ValueError(f"loop update {upd!r} needs iters=")


# ============================================================================ simulator (verification)
class _Return(Exception):
    def __init__(self, value):
        self.value = value


class Simulator:
    """Runs a Program, counting how many times each row executes. Used to verify every exercise."""

    MAX_STEPS = 2_000_000

    def __init__(self, prog):
        self.prog = prog
        self.counts = {r.key: 0 for r in prog.rows}
        self.steps = 0
        self._compiled = {}

    def run(self, args):
        env = dict(args)
        self.call_proc(env)
        return self.counts

    def call_proc(self, env):
        it = iter(self.prog.rows)
        keys = {}
        self._assign_keys(self.prog.body, it, keys)
        try:
            self._block(self.prog.body, env, keys)
        except _Return as r:
            return r.value
        return None

    def _assign_keys(self, block, it, keys):
        for st in block:
            if st.kind in ("assign", "call", "return", "while", "if"):
                keys[id(st)] = [next(it).key]
            elif st.kind == "for":
                keys[id(st)] = [next(it).key, next(it).key, next(it).key]
            self._assign_keys(st.body, it, keys)
            self._assign_keys(st.orelse, it, keys)

    def _hit(self, key):
        self.counts[key] += 1
        self.steps += 1
        if self.steps > self.MAX_STEPS:
            raise RuntimeError("simulation too long")

    def _eval(self, expr, env):
        node = self._compiled.get(expr)
        if node is None:
            node = self._compiled[expr] = _parse_py(expr)
        return self._ev(node, env)

    def _ev(self, n, env):
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.Name):
            return env[n.id]
        if isinstance(n, ast.BinOp):
            a, b = self._ev(n.left, env), self._ev(n.right, env)
            return {ast.Add: lambda: a + b, ast.Sub: lambda: a - b, ast.Mult: lambda: a * b,
                    ast.Div: lambda: a / b, ast.Mod: lambda: a % b, ast.FloorDiv: lambda: a // b}[type(n.op)]()
        if isinstance(n, ast.UnaryOp):
            v = self._ev(n.operand, env)
            return -v if isinstance(n.op, ast.USub) else (not v)
        if isinstance(n, ast.BoolOp):
            if isinstance(n.op, ast.And):
                return all(self._ev(v, env) for v in n.values)
            return any(self._ev(v, env) for v in n.values)
        if isinstance(n, ast.Compare):
            left = self._ev(n.left, env)
            for op, comp in zip(n.ops, n.comparators):
                right = self._ev(comp, env)
                ok = {ast.Lt: left < right, ast.LtE: left <= right, ast.Gt: left > right, ast.GtE: left >= right,
                      ast.Eq: left == right, ast.NotEq: left != right}[type(op)]
                if not ok:
                    return False
                left = right
            return True
        if isinstance(n, ast.Subscript):
            return self._ev(n.value, env)[self._ev(n.slice, env)]
        if isinstance(n, ast.Call):
            name = n.func.id
            args = [self._ev(a, env) for a in n.args]
            if name == "print":
                return None
            if name == self.prog.name:
                sub = dict(zip(self.prog.params, args))
                sub.update({k: v for k, v in env.items() if k not in self.prog.params and isinstance(v, list)})
                return self.call_proc(sub)
            if name in ("floor",):
                return int(args[0] // 1)
            raise ValueError(f"unknown function {name}")
        raise ValueError(f"unsupported node {type(n).__name__}")

    def _store(self, target, value, env):
        node = _parse_py(target)
        if isinstance(node, ast.Name):
            env[node.id] = value
        else:
            self._ev(node.value, env)[self._ev(node.slice, env)] = value

    def _block(self, block, env, keys):
        for st in block:
            k = st.kind
            ks = keys[id(st)]
            if k == "assign":
                self._hit(ks[0])
                self._store(st.a, self._eval(st.b, env), env)
            elif k == "call":
                self._hit(ks[0])
                self._eval(st.a, env)
            elif k == "return":
                self._hit(ks[0])
                raise _Return(self._eval(st.a, env) if st.a else None)
            elif k == "for":
                self._hit(ks[0])
                env[st.a] = self._eval(st.b, env)
                while True:
                    self._hit(ks[1])
                    if not self._eval(st.c, env):
                        break
                    self._block(st.body, env, keys)
                    self._hit(ks[2])
                    u = st.d.strip()
                    if u.endswith("++"):
                        env[st.a] += 1
                    elif u.endswith("--"):
                        env[st.a] -= 1
                    else:
                        tgt, expr = u.split("=", 1)
                        self._store(tgt.strip(), self._eval(expr.strip(), env), env)
            elif k == "while":
                while True:
                    self._hit(ks[0])
                    if not self._eval(st.b, env):
                        break
                    self._block(st.body, env, keys)
            elif k == "if":
                self._hit(ks[0])
                if self._eval(st.b, env):
                    self._block(st.body, env, keys)
                else:
                    self._block(st.orelse, env, keys)


# ============================================================================ exercise assembly
TOPIC_NOTES = {
    "tn_constant": "No loops: every statement runs exactly once, so T(n) is just the sum of the statement costs.",
    "tn_single": "Count the loop control too: init once, the condition I + 1 times, the update I times, the body I times.",
    "tn_sequential": "Sections that run one after another ADD: T(n) = T₁(n) + T₂(n).",
    "tn_nested": "The inner loop runs completely for every outer iteration, so its rows are multiplied by the outer count.",
    "tn_dependent": "When the inner bound depends on the outer variable, add up the inner counts: 1 + 2 + … + n = n(n + 1)/2.",
    "tn_log": "Multiplying (or dividing) the loop variable by 2 reaches n after log₂ n steps.",
    "tn_multi": "Keep independent sizes separate: n and m stay as different variables, e.g. T(n, m) = 3nm + 2n + 2.",
    "tn_conditional": "The count depends on the data, so there is a best case and a worst case for each size n.",
    "tn_algorithms": "Count the full algorithm row by row, then simplify and classify.",
}


class Exercise:
    """A T(n) exercise built from a structured program and verified by simulation."""

    def __init__(self, spec):
        self.spec = spec
        self.id = spec["id"]
        self.vars = spec.get("vars", ["n"])
        self.prog = Program(spec["name"], spec["params"], spec["body"])
        self.cases = list(spec["execs"].keys()) if spec.get("execs") else ["all"]
        if spec.get("execs"):
            self.counts = {}
            for case, exprs in spec["execs"].items():
                if len(exprs) != len(self.prog.rows):
                    raise ValueError(f"{self.id}: {case} needs {len(self.prog.rows)} counts, got {len(exprs)}")
                self.counts[case] = {r.key: sp.expand(_e(x)) for r, x in zip(self.prog.rows, exprs)}
            self.auto = False
        else:
            self.counts = {"all": derive_counts(self.prog)}
            self.auto = True
        self.T = {c: sp.expand(sum(r.cost * self.counts[c][r.key] for r in self.prog.rows)) for c in self.cases}

    # -- formatting helpers
    def fn(self, case="all"):
        args = ", ".join(self.vars)
        label = CASE_LABELS.get(case, case)
        return f"T{('_' + label) if label else ''}({args})"

    def table(self, case):
        out = []
        for r in self.prog.rows:
            e = self.counts[case][r.key]
            out.append({"key": r.key, "line": r.line, "text": r.text, "cost": r.cost, "role": r.role,
                        "ops": r.ops, "exec": tnmath.pretty(e), "total": tnmath.pretty(r.cost * e)})
        return out

    def sum_text(self, case):
        parts = []
        for r in self.prog.rows:
            e = self.counts[case][r.key]
            t = sp.expand(r.cost * e)
            if t == 0:
                continue
            txt = tnmath.pretty(t)
            parts.append(f"({txt})" if (" + " in txt or " - " in txt) else txt)
        return " + ".join(parts) or "0"

    def theta(self, case):
        return tnmath.theta_text(self.T[case], tuple(self.vars))

    def dominant_text(self, case):
        lead = tnmath.leading_coefficients(self.T[case], tuple(self.vars))
        return " + ".join(tnmath.pretty(c * _sig_expr(s)) for s, c in sorted(lead.items(), key=lambda kv: kv[0].text()))

    # -- variants used to recognise common mistakes
    def variants(self, case):
        rows, cnt = self.prog.rows, self.counts[case]
        out = []

        def T_with(fn):
            return sp.expand(sum(fn(r) for r in rows))

        if self.prog.loops:
            entries = {li.cond_key: (li.entries if li.entries is not None else None) for li in self.prog.loops}
            if all(v is not None for v in entries.values()):
                out.append(("missed_final_check", T_with(lambda r: r.cost * (cnt[r.key] - entries[r.key]) if r.key in entries else r.cost * cnt[r.key])))
            out.append(("no_loop_control", T_with(lambda r: 0 if r.role in ("init", "cond", "update") else r.cost * cnt[r.key])))
            out.append(("cond_as_iterations", T_with(lambda r: r.cost * (cnt[r.key] - 1) if r.role == "cond" and r.depth == 0 else r.cost * cnt[r.key])))
        out.append(("statements_not_operations", T_with(lambda r: (1 if r.cost else 0) * cnt[r.key])))
        out.append(("only_body", T_with(lambda r: r.cost * cnt[r.key] if r.depth == max(x.depth for x in rows) and r.role not in ("init", "cond", "update") else 0)))
        if self.auto and any(li.parent is not None for li in self.prog.loops):
            # inner loops counted once in total instead of once per outer iteration
            once = {}
            for li in self.prog.loops:
                if li.parent is None:
                    continue
                outer = self.prog.loops[li.parent]
                factor = outer.per_entry if outer.per_entry is not None else 1
                for k in [li.init_key, li.cond_key, li.update_key] + li.body_keys:
                    if k:
                        once[k] = factor
            if once:
                out.append(("inner_once", T_with(lambda r: r.cost * sp.cancel(cnt[r.key] / once[r.key]) if r.key in once else r.cost * cnt[r.key])))
        return [(cat, expr) for cat, expr in out if not tnmath.equivalent(expr, self.T[case])]

    # -- hints
    def hints(self):
        h = [TOPIC_NOTES.get(self.spec["topic"], "Work row by row: cost × executions.")]
        case = "worst" if "worst" in self.cases else self.cases[0]
        cnt = self.counts[case]
        if not self.prog.loops:
            r = max(self.prog.rows, key=lambda x: x.cost)
            h.append(f"Count operator symbols on each line. `{r.text}` contains {', '.join(r.ops)} → cost {r.cost}.")
            h.append("Every line runs exactly once, so its total is just its cost.")
            h.append("Add up the costs of all the rows to get T(n). It will be a constant.")
            return h
        outer = self.prog.loops[0]
        cond = self.prog.row(outer.cond_key)
        if outer.per_entry is not None:
            h.append(f"The loop on line {outer.line} runs its body {tnmath.pretty(outer.per_entry)} times, so its condition `{cond.text}` "
                     f"is checked {tnmath.pretty(cnt[cond.key])} times (one extra, failed check ends the loop).")
        else:
            h.append(f"Start with the loop on line {outer.line}: how many times is `{cond.text}` checked in the "
                     f"{case} case? (Its final check is the one that fails.)")
        inner = next((li for li in self.prog.loops if li.parent is not None), None)
        deepest = max(self.prog.rows, key=lambda r: (r.depth, r.cost))
        if inner is not None and inner.per_entry is not None:
            h.append(f"The inner loop on line {inner.line} runs {tnmath.pretty(inner.per_entry)} times for EACH outer iteration, "
                     f"so the innermost statement `{deepest.text}` runs {tnmath.pretty(cnt[deepest.key])} times in total.")
        else:
            h.append(f"The statement `{deepest.text}` costs {deepest.cost} and runs {tnmath.pretty(cnt[deepest.key])} times "
                     f"in the {case} case.")
        lead = self.dominant_text(case)
        h.append(f"Multiply each row's cost by its executions and add everything up. Check: the largest term of "
                 f"{self.fn(case)} should be {lead}.")
        return h

    # -- guided steps
    def guided(self):
        steps = []
        if self.auto:
            for li in self.prog.loops:
                allowed = self.vars + _outer_vars(self.prog, li)
                cond = self.prog.row(li.cond_key)
                if li.per_entry is not None:
                    steps.append({"id": f"L{li.idx}-iter", "allowed": allowed,
                                  "q": f"Line {li.line}, `{li.header}`: how many times does its body run each time the loop is reached?",
                                  "answer": li.per_entry,
                                  "explain": _iter_explain(li)})
                steps.append({"id": f"L{li.idx}-cond", "allowed": self.vars,
                              "q": f"In total (over the whole run), how many times is the condition `{cond.text}` evaluated?",
                              "answer": self.counts["all"][li.cond_key],
                              "explain": _cond_explain(li, self.counts["all"][li.cond_key])})
            inner_rows = [r for r in self.prog.rows if r.depth == max(x.depth for x in self.prog.rows)
                          and r.role not in ("init", "cond", "update")]
            if self.prog.loops and inner_rows:
                cost = sum(r.cost for r in inner_rows)
                lines = sorted({r.line for r in inner_rows})
                steps.append({"id": "body-cost", "allowed": self.vars,
                              "q": f"What does one pass through the innermost body (line{'s' if len(lines) > 1 else ''} "
                                   f"{', '.join(map(str, lines))}) cost?",
                              "answer": sp.Integer(cost),
                              "explain": "; ".join(f"`{r.text}`: {', '.join(r.ops) or 'nothing'} → {r.cost}" for r in inner_rows)})
                steps.append({"id": "body-total", "allowed": self.vars,
                              "q": f"How many times does `{inner_rows[0].text}` run in total?",
                              "answer": self.counts["all"][inner_rows[0].key],
                              "explain": "Multiply the iteration counts of every loop around it (or add them up when the inner count changes)."})
            if not self.prog.loops:
                for r in self.prog.rows:
                    steps.append({"id": f"cost-{r.key}", "allowed": self.vars, "q": f"Line {r.line}: what does `{r.text}` cost?",
                                  "answer": sp.Integer(r.cost), "explain": f"{', '.join(r.ops) or 'no operations'} → {r.cost}"})
        else:
            for case in self.cases:
                varying = [r for r in self.prog.rows if not self.counts[case][r.key].is_number or self.counts[case][r.key] > 1][:5]
                for r in varying:
                    steps.append({"id": f"{case}-{r.key}", "allowed": self.vars,
                                  "q": f"{'In the ' + case + ' case: h' if case != 'all' else 'H'}ow many times does `{r.text}` (line {r.line}) execute?",
                                  "answer": self.counts[case][r.key],
                                  "explain": self.spec.get("case_notes", {}).get(case, "")})
        for case in self.cases:
            steps.append({"id": f"{case}-combine", "allowed": self.vars, "final": False,
                          "q": f"Combine the rows: write {self.fn(case)} as Σ cost × executions (no need to simplify yet).",
                          "answer": self.T[case], "explain": f"{self.fn(case)} = {self.sum_text(case)}"})
            steps.append({"id": f"{case}-simplify", "allowed": self.vars, "simplify": True,
                          "q": f"Simplify {self.fn(case)}: collect like terms into a sum of distinct terms.",
                          "answer": self.T[case], "explain": f"{self.fn(case)} = {tnmath.pretty(self.T[case])}"})
            steps.append({"id": f"{case}-theta", "allowed": self.vars, "theta": True,
                          "q": f"Keep the dominant term and drop its constant: {self.fn(case)} ∈ Θ(?)",
                          "answer": self.T[case], "explain": f"Dominant term {self.dominant_text(case)} → Θ({self.theta(case)})"})
        return steps

    # -- complete stored payload
    def payload(self):
        sp_ = self.spec
        cases = {}
        for c in self.cases:
            cases[c] = {"T": str(self.T[c]), "T_text": tnmath.pretty(self.T[c]), "sum": self.sum_text(c),
                        "theta": self.theta(c), "dominant": self.dominant_text(c), "table": self.table(c),
                        "variants": [(cat, str(e)) for cat, e in self.variants(c)]}
        steps = [{k: (str(v) if isinstance(v, sp.Basic) else v) for k, v in s.items()} for s in self.guided()]
        level = sp_["level"]
        return {
            "id": self.id, "track": "tn", "type": "tn", "topic": sp_["topic"], "level": level,
            "difficulty": "beginner" if level <= 3 else ("intermediate" if level <= 6 else "advanced"),
            "title": sp_["title"], "prompt": sp_.get("prompt", ""), "code": self.prog.code, "vars": self.vars,
            "assumptions": sp_.get("assumptions", ""), "note": sp_.get("note", ""), "cases": self.cases,
            "fn": {c: self.fn(c) for c in self.cases}, "case_notes": sp_.get("case_notes", {}),
            "table_blank": sp_.get("blank", "exec"), "mode": sp_.get("mode", "table" if level <= 3 else "direct"),
            "rows": [{"key": r.key, "line": r.line, "text": r.text, "cost": r.cost, "role": r.role, "ops": r.ops}
                     for r in self.prog.rows],
            "loops": [{"line": li.line, "header": li.header, "parent": li.parent} for li in self.prog.loops],
            "solution": cases, "hints": self.hints(), "guided": steps,
            "tags": ["tn", sp_["topic"]] + sp_.get("tags", []),
        }


def _sig_expr(sig):
    e = sp.Integer(1)
    for v, p, l in sig.parts:
        e *= SYM[v] ** p * tnmath.log2(SYM[v]) ** l
    return e


def _outer_vars(prog, li):
    out, idx = [], li.parent
    while idx is not None:
        if prog.loops[idx].var:
            out.append(prog.loops[idx].var)
        idx = prog.loops[idx].parent
    return out


def _iter_explain(li):
    if li.range is not None:
        v, lo, hi = li.range
        return f"{v} takes the values {tnmath.pretty(lo)}, …, {tnmath.pretty(hi)} → {tnmath.pretty(li.per_entry)} iterations."
    return f"The loop variable is multiplied/divided each time, so it takes {tnmath.pretty(li.per_entry)} iterations to cross the bound."


def _cond_explain(li, total):
    per = tnmath.pretty(li.per_entry + 1) if li.per_entry is not None else "iterations + 1"
    if li.entries is not None and li.entries != 1:
        return (f"Each time the loop is reached its condition is checked {per} times (the last check fails), and the loop is "
                f"reached {tnmath.pretty(li.entries)} times → {tnmath.pretty(total)}.")
    return f"{per} checks: one per iteration plus the final failed check → {tnmath.pretty(total)}."


def verify(spec, exercise=None):
    """Run the simulator for every size/case and compare with the symbolic counts. Returns a list of errors."""
    ex = exercise or Exercise(spec)
    errors = []
    for size in spec["sizes"]:
        for case in ex.cases:
            args = spec["setup"](case, dict(size))
            sim = Simulator(ex.prog)
            try:
                counts = sim.run(copy.deepcopy(args))
            except Exception as e:  # noqa: BLE001
                errors.append(f"{case} {size}: simulation failed: {e!r}")
                continue
            for r in ex.prog.rows:
                expected = ex.counts[case][r.key].subs({SYM[k]: v for k, v in size.items()})
                expected = sp.nsimplify(sp.N(expected, 30))
                if expected != counts[r.key]:
                    errors.append(f"{case} {size}: row {r.key} `{r.text}` expected {expected}, simulated {counts[r.key]}")
    return errors


# ============================================================================ grading
MISTAKE_MESSAGES = {
    "asymptotic_only": ("This box asks for the operation-count function, not only its asymptotic class.",
                        "Write the full count, e.g. T(n) = 4n² + 3n + 2. You can then simplify it to Θ(n²) in the second box."),
    "missed_final_check": ("You appear to have left out the final condition check of the loop(s).",
                           "A loop whose body runs I times evaluates its condition I + 1 times: the last, failed comparison is "
                           "what ends the loop."),
    "cond_as_iterations": ("Your count is one short for the outer loop's condition.",
                           "The condition is checked once more than the body runs - the final check fails and ends the loop."),
    "no_loop_control": ("You counted the work inside the loops but not the loop control.",
                        "Each loop also costs: the initialization (once per entry), the condition checks (iterations + 1) "
                        "and the updates (iterations)."),
    "statements_not_operations": ("You counted statements rather than operations.",
                                  "Under the counting model, a line like `sum = sum + A[i]` costs 2 (one + and one =). "
                                  "Count every operator symbol."),
    "only_body": ("You counted only the innermost statement.",
                  "T(n) includes every row: statements outside the loops and all loop-control operations too."),
    "inner_once": ("You appear to have counted the inner loop only once in total.",
                   "The inner loop executes completely for every iteration of the outer loop, so its rows are "
                   "multiplied by the number of outer iterations."),
    "missing_loop_factor": ("Your T(n) grows too slowly - it looks like a loop's repetition is missing.",
                            "When a loop sits inside another loop, the inner loop's work is repeated for every outer "
                            "iteration: multiply the counts."),
    "extra_loop_factor": ("Your T(n) grows too fast.",
                          "Loops that run one after another are added, not multiplied. Only a loop INSIDE another loop "
                          "multiplies."),
    "merged_variables": ("You've combined independent input sizes.",
                         "n and m are separate sizes - an n-loop around an m-loop runs n·m times, not n². Keep each "
                         "variable as it appears in the loop bounds."),
    "missing_log": ("Your count is missing the logarithmic factor.",
                    "A loop that doubles (or halves) its variable reaches n after log₂ n iterations, so its rows "
                    "execute about log₂ n times, not n times."),
    "unexpected_log": ("Your count has a logarithm where the loop is linear.",
                       "A loop that adds a constant to its variable each time runs a linear number of times; only "
                       "multiplying/dividing gives log₂ n."),
    "summation": ("Your leading term is off by a factor of about 2.",
                  "The inner loop doesn't run n times on every outer iteration - its count grows with the outer "
                  "variable. Add the counts: 1 + 2 + … + n = n(n + 1)/2, which has leading term n²/2."),
    "leading_coefficient": ("Your highest-order term has the wrong coefficient.",
                            "Check the cost of each statement inside the innermost loop (count every operator) and how "
                            "many times that loop's rows run."),
    "lower_terms": ("The highest-order term is right, but the lower-order terms differ.",
                    "Re-check the rows outside the innermost loop: loop initializations, the final failed condition "
                    "checks, and statements before/after the loops."),
    "constant_term": ("Everything is right except the constant.",
                      "Re-check the statements that run exactly once: initializations, the outer loop's init, and the "
                      "return."),
    "wrong": ("Your T(n) doesn't match the operation count.",
              "Work row by row: cost × executions, then add."),
}


def diagnose(student, expected, variants, topic, variables):
    """Return (category, headline, detail) explaining why `student` != `expected`."""
    for cat, expr in variants:
        if tnmath.equivalent(student, expr):
            return (cat,) + MISTAKE_MESSAGES[cat]
    vs = tuple(variables)
    for v in vs[1:]:
        if tnmath.has_var(expected, v) and not tnmath.has_var(student, v):
            return ("merged_variables",) + MISTAKE_MESSAGES["merged_variables"]
    ed, sd = tnmath.dominant(expected, vs), tnmath.dominant(student, vs)
    if ed != sd:
        e_log = any(l for s in ed for _, _, l in s.parts)
        s_log = any(l for s in sd for _, _, l in s.parts)
        if e_log and not s_log:
            return ("missing_log",) + MISTAKE_MESSAGES["missing_log"]
        if s_log and not e_log:
            return ("unexpected_log",) + MISTAKE_MESSAGES["unexpected_log"]
        e_deg = max((sum(p for _, p, _ in s.parts) for s in ed), default=0)
        s_deg = max((sum(p for _, p, _ in s.parts) for s in sd), default=0)
        if s_deg < e_deg:
            if topic in ("tn_nested", "tn_dependent", "tn_multi", "tn_algorithms"):
                return ("inner_once",) + MISTAKE_MESSAGES["inner_once"]
            return ("missing_loop_factor",) + MISTAKE_MESSAGES["missing_loop_factor"]
        if s_deg > e_deg:
            return ("extra_loop_factor",) + MISTAKE_MESSAGES["extra_loop_factor"]
        return ("wrong",) + MISTAKE_MESSAGES["wrong"]
    el, sl = tnmath.leading_coefficients(expected, vs), tnmath.leading_coefficients(student, vs)
    if any(el[s] != sl.get(s) for s in el):
        ratios = {sp.nsimplify(sl[s] / el[s]) for s in el if el[s] and sl.get(s)}
        if topic in ("tn_dependent",) and ratios & {2, sp.Rational(1, 2)}:
            return ("summation",) + MISTAKE_MESSAGES["summation"]
        return ("leading_coefficient",) + MISTAKE_MESSAGES["leading_coefficient"]
    diff = sp.expand(student - expected)
    if diff.is_number:
        return ("constant_term",) + MISTAKE_MESSAGES["constant_term"]
    return ("lower_terms",) + MISTAKE_MESSAGES["lower_terms"]


def check_T(text, ex, case):
    """Grade one T(n) answer. Returns a dict with correct, category, messages, normalized text."""
    sol = ex["solution"][case]
    expected = tnmath.sympify_trusted(sol["T"])
    try:
        parsed = tnmath.parse(text or "", tuple(ex["vars"]), allow_wrapper=True)
    except ParseError as e:
        return {"correct": False, "category": "syntax", "headline": "That expression couldn't be read.",
                "detail": str(e), "given": text or ""}
    if parsed.wrapper:
        head, detail = MISTAKE_MESSAGES["asymptotic_only"]
        return {"correct": False, "category": "asymptotic_only", "headline": head, "detail": detail,
                "given": text, "given_text": f"{'Θ' if parsed.wrapper == 'theta' else parsed.wrapper}({tnmath.pretty(parsed.expr)})"}
    if tnmath.equivalent(parsed.expr, expected):
        note = None if tnmath.is_simplified(parsed) else f"Correct. Simplified, it is {tnmath.pretty(expected)}."
        return {"correct": True, "given": text, "given_text": tnmath.pretty(parsed.expr), "note": note}
    variants = [(c, tnmath.sympify_trusted(e)) for c, e in sol["variants"]]
    cat, head, detail = diagnose(parsed.expr, expected, variants, ex["topic"], ex["vars"])
    if tnmath.dominant(parsed.expr, tuple(ex["vars"])) == tnmath.dominant(expected, tuple(ex["vars"])):
        head = head + " (Your asymptotic growth is right, though.)"
    return {"correct": False, "category": cat, "headline": head, "detail": detail, "given": text,
            "given_text": tnmath.pretty(parsed.expr)}


def check_theta(text, ex, case):
    sol = ex["solution"][case]
    expected = tnmath.sympify_trusted(sol["T"])
    raw = (text or "").strip()
    try:
        parsed = tnmath.parse(raw, tuple(ex["vars"]), allow_wrapper=True)
    except ParseError as e:
        return {"correct": False, "category": "syntax", "headline": "That couldn't be read.", "detail": str(e), "given": raw}
    vs = tuple(ex["vars"])
    if parsed.wrapper in ("O", "omega"):
        sym = "O" if parsed.wrapper == "O" else "Ω"
        return {"correct": False, "category": "wrong_notation", "given": raw,
                "headline": f"This box asks for the tight bound Θ, not {sym}.",
                "detail": f"{sym} is only an upper/lower bound. Θ means both at once: here Θ({sol['theta']})."}
    same = tnmath.dominant(parsed.expr, vs) == tnmath.dominant(expected, vs)
    if same:
        note = None
        if len(sp.Add.make_args(parsed.expr)) > len(tnmath.dominant(expected, vs)) or any(
                abs(c) != 1 for c in tnmath.leading_coefficients(parsed.expr, vs).values()):
            note = f"Correct, but usually written without constants or lower-order terms: Θ({sol['theta']})."
        return {"correct": True, "given": raw, "given_text": f"Θ({tnmath.theta_text(parsed.expr, vs)})", "note": note}
    return {"correct": False, "category": "theta", "given": raw,
            "headline": "That isn't the tight bound.",
            "detail": f"Keep only the fastest-growing term of {ex['fn'][case]} and drop its constant: the dominant term is "
                      f"{sol['dominant']}."}


def check_cell(value, ex, case, key, column):
    row = next(r for r in ex["rows"] if r["key"] == key)
    expected = sp.Integer(row["cost"]) if column == "cost" else tnmath.sympify_trusted(
        next(t for t in ex["solution"][case]["table"] if t["key"] == key)["exec"])
    try:
        got = tnmath.parse(value or "", tuple(ex["vars"])).expr
    except ParseError as e:
        return {"correct": False, "error": str(e)}
    return {"correct": bool(tnmath.equivalent(got, expected)), "expected": tnmath.pretty(expected)}


def check_step(ex, step_id, value, reveal=False):
    """Check one guided step. The expected value is only returned when the step is right or the
    student explicitly asks to see it, so the guided mode can't be used for guessing."""
    step = next((s for s in ex["guided"] if s["id"] == step_id), None)
    if step is None:
        raise KeyError(step_id)
    expected = tnmath.sympify_trusted(step["answer"])
    vs = tuple(ex["vars"])
    shown = f"Θ({tnmath.theta_text(expected, vs)})" if step.get("theta") else tnmath.pretty(expected)
    if reveal:
        return {"correct": False, "revealed": True, "expected": shown, "explain": step["explain"]}
    res = _check_step_value(step, expected, value, vs)
    if res.get("correct"):
        res.update(expected=shown, explain=step["explain"])
    return res


def _check_step_value(step, expected, value, vs):
    allowed = tuple(dict.fromkeys(step.get("allowed", vs)))
    try:
        parsed = tnmath.parse(value or "", allowed, allow_wrapper=True)
    except ParseError as e:
        return {"correct": False, "error": str(e)}
    if step.get("theta"):
        if parsed.wrapper in ("O", "omega"):
            return {"correct": False, "error": "Give the tight bound Θ here, not an O or Ω bound."}
        return {"correct": tnmath.dominant(parsed.expr, vs) == tnmath.dominant(expected, vs)}
    if parsed.wrapper:
        return {"correct": False, "error": "Write the count itself here, not an O/Θ/Ω bound."}
    ok = tnmath.equivalent(parsed.expr, expected)
    if ok and step.get("simplify") and not tnmath.is_simplified(parsed):
        return {"correct": False, "error": "That's equal, but not simplified: collect like terms into one term per power."}
    return {"correct": ok}


def grade(ex, answer):
    """Grade a T(n) submission. Parts graded independently: table cells, T per case, Θ per case."""
    answer = answer if isinstance(answer, dict) else {}
    mode = answer.get("mode") if answer.get("mode") in ("table", "direct", "guided") else "direct"
    T_in = answer.get("T") if isinstance(answer.get("T"), dict) else {}
    th_in = answer.get("theta") if isinstance(answer.get("theta"), dict) else {}
    cells_in = answer.get("cells") if isinstance(answer.get("cells"), dict) else {}
    res = {"mode": mode, "T": {}, "theta": {}, "cells": {}}
    for case in ex["cases"]:
        res["T"][case] = check_T(str(T_in.get(case, ""))[:400], ex, case)
        res["theta"][case] = check_theta(str(th_in.get(case, ""))[:400], ex, case)
    table_case = "worst" if "worst" in ex["cases"] else ex["cases"][0]
    if mode == "table":
        blank = ex.get("table_blank", "exec")
        for row in ex["rows"]:
            cell = cells_in.get(row["key"]) if isinstance(cells_in.get(row["key"]), dict) else {}
            for col in (("cost", "exec") if blank == "both" else (blank,)):
                r = check_cell(str(cell.get(col, ""))[:200], ex, table_case, row["key"], col)
                res["cells"].setdefault(row["key"], {})[col] = r
    t_ok = all(r["correct"] for r in res["T"].values())
    th_ok = all(r["correct"] for r in res["theta"].values())
    cells_ok = all(c["correct"] for cols in res["cells"].values() for c in cols.values())
    res["t_correct"], res["theta_correct"], res["cells_correct"] = t_ok, th_ok, cells_ok
    res["correct"] = t_ok and th_ok and cells_ok
    if not res["correct"]:                       # don't hand out the counts before the student has them
        for cols in res["cells"].values():
            for c in cols.values():
                c.pop("expected", None)
    first_wrong = next((r for r in res["T"].values() if not r["correct"]), None)
    res["category"] = first_wrong["category"] if first_wrong else ("theta" if not th_ok else ("table" if not cells_ok else None))
    res["answer_text"] = "; ".join(
        f"{ex['fn'][c]} = {res['T'][c].get('given_text') or res['T'][c].get('given') or '(blank)'}, "
        f"Θ: {res['theta'][c].get('given') or '(blank)'}" for c in ex["cases"])
    res["correct_text"] = correct_text(ex)
    return res


def correct_text(ex):
    return "; ".join(f"{ex['fn'][c]} = {ex['solution'][c]['T_text']}, Θ({ex['solution'][c]['theta']})" for c in ex["cases"])


def explanation_text(ex):
    lines = []
    for c in ex["cases"]:
        s = ex["solution"][c]
        if c != "all":
            lines.append(f"[{c} case] {ex['case_notes'].get(c, '')}".rstrip())
        for t in s["table"]:
            lines.append(f"  line {t['line']}: {t['text']:<28} cost {t['cost']} × {t['exec']} = {t['total']}")
        lines.append(f"  {ex['fn'][c]} = {s['sum']}")
        lines.append(f"  {ex['fn'][c]} = {s['T_text']}  →  dominant term {s['dominant']}  →  Θ({s['theta']})")
    return "\n".join(lines)


def public_view(ex):
    """Everything the page needs before an answer - no counts, totals, T(n) or Θ."""
    blank = ex.get("table_blank", "exec")
    rows = []
    for r in ex["rows"]:
        rows.append({"key": r["key"], "line": r["line"], "text": r["text"], "role": r["role"],
                     "cost": None if blank in ("cost", "both") else r["cost"]})
    steps = [{"id": s["id"], "q": s["q"], "allowed": s.get("allowed", ex["vars"]),
              "kind": "bound" if s.get("theta") else ("simplify" if s.get("simplify") else "count")} for s in ex["guided"]]
    return {"code": ex["code"], "vars": ex["vars"], "assumptions": ex["assumptions"], "cases": ex["cases"],
            "fn": ex["fn"], "rows": rows, "table_blank": blank, "mode": ex["mode"], "guided": steps,
            "table_case": "worst" if "worst" in ex["cases"] else ex["cases"][0], "model": MODEL_RULES}


def solution_payload(ex):
    return {"cases": {c: {k: v for k, v in ex["solution"][c].items() if k != "variants"} for c in ex["cases"]},
            "fn": ex["fn"], "note": ex.get("note"), "case_notes": ex.get("case_notes", {}),
            "steps": explanation_text(ex).split("\n"), "code": ex["code"]}


def category_label(cat):
    """Short human label for a stored mistake category (None if not a T(n) category)."""
    if not cat:
        return None
    extra = {"syntax": "Expression could not be parsed", "theta": "Wrong asymptotic class (Θ)",
             "wrong_notation": "Used O or Ω instead of Θ", "table": "Operation-table cell wrong",
             "wrong_count": "Operation count wrong"}
    if cat in extra:
        return extra[cat]
    if cat in MISTAKE_MESSAGES:
        return MISTAKE_MESSAGES[cat][0].rstrip(".")
    return cat.replace("_", " ").capitalize()
