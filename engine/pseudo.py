"""
A forgiving pseudocode interpreter.

Pseudocode is translated line-by-line into a restricted Python program and then
executed in a sandbox with a step limit and recursion limit.  It exists so the
Pseudocode Lab can *test* what a student writes instead of demanding one exact
textual answer.

Supported convention (plus many common variants):

    procedure Name(a, b)            function / algorithm / def also work
        x = 0                       also  x <- 0, x ← 0, x := 0, set x to 0
        for i = 0 to n - 1          inclusive bounds; also "downto", "step 2"
        for each x in A             also "for x in A"
        while cond                  trailing "do", "then", ":" are ignored
        if cond / else if / else    "end if", "end for", "}" lines are ignored
        return value
        x++, x += 2, increment x
        swap(A[i], A[j])            also "swap A[i] and A[j]"
        append(L, x)                also "append x to L"
        print x
    Operators: and or not mod div, =/== in conditions, ≠ ≤ ≥ <> ^ (power)
    Functions: length(A) / A.length, floor, ceil, sqrt, abs, min, max
    Arrays are 0-indexed and bounds-checked; new array[n] creates zeros.

Blocks are defined by indentation.
"""
from __future__ import annotations

import copy
import math
import re
import sys
import threading

STEP_LIMIT = 300_000
DEPTH_LIMIT = 300
FILENAME = "<pseudo>"


class PseudoError(Exception):
    def __init__(self, msg, line=None):
        self.msg = msg
        self.line = line
        super().__init__(f"Line {line}: {msg}" if line else msg)


# --------------------------------------------------------------------------
# Runtime helpers
# --------------------------------------------------------------------------
class PList(list):
    """0-indexed list that refuses negative / out-of-range indices."""

    def _idx(self, i):
        if isinstance(i, bool):
            raise PseudoError("an array index must be a number, not true/false")
        if isinstance(i, float):
            if math.isnan(i) or math.isinf(i):
                raise PseudoError("an array index must be a finite number")
            i = math.floor(i)
        if not isinstance(i, int):
            raise PseudoError(f"an array index must be an integer, got {fmt(i)}")
        if i < 0 or i >= len(self):
            if len(self) == 0:
                raise PseudoError(f"index {i} is out of bounds (the array is empty)")
            raise PseudoError(f"index {i} is out of bounds (valid indices are 0..{len(self) - 1})")
        return i

    def __getitem__(self, i):
        if isinstance(i, slice):
            return PList(list.__getitem__(self, i))
        return list.__getitem__(self, self._idx(i))

    def __setitem__(self, i, v):
        if isinstance(i, slice):
            return list.__setitem__(self, i, v)
        list.__setitem__(self, self._idx(i), v)

    def __add__(self, other):
        return PList(list(self) + list(other))


def to_plist(v):
    if isinstance(v, (list, tuple)):
        return PList(to_plist(x) for x in v)
    return v


def normalize(v):
    """Convert runtime values into plain JSON-friendly values."""
    if isinstance(v, (list, tuple)):
        return [normalize(x) for x in v]
    if isinstance(v, float):
        if math.isinf(v):
            return "∞" if v > 0 else "-∞"
        if abs(v - round(v)) < 1e-9:
            return int(round(v))
        return round(v, 6)
    return v


def fmt(v):
    v = normalize(v)
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, list):
        return "[" + ", ".join(fmt(x) for x in v) + "]"
    return str(v)


def values_equal(a, b):
    a, b = normalize(a), normalize(b)
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-6
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(values_equal(x, y) for x, y in zip(a, b))
    return a == b


def _rng(a, b, step=1, down=False):
    if step == 0:
        raise PseudoError("loop step cannot be 0")
    if down:
        step = -abs(step)
        start, stop = math.floor(a), math.ceil(b)
        return range(int(start), int(stop) - 1, int(step)) if float(step).is_integer() else _frange(a, b, step)
    start, stop = math.ceil(a), math.floor(b)
    if float(step).is_integer() and step > 0:
        return range(int(start), int(stop) + 1, int(step))
    return _frange(a, b, step)


def _frange(a, b, step):
    x = a
    out = []
    while (x <= b + 1e-12) if step > 0 else (x >= b - 1e-12):
        out.append(x)
        x += step
        if len(out) > STEP_LIMIT:
            raise PseudoError("loop runs too many times")
    return out


def _array(n, fill=0):
    n = normalize(n)
    if not isinstance(n, int) or n < 0:
        raise PseudoError(f"array size must be a non-negative integer, got {fmt(n)}")
    return PList([fill] * n)


def _L(v):
    return to_plist(v) if isinstance(v, list) else v


def _append(lst, x):
    if not isinstance(lst, list):
        raise PseudoError("append needs a list")
    list.append(lst, x)


def _length(x):
    return len(x)


def _floor(x):
    return math.floor(x)


def _ceil(x):
    return math.ceil(x)


def _sqrt(x):
    return math.sqrt(x)


def _swap_check(*a):
    return a


SAFE_ENV = {
    "length": _length, "len": _length, "size": _length,
    "floor": _floor, "ceil": _ceil, "ceiling": _ceil, "sqrt": _sqrt,
    "abs": abs, "min": min, "max": max, "round": round, "int": int,
    "append": _append, "range": range, "list": lambda *a: PList(list(*a)),
    "log2": math.log2, "log": math.log, "log10": math.log10,
    "sum": sum, "sorted": lambda a: PList(sorted(a)),
    "True": True, "False": False, "None": None,
    "_rng": _rng, "_array": _array, "_L": _L, "_append": _append,
    "_INF": math.inf, "_fmt": fmt,
}


# --------------------------------------------------------------------------
# Transpiler
# --------------------------------------------------------------------------
LHS = r"[A-Za-z_]\w*(?:\s*\[.*?\])*"
ASSIGN_OPS = r"(?:=|←|<-|:=)"

WORD_MAP = {
    "and": " and ", "or": " or ", "not": " not ", "mod": " % ", "div": " // ",
    "true": " True ", "false": " False ", "null": " None ", "nil": " None ",
    "none": " None ", "infinity": " _INF ", "inf": " _INF ",
}
WORD_RE = re.compile(r"\b(" + "|".join(WORD_MAP) + r")\b", re.I)
FORBIDDEN = re.compile(r"__|\bimport\b|\blambda\b|\bexec\b|\beval\b|\bglobals\b|\blocals\b|\bgetattr\b|\bsetattr\b|\bopen\b|\bclass\b|\byield\b|\bwith\b|\bdel\b|\bglobal\b|\bnonlocal\b|\btry\b|\braise\b|\bassert\b")


def conv_expr(s: str, line: int) -> str:
    s = s.strip()
    if not s:
        return s
    pieces = re.split(r"(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')", s)
    out = []
    for k, p in enumerate(pieces):
        if k % 2 == 1:
            # no string prefixes (f"", r"", b"") - f-strings would evaluate arbitrary expressions
            if re.search(r"[A-Za-z0-9_]$", pieces[k - 1]):
                raise PseudoError("string prefixes like f\"...\" are not allowed", line)
            out.append(p)
            continue
        if re.search(r"(?<![\w.])_[A-Za-z_]", p):
            raise PseudoError("names may not start with an underscore", line)
        conv = _conv_code(p, line)
        # attribute access (x.something) is never needed after conversion and is the classic
        # sandbox-escape route (e.g. "...".format(...) or obj.attr chains), so it is rejected
        if re.search(r"\.\s*[A-Za-z_]", conv):
            raise PseudoError("attribute access (x.name) isn't supported - use functions like length(A)", line)
        out.append(conv)
    res = "".join(out).strip()
    if FORBIDDEN.search(res):
        raise PseudoError("that construct is not allowed in pseudocode here", line)
    return res


def _conv_code(p: str, line: int) -> str:
    for a, b in (("≤", "<="), ("≥", ">="), ("≠", "!="), ("×", "*"), ("÷", "/"), ("−", "-"),
                 ("⌊", " floor("), ("⌋", ")"), ("⌈", " ceil("), ("⌉", ")"), ("∞", " _INF "),
                 ("&&", " and "), ("||", " or "), ("<>", "!="), ("^", "**"), ("·", "*")):
        p = p.replace(a, b)
    # A.length / A.size / A.length()  ->  len(A)
    p = re.sub(r"([A-Za-z_]\w*(?:\[[^\[\]]*\])*)\.(length|size|count)\b(\(\))?", r"len(\1)", p)
    # A.append(x) -> _append(A, x)
    p = re.sub(r"([A-Za-z_]\w*)\.(append|add|push)\(", r"_append(\1, ", p)
    # ! (not followed by =) -> not
    p = re.sub(r"!(?!=)", " not ", p)
    # single = -> ==
    p = re.sub(r"(?<![<>=!+\-*/%])=(?!=)", "==", p)
    p = WORD_RE.sub(lambda m: WORD_MAP[m.group(1).lower()], p)
    # new array[n], array of size n
    p = re.sub(r"\bnew\s+(?:array|list)\s*\[([^\]]+)\]", r"_array(\1)", p, flags=re.I)
    p = re.sub(r"\b(?:new\s+)?(?:array|list)\s+of\s+(?:size|length)\s+(.+)$", r"_array(\1)", p, flags=re.I)
    p = re.sub(r"\bnew\s+(?:array|list)\s*\(", "_array(", p, flags=re.I)
    p = re.sub(r"\b(?:empty\s+(?:array|list))\b", "_L([])", p, flags=re.I)
    return p


def conv_lhs(s: str, line: int) -> str:
    s = s.strip()
    if not re.fullmatch(LHS, s):
        raise PseudoError(f"can't assign to '{s}'", line)
    return conv_expr(s, line).replace("==", "=")


def conv_rhs(s: str, line: int) -> str:
    e = conv_expr(s, line)
    if e.startswith("["):
        e = f"_L({e})"
    return e


END_RE = re.compile(
    r"^(end\b.*|endif|endfor|endwhile|endfunction|endprocedure|endproc|endfunc|fi|od|done|wend|loop|begin|\}|\{|next(\s+\w+)?)$",
    re.I)


def _strip_line(raw: str) -> str:
    s = re.sub(r"//.*$", "", raw)
    s = re.sub(r"(^|\s)#.*$", "", s)
    s = re.sub(r"▷.*$", "", s)
    s = s.rstrip()
    s = s.rstrip(";").rstrip()
    if s.endswith("{"):
        s = s[:-1].rstrip()
    return s


def _strip_suffix(stmt: str) -> str:
    s = re.sub(r"\s+(then|do|begin)$", "", stmt, flags=re.I)
    if s.endswith(":"):
        s = s[:-1].rstrip()
    return s


def translate_stmt(stmt: str, line: int):
    """Return (python_text, opens_block, kind)."""
    s = _strip_suffix(stmt.strip())
    low = s.lower()

    m = re.match(r"^(?:procedure|function|algorithm|def|proc|func|method|subroutine)\s+([A-Za-z_]\w*)\s*(?:\((.*?)\))?\s*(?:(?:->|returns?\b|:).*)?$", s, re.I)
    if m:
        params = []
        if m.group(2) and m.group(2).strip():
            for part in m.group(2).split(","):
                part = part.strip()
                part = re.sub(r":.*$", "", part).strip()          # strip ": type"
                ids = re.findall(r"[A-Za-z_]\w*", part)
                if not ids:
                    raise PseudoError(f"can't read parameter '{part}'", line)
                params.append(ids[-1] if len(ids) > 1 and ids[0].lower() in ("int", "array", "integer", "list", "real", "float", "string", "bool", "boolean") else ids[0])
        if FORBIDDEN.search(m.group(1)):
            raise PseudoError("invalid procedure name", line)
        return f"def {m.group(1)}({', '.join(params)}):", True, "def"

    m = re.match(r"^(?:else\s*if|elseif|elsif|elif|else,\s*if)\s+(.+)$", s, re.I)
    if m:
        return f"elif {conv_expr(m.group(1), line)}:", True, "elif"
    if low in ("else", "otherwise"):
        return "else:", True, "else"
    m = re.match(r"^if\s+(.+)$", s, re.I)
    if m:
        return f"if {conv_expr(m.group(1), line)}:", True, "if"

    m = re.match(r"^for\s+([A-Za-z_]\w*)\s*(?:=|←|<-|:=|\bfrom\b)\s*(.+?)\s+(to|downto|down\s+to)\s+(.+?)(?:\s+(?:step|by)\s+(.+))?$", s, re.I)
    if m:
        var, a, direction, b, step = m.groups()
        down = direction.lower().replace(" ", "") == "downto"
        if step:
            st = conv_expr(step, line)
            if st.strip().startswith("-"):
                down = True
                st = st.strip()[1:]
        else:
            st = "1"
        return f"for {var} in _rng({conv_expr(a, line)}, {conv_expr(b, line)}, {st}, {down}):", True, "for"
    m = re.match(r"^for\s+(?:each\s+|every\s+|all\s+)?([A-Za-z_]\w*)\s+in\s+(.+)$", s, re.I)
    if m:
        return f"for {m.group(1)} in list({conv_expr(m.group(2), line)}):", True, "for"
    m = re.match(r"^while\s+(.+)$", s, re.I)
    if m:
        return f"while {conv_expr(m.group(1), line)}:", True, "while"
    if low in ("repeat", "do", "loop forever", "while true"):
        raise PseudoError("repeat/until loops aren't supported here; use a while loop", line)

    m = re.match(r"^return\b\s*(.*)$", s, re.I)
    if m:
        e = m.group(1).strip()
        return (f"return {conv_rhs(e, line)}" if e else "return None"), False, "return"
    if low in ("break", "continue"):
        return low, False, low
    if low in ("pass", "skip", "do nothing", "nothing"):
        return "pass", False, "pass"

    m = re.match(r"^(?:print|output|display|write|println|printf|say)\b\s*(.*)$", s, re.I)
    if m:
        arg = m.group(1).strip()
        return f"_print({conv_expr(arg, line)})", False, "print"

    m = re.match(r"^(?:swap|exchange)\s*\(?\s*(" + LHS + r")\s*(?:,|\band\b|\bwith\b)\s*(" + LHS + r")\s*\)?$", s, re.I)
    if m:
        a, b = conv_lhs(m.group(1), line), conv_lhs(m.group(2), line)
        return f"{a}, {b} = {b}, {a}", False, "assign"

    m = re.match(r"^(" + LHS + r")\s*(\+\+|--)$", s) or re.match(r"^(\+\+|--)\s*(" + LHS + r")$", s)
    if m:
        g = m.groups()
        var, op = (g[0], g[1]) if g[1] in ("++", "--") else (g[1], g[0])
        return f"{conv_lhs(var, line)} {'+=' if op == '++' else '-='} 1", False, "assign"

    m = re.match(r"^(increment|increase|decrement|decrease)\s+(" + LHS + r")(?:\s+by\s+(.+))?$", s, re.I)
    if m:
        op = "+=" if m.group(1).lower().startswith("inc") else "-="
        amt = conv_expr(m.group(3), line) if m.group(3) else "1"
        return f"{conv_lhs(m.group(2), line)} {op} {amt}", False, "assign"

    m = re.match(r"^set\s+(" + LHS + r")\s+(?:to|=|←|:=)\s+(.+)$", s, re.I)
    if m:
        return f"{conv_lhs(m.group(1), line)} = {conv_rhs(m.group(2), line)}", False, "assign"

    m = re.match(r"^(?:append|add|push)\s+(.+?)\s+(?:to|onto|into)\s+(" + LHS + r")$", s, re.I)
    if m:
        return f"_append({conv_expr(m.group(2), line)}, {conv_expr(m.group(1), line)})", False, "call"

    m = re.match(r"^(" + LHS + r")\s*(\+=|-=|\*=|/=|%=)\s*(.+)$", s)
    if m:
        return f"{conv_lhs(m.group(1), line)} {m.group(2)} {conv_expr(m.group(3), line)}", False, "assign"

    m = re.match(r"^(" + LHS + r"(?:\s*,\s*" + LHS + r")*)\s*" + ASSIGN_OPS + r"\s*(.+)$", s)
    if m:
        targets = [conv_lhs(t, line) for t in _split_top(m.group(1))]
        rhs_parts = _split_top(m.group(2))
        if len(targets) > 1 and len(rhs_parts) == len(targets):
            rhs = ", ".join(conv_rhs(r, line) for r in rhs_parts)
        else:
            rhs = conv_rhs(m.group(2), line)
        return f"{', '.join(targets)} = {rhs}", False, "assign"

    m = re.match(r"^(?:call\s+)?([A-Za-z_][\w\.]*\s*\(.*\))$", s, re.I)
    if m:
        return conv_expr(m.group(1), line), False, "call"

    raise PseudoError(f"I couldn't understand this statement: \"{stmt.strip()}\"", line)


def _split_top(s):
    """Split on commas not inside brackets/parens."""
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts]


class Transpiled:
    def __init__(self, py, line_map, defs):
        self.py = py
        self.line_map = line_map
        self.defs = defs


def transpile(src: str, params=None, snap_header=None, snap_after=None) -> Transpiled:
    """Translate pseudocode into Python.

    params: if the code has no procedure header, it is wrapped into
            def _main(*params).
    snap_header: original line number of a loop header; a _snap() call is
            inserted at the end of that loop's body (one snapshot per iteration).
    """
    raw_lines = src.replace("\t", "    ").split("\n")
    stmts = []  # (orig_line, indent_width, text)
    for i, raw in enumerate(raw_lines, start=1):
        s = _strip_line(raw)
        if not s.strip():
            continue
        text = s.strip()
        if END_RE.match(text):
            continue
        # "} else {" style
        text = re.sub(r"^\}\s*", "", text)
        if not text:
            continue
        indent = len(s) - len(s.lstrip(" "))
        stmts.append((i, indent, text))

    if not stmts:
        raise PseudoError("the code is empty")

    out_lines = []
    line_map = {}
    defs = []
    stack = [0]          # indentation widths
    snap_level = None    # python level where the snap goes
    pending_snap = False
    prev_opens = False
    prev_line = None

    translated = []
    for (ln, ind, text) in stmts:
        py, opens, kind = translate_stmt(text, ln)
        translated.append((ln, ind, py, opens, kind))

    has_def = any(k == "def" for (_, _, _, _, k) in translated)
    wrap = (not has_def) and params is not None
    base = 1 if wrap else 0
    if wrap:
        defs.append("_main")
        out_lines.append(f"def _main({', '.join(params)}):")
        line_map[1] = translated[0][0]

    def emit(level, text, ln):
        out_lines.append("    " * (level + base) + text)
        line_map[len(out_lines)] = ln

    for idx, (ln, ind, py, opens, kind) in enumerate(translated):
        # figure out the logical level
        if prev_opens:
            if ind <= stack[-1]:
                raise PseudoError(f"the line after line {prev_line} should be indented (its body is missing)", ln)
            stack.append(ind)
        else:
            if ind > stack[-1]:
                raise PseudoError("unexpected indentation (this line is indented but the line above doesn't start a block)", ln)
            while ind < stack[-1]:
                stack.pop()
                level_closed = len(stack) - 1
                if pending_snap and snap_level is not None and level_closed < snap_level:
                    emit(snap_level, "_snap()", ln)
                    pending_snap = False
                    snap_level = None
            if ind != stack[-1]:
                raise PseudoError("indentation doesn't line up with any earlier line", ln)
        level = len(stack) - 1
        emit(level, py, ln)
        if snap_header is not None and ln == snap_header:
            if not opens:
                raise PseudoError("snapshot line is not a loop header", ln)
            pending_snap = True
            snap_level = level + 1
        if snap_after is not None and ln == snap_after:
            if opens:
                raise PseudoError("snapshot line must be a simple statement", ln)
            emit(level, "_snap()", ln)
        if kind == "def":
            defs.append(re.match(r"def (\w+)", py).group(1))
        prev_opens = opens
        prev_line = ln

    if prev_opens:
        raise PseudoError(f"line {prev_line} starts a block but nothing is inside it", prev_line)
    if pending_snap:
        emit(snap_level, "_snap()", translated[-1][0])

    return Transpiled("\n".join(out_lines) + "\n", line_map, defs)


# --------------------------------------------------------------------------
# Execution
# --------------------------------------------------------------------------
class _State(threading.local):
    steps = 0
    depth = 0
    limit = STEP_LIMIT


_state = _State()


def _local_tracer(frame, event, arg):
    if event == "line":
        _state.steps += 1
        if _state.steps > _state.limit:
            raise PseudoError("step limit exceeded - the code may contain an infinite loop")
    elif event == "return":
        _state.depth -= 1
    return _local_tracer


def _global_tracer(frame, event, arg):
    if frame.f_code.co_filename != FILENAME:
        return None
    if event == "call":
        _state.depth += 1
        if _state.depth > DEPTH_LIMIT:
            raise PseudoError("recursion is too deep - check that the base case is reached")
    return _local_tracer


def _error_line(exc, line_map):
    tb = exc.__traceback__
    line = None
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == FILENAME:
            line = line_map.get(tb.tb_lineno, line)
        tb = tb.tb_next
    return line


def _friendly(exc):
    if isinstance(exc, PseudoError):
        return exc.msg
    if isinstance(exc, NameError):
        m = re.search(r"name '(\w+)'", str(exc))
        name = m.group(1) if m else "a name"
        return f"'{name}' is used before it has a value (is it misspelled or never initialized?)"
    if isinstance(exc, ZeroDivisionError):
        return "division by zero"
    if isinstance(exc, RecursionError):
        return "recursion is too deep - check that the base case is reached"
    if isinstance(exc, IndexError):
        return "array index out of bounds"
    if isinstance(exc, TypeError):
        msg = str(exc)
        if "not callable" in msg:
            return "something that isn't a procedure is being called like one"
        if "positional argument" in msg:
            return "a procedure is called with the wrong number of arguments"
        return "type error: " + msg
    return f"{type(exc).__name__}: {exc}"


class Program:
    def __init__(self, src, params=None, snap_header=None, watch=None, snap_after=None):
        self.src = src
        self.tr = transpile(src, params=params, snap_header=snap_header, snap_after=snap_after)
        self.watch = watch or []
        self.output = []
        self.snaps = []
        env = dict(SAFE_ENV)
        env["_print"] = self._print
        env["_snap"] = self._snap
        env["__builtins__"] = {}
        self.env = env
        try:
            code = compile(self.tr.py, FILENAME, "exec")
        except SyntaxError as e:
            line = self.tr.line_map.get(e.lineno)
            raise PseudoError("this line couldn't be parsed" + (f" ({e.msg})" if e.msg else ""), line)
        self._run_guarded(lambda: exec(code, env))
        self.functions = [d for d in dict.fromkeys(self.tr.defs) if callable(env.get(d))]

    def _print(self, *args):
        self.output.append(" ".join(fmt(a) for a in args))

    def _snap(self):
        f = sys._getframe(1)
        row = {}
        for w in self.watch:
            row[w] = normalize(copy.deepcopy(f.f_locals.get(w, None)))
        self.snaps.append(row)

    def _run_guarded(self, fn):
        _state.steps = 0
        _state.depth = 0
        old = sys.gettrace()
        sys.settrace(_global_tracer)
        try:
            return fn()
        except PseudoError as e:
            if e.line is None:
                e.line = _error_line(e, self.tr.line_map)
                e.args = (f"Line {e.line}: {e.msg}" if e.line else e.msg,)
            raise
        except Exception as e:  # noqa: BLE001
            raise PseudoError(_friendly(e), _error_line(e, self.tr.line_map)) from None
        finally:
            sys.settrace(old)

    def find_entry(self, name=None, arity=None):
        if not self.functions:
            raise PseudoError("no procedure was defined")
        if "_main" in self.functions:
            return "_main"
        norm = lambda s: re.sub(r"[_\s]", "", s.lower())
        if name:
            for f in self.functions:
                if norm(f) == norm(name):
                    return f
        if len(self.functions) == 1:
            return self.functions[0]
        if arity is not None:
            for f in self.functions:
                if self.env[f].__code__.co_argcount == arity:
                    return f
        return self.functions[0]

    def call(self, fname, args):
        fn = self.env[fname]
        want = fn.__code__.co_argcount
        if want != len(args):
            raise PseudoError(f"procedure {fname} takes {want} parameter(s) but the exercise passes {len(args)}")
        return self._run_guarded(lambda: fn(*args))


def run_tests(src, tests, entry=None, params=None):
    """Run test cases against student code.

    Each test: {"args": [...], "expect": value, "check": "return" | "arg0" | "either"}
    Returns dict with runnable, error, passed, total, results.
    """
    try:
        prog = Program(src, params=params)
        fname = prog.find_entry(entry, arity=len(params) if params else None)
    except PseudoError as e:
        return {"runnable": False, "error": str(e), "error_line": e.line, "passed": 0, "total": len(tests), "results": []}
    results = []
    passed = 0
    for t in tests:
        args = [to_plist(copy.deepcopy(a)) for a in t["args"]]
        check = t.get("check", "return")
        prog.output = []
        try:
            ret = prog.call(fname, args)
            if check == "arg0":
                got = args[0]
            elif check == "either":
                got = ret if ret is not None else args[0]
            else:
                got = ret
            ok = values_equal(got, t["expect"])
            res = {"input": _fmt_args(t, params), "expected": fmt(t["expect"]), "got": fmt(got), "ok": ok}
        except PseudoError as e:
            ok = False
            res = {"input": _fmt_args(t, params), "expected": fmt(t["expect"]), "got": "error", "error": str(e), "ok": False}
        passed += ok
        results.append(res)
    return {"runnable": True, "error": None, "passed": passed, "total": len(tests), "results": results, "entry": fname}


def _fmt_args(t, params):
    names = params or [f"arg{i + 1}" for i in range(len(t["args"]))]
    return ", ".join(f"{n} = {fmt(a)}" for n, a in zip(names, t["args"]))


def run_trace(src, inputs: dict, snap_header, watch: list, entry=None, snap_after=None):
    """Execute code and return snapshot rows.

    snap_header: loop header line -> one row at the end of every iteration.
    snap_after:  statement line   -> one row every time that statement runs.
    """
    params = list(inputs.keys())
    prog = Program(src, params=params, snap_header=snap_header, watch=watch, snap_after=snap_after)
    fname = prog.find_entry(entry, arity=len(params))
    args = [to_plist(copy.deepcopy(inputs[p])) for p in params]
    ret = prog.call(fname, args)
    return {"rows": prog.snaps, "result": normalize(ret), "output": prog.output}
