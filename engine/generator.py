"""
Deterministic challenge generator.

Questions are built from a small structural spec (loops, nesting, sequencing,
branches), and the answer is computed symbolically from that spec, never by
guessing. The same spec also drives an exact operation-count simulator that
the test-suite uses to confirm every generated answer empirically.

Supported building blocks (each with a proven iteration count):
    lin   for i = 1 to V            (optionally step s)     → V
    const for i = 1 to c                                     → 1
    mul   i = 1; while i < V: i = i * c                      → log V
    div   i = V; while i > 1: i = i / c                      → log V
    sqrt  i = 1; while i * i <= V: i = i + 1                 → √V
Dependent inner loops (only directly under a matching outer loop over V):
    dep_lin  for j = 1 to i        under lin  → V²      (Σ i)
             under mul             → V        (geometric series)
    dep_log  j = 1; while j < i: j = j * 2 under lin → V log V   (Σ log i = log V!)
    harm     j = 1; while j <= V: j = j + i under lin → V log V  (harmonic)
"""
from __future__ import annotations

import math
import random
from fractions import Fraction

FAMILIES = {
    "single": "Single loop (varied bounds and updates)",
    "sequential": "Sequential sections",
    "nested": "Nested loops",
    "multivar": "Multiple variables (n, m, k)",
    "dependent": "Dependent / irregular loops",
    "conditional": "Conditional branches (worst case)",
    "mixed": "Surprise me",
}

SUB = {2: "₂", 3: "₃", 4: "₄", 10: "₁₀"}
LOOP_VARS = ["i", "j", "t", "u"]


# ---------------------------------------------------------------------------- monomials
class Mono:
    """Product of var^exp · (log var)^lexp."""

    def __init__(self, terms=None):
        self.t = {}
        for v, (e, l) in (terms or {}).items():
            if e or l:
                self.t[v] = (Fraction(e), l)

    def __mul__(self, o):
        out = dict(self.t)
        for v, (e, l) in o.t.items():
            e0, l0 = out.get(v, (Fraction(0), 0))
            out[v] = (e0 + e, l0 + l)
        return Mono(out)

    def key(self):
        return tuple(sorted((v, e, l) for v, (e, l) in self.t.items()))

    def __eq__(self, o):
        return isinstance(o, Mono) and self.key() == o.key()

    def __hash__(self):
        return hash(self.key())

    def geq(self, o):
        """self grows at least as fast as o (assuming every variable ≥ 2)."""
        for v in set(self.t) | set(o.t):
            a = self.t.get(v, (Fraction(0), 0))
            b = o.t.get(v, (Fraction(0), 0))
            if a < b:
                return False
        return True

    def value(self, env):
        x = 1.0
        for v, (e, l) in self.t.items():
            x *= env[v] ** float(e) * (math.log2(env[v]) ** l)
        return x

    def label(self):
        if not self.t:
            return "1"
        order = [v for v in ("n", "m", "k") if v in self.t]
        poly, logs = "", []
        for v in order:
            e, l = self.t[v]
            if e == Fraction(1, 2):
                poly += "√" + v
            elif e == 1:
                poly += v
            elif e > 0:
                poly += v + {2: "²", 3: "³", 4: "⁴"}.get(int(e), f"^{e}")
            if l:
                logs.append(("log " if l == 1 else "log² ") + v)
        if poly and logs:
            return poly + " " + " ".join(logs)
        return poly or " ".join(logs)


def simplify_sum(monos):
    """Drop every term dominated by another term."""
    uniq = list(dict.fromkeys(monos))
    keep = []
    for a in uniq:
        if any(b != a and b.geq(a) for b in uniq):
            continue
        keep.append(a)
    return sorted(keep, key=lambda m: (-sum(float(e) for e, _ in m.t.values()), -sum(l for _, l in m.t.values()), m.label()))


def sum_label(monos):
    return " + ".join(m.label() for m in simplify_sum(monos))


# ---------------------------------------------------------------------------- loops
def loop_mono(lp):
    k, v = lp["kind"], lp.get("var")
    if k == "lin":
        return Mono({v: (1, 0)})
    if k == "const":
        return Mono()
    if k in ("mul", "div"):
        return Mono({v: (0, 1)})
    if k == "sqrt":
        return Mono({v: (Fraction(1, 2), 0)})
    raise ValueError(k)


def chain_cost(loops):
    """Total innermost-body executions of a nested chain, as a Mono."""
    m = Mono()
    i = 0
    while i < len(loops):
        lp = loops[i]
        nxt = loops[i + 1] if i + 1 < len(loops) else None
        if nxt and nxt["kind"] in ("dep_lin", "dep_log", "harm"):
            v = lp["var"]
            if lp["kind"] == "lin" and nxt["kind"] == "dep_lin":
                m = m * Mono({v: (2, 0)})
            elif lp["kind"] == "mul" and nxt["kind"] == "dep_lin":
                m = m * Mono({v: (1, 0)})
            elif lp["kind"] == "lin" and nxt["kind"] in ("dep_log", "harm"):
                m = m * Mono({v: (1, 1)})
            else:
                raise ValueError("unsupported dependent pair")
            i += 2
            continue
        m = m * loop_mono(lp)
        i += 1
    return m


def iter_label(lp, outer_name=None):
    k, v = lp["kind"], lp.get("var")
    if k == "lin":
        s = lp.get("step", 1)
        return f"{v} iterations" if s == 1 else f"≈ {v}/{s} iterations → linear"
    if k == "const":
        return f"{lp['c']} iterations (constant)"
    if k in ("mul", "div"):
        return f"≈ log{SUB.get(lp['c'], '')} {v} iterations"
    if k == "sqrt":
        return f"≈ √{v} iterations"
    if k == "dep_lin":
        return f"{outer_name} iterations (depends on {outer_name})"
    if k == "dep_log":
        return f"≈ log {outer_name} iterations"
    if k == "harm":
        return f"≈ {lp['var']}/{outer_name} iterations"
    return ""


# ---------------------------------------------------------------------------- rendering
OP = "count = count + 1"


def render_chain(loops, indent, names, lines, marks):
    """Append the pseudocode for a nested chain; marks collects (line_no, label)."""
    pad = "    " * indent
    if not loops:
        lines.append(pad + OP)
        return
    lp, rest = loops[0], loops[1:]
    name = names[0]
    outer = lp.get("_outer")
    k, v = lp["kind"], lp.get("var")
    post = None
    if k == "lin" and lp.get("step", 1) == 1:
        lines.append(f"{pad}for {name} = 1 to {v}")
    elif k == "lin":
        lines.append(f"{pad}{name} = 1")
        lines.append(f"{pad}while {name} <= {v}")
        post = f"{name} = {name} + {lp['step']}"
    elif k == "const":
        lines.append(f"{pad}for {name} = 1 to {lp['c']}")
    elif k == "mul":
        lines.append(f"{pad}{name} = 1")
        lines.append(f"{pad}while {name} < {v}")
        post = f"{name} = {name} * {lp['c']}"
    elif k == "div":
        lines.append(f"{pad}{name} = {v}")
        lines.append(f"{pad}while {name} > 1")
        post = f"{name} = {name} / {lp['c']}"
    elif k == "sqrt":
        lines.append(f"{pad}{name} = 1")
        lines.append(f"{pad}while {name} * {name} <= {v}")
        post = f"{name} = {name} + 1"
    elif k == "dep_lin":
        lines.append(f"{pad}for {name} = 1 to {outer}")
    elif k == "dep_log":
        lines.append(f"{pad}{name} = 1")
        lines.append(f"{pad}while {name} < {outer}")
        post = f"{name} = {name} * 2"
    elif k == "harm":
        lines.append(f"{pad}{name} = 1")
        lines.append(f"{pad}while {name} <= {v}")
        post = f"{name} = {name} + {outer}"
    marks.append((len(lines), iter_label(lp, outer)))
    if rest:
        rest = [dict(r) for r in rest]
        if rest[0]["kind"] in ("dep_lin", "dep_log", "harm"):
            rest[0]["_outer"] = name
    render_chain(rest, indent + 1, names[1:], lines, marks)
    if post:
        lines.append(pad + "    " + post)


# ---------------------------------------------------------------------------- random specs
def _rand_basic(rng, var, allow=("lin", "const", "mul", "div", "sqrt"), weights=None):
    kind = rng.choices(list(allow), weights=weights or [1] * len(allow))[0]
    lp = {"kind": kind, "var": var}
    if kind == "lin":
        lp["step"] = rng.choice([1, 1, 1, 2, 3])
    elif kind == "const":
        lp["c"] = rng.choice([5, 10, 50, 100])
    elif kind in ("mul", "div"):
        lp["c"] = rng.choice([2, 2, 3])
    return lp


def _dependent_chain(rng, var="n"):
    pat = rng.choice(["lin_dep_lin", "mul_dep_lin", "lin_dep_log", "lin_harm"])
    if pat == "lin_dep_lin":
        return [{"kind": "lin", "var": var, "step": 1}, {"kind": "dep_lin"}]
    if pat == "mul_dep_lin":
        return [{"kind": "mul", "var": var, "c": 2}, {"kind": "dep_lin"}]
    if pat == "lin_dep_log":
        return [{"kind": "lin", "var": var, "step": 1}, {"kind": "dep_log"}]
    return [{"kind": "lin", "var": var, "step": 1}, {"kind": "harm", "var": var}]


def build_spec(family, rng):
    if family == "mixed":
        family = rng.choice(["single", "sequential", "nested", "multivar", "dependent", "conditional"])
    blocks = []
    if family == "single":
        blocks.append({"loops": [_rand_basic(rng, "n", weights=[3, 1, 2, 2, 1])]})
    elif family == "nested":
        depth = rng.choice([2, 2, 3])
        loops = [_rand_basic(rng, "n", allow=("lin", "const", "mul", "div"), weights=[4, 1, 2, 1]) for _ in range(depth)]
        if all(lp["kind"] == "const" for lp in loops):
            loops[0] = {"kind": "lin", "var": "n", "step": 1}
        blocks.append({"loops": loops})
    elif family == "sequential":
        for _ in range(rng.choice([2, 2, 3])):
            depth = rng.choice([1, 1, 2])
            blocks.append({"loops": [_rand_basic(rng, "n", allow=("lin", "const", "mul"), weights=[4, 1, 2]) for _ in range(depth)]})
    elif family == "multivar":
        vars_ = ["n", "m", "k"]
        if rng.random() < 0.5:
            depth = rng.choice([2, 3])
            chosen = vars_[:depth]
            rng.shuffle(chosen)
            loops = [_rand_basic(rng, v, allow=("lin", "mul"), weights=[4, 1]) for v in chosen]
            blocks.append({"loops": loops})
            if rng.random() < 0.5:
                blocks.append({"loops": [_rand_basic(rng, rng.choice(vars_), allow=("lin",))]})
        else:
            for v in rng.sample(vars_, rng.choice([2, 3])):
                depth = rng.choice([1, 2])
                other = rng.choice(vars_)
                chain = [_rand_basic(rng, v, allow=("lin", "mul"), weights=[4, 1])]
                if depth == 2:
                    chain.append(_rand_basic(rng, other, allow=("lin", "mul"), weights=[3, 1]))
                blocks.append({"loops": chain})
    elif family == "dependent":
        chain = _dependent_chain(rng)
        blocks.append({"loops": chain})
        if rng.random() < 0.4:
            blocks.append({"loops": [_rand_basic(rng, "n", allow=("lin", "mul"), weights=[3, 1])]})
    elif family == "conditional":
        outer = {"kind": "lin", "var": "n", "step": 1}
        opts = [[], [{"kind": "lin", "var": "n", "step": 1}], [{"kind": "mul", "var": "n", "c": 2}],
                [{"kind": "const", "var": "n", "c": 10}]]
        a, b = rng.sample(range(len(opts)), 2)
        blocks.append({"cond": True, "outer": outer, "then": opts[a], "else": opts[b]})
        if rng.random() < 0.4:
            blocks.append({"loops": [_rand_basic(rng, "n", allow=("lin", "mul"), weights=[3, 1])]})
    return family, blocks


def block_cost(b):
    if b.get("cond"):
        outer = loop_mono(b["outer"])
        t, e = chain_cost(b["then"]), chain_cost(b["else"])
        worst = t if t.geq(e) else e
        return outer * worst
    return chain_cost(b["loops"])


def render(blocks):
    lines = ["count = 0"]
    marks = []
    for b in blocks:
        if b.get("cond"):
            lp = b["outer"]
            lines.append(f"for i = 1 to {lp['var']}")
            marks.append((len(lines), f"{lp['var']} iterations"))
            lines.append("    if A[i] > 0")
            marks.append((len(lines), "branch: worst case takes the more expensive side"))
            render_chain(b["then"], 2, ["j", "t"], lines, marks)
            lines.append("    else")
            render_chain(b["else"], 2, ["j", "t"], lines, marks)
        else:
            render_chain([dict(x) for x in b["loops"]], 0, LOOP_VARS, lines, marks)
    return "\n".join(lines), marks


# ---------------------------------------------------------------------------- explanation
def explain(blocks):
    steps = ["The basic operation is count = count + 1. Count how often it runs."]
    costs = []
    for idx, b in enumerate(blocks, start=1):
        c = block_cost(b)
        costs.append(c)
        tag = f"Section {idx}" if len(blocks) > 1 else "The code"
        if b.get("cond"):
            t, e = chain_cost(b["then"]), chain_cost(b["else"])
            steps.append(f"{tag}: an outer loop of n iterations containing an if/else.")
            steps.append(f"   then-branch costs {t.label()} per iteration, else-branch costs {e.label()}.")
            steps.append(f"   Worst case (every A[i] > 0 chooses the costlier side): n × {(t if t.geq(e) else e).label()} = {c.label()}")
            continue
        loops = b["loops"]
        parts = []
        i = 0
        while i < len(loops):
            lp = loops[i]
            nxt = loops[i + 1] if i + 1 < len(loops) else None
            if nxt and nxt["kind"] in ("dep_lin", "dep_log", "harm"):
                pair = chain_cost([lp, nxt]).label()
                if lp["kind"] == "mul":
                    parts.append(f"a doubling loop whose inner loop runs i times: 1 + 2 + 4 + ... < 2n → {pair}")
                elif nxt["kind"] == "dep_lin":
                    parts.append(f"a loop to n whose inner loop runs i times: 1 + 2 + ... + n = n(n + 1)/2 → {pair}")
                elif nxt["kind"] == "dep_log":
                    parts.append(f"a loop to n whose inner loop runs ≈ log i times: Σ log i = log(n!) → {pair}")
                else:
                    parts.append(f"a loop to n whose inner loop runs ≈ n/i times: n(1 + 1/2 + ... + 1/n) → {pair}")
                i += 2
                continue
            parts.append(f"{iter_label(lp)}")
            i += 1
        if len(parts) == 1:
            steps.append(f"{tag}: {parts[0]} → {c.label()}")
        else:
            steps.append(f"{tag}: nested → multiply: " + " × ".join(f"({p})" for p in parts) + f" = {c.label()}")
    if len(blocks) > 1:
        steps.append("The sections run one after another → ADD: T = " + " + ".join(x.label() for x in costs))
        simp = sum_label(costs)
        if simp != " + ".join(x.label() for x in costs):
            steps.append(f"Drop the dominated terms → {simp}")
    ans = sum_label(costs)
    steps.append(f"Therefore T ∈ Θ({ans}), and the tightest upper bound is O({ans}).")
    return steps, ans, costs


def distractors(costs, answer, rng):
    monos = simplify_sum(costs)
    cands = []
    # multiply everything (confusing sequential with nested)
    prod = Mono()
    for c in costs:
        prod = prod * c
    cands.append(prod.label())
    # one step more / less in each variable
    for m in monos:
        for v in list(m.t) or ["n"]:
            e, l = m.t.get(v, (Fraction(0), 0))
            cands.append(Mono({**{x: y for x, y in m.t.items()}, v: (e + 1, l)}).label())
            if l:
                cands.append(Mono({**m.t, v: (e, 0)}).label())
                cands.append(Mono({**m.t, v: (e + 1, 0)}).label())
            else:
                cands.append(Mono({**m.t, v: (e, 1)}).label())
            if e >= 1:
                cands.append(Mono({**m.t, v: (e - 1, l)}).label())
    # all variables collapsed into n
    vars_ = {v for m in monos for v in m.t}
    if len(vars_) > 1:
        tot = sum(float(m.t.get(v, (0, 0))[0]) for m in monos[:1] for v in m.t)
        cands.append({1: "n", 2: "n²", 3: "n³"}.get(int(tot), "n²"))
        cands.append(" + ".join(sorted(vars_)))
    cands += ["n", "n²", "log n", "n log n"]
    out = []
    for c in cands:
        if c != answer and c not in out and c.strip():
            out.append(c)
    rng.shuffle(out)
    opts = out[:4] + [answer]
    rng.shuffle(opts)
    return opts


def generate(family="mixed", seed=None):
    if seed is None:
        seed = random.randrange(10 ** 9)
    rng = random.Random(f"{family}:{seed}")
    fam, blocks = build_spec(family, rng)
    src, marks = render(blocks)
    steps, answer, costs = explain(blocks)
    options = distractors(costs, answer, rng)
    has_dep = any(lp.get("kind") in ("dep_lin", "dep_log", "harm") for b in blocks for lp in b.get("loops", []))
    has_log = "log" in answer or any(lp.get("kind") in ("mul", "div") for b in blocks for lp in b.get("loops", []))
    level = 5 if (has_dep or fam == "conditional") else 3 if fam == "multivar" else 4 if has_log else 2
    topic = {"single": "fundamentals", "sequential": "sequential", "nested": "nested_loops",
             "multivar": "multi_variable", "dependent": "irregular_loops", "conditional": "conditionals"}[fam]
    if fam in ("single", "nested") and has_log:
        topic = "logarithmic"
    vars_ = sorted({lp.get("var") for b in blocks for lp in b.get("loops", []) + [b.get("outer", {})] if lp.get("var")})
    prompt = "What is the time complexity? Choose the tightest (smallest correct) upper bound."
    if fam == "conditional":
        prompt = "What is the WORST-CASE time complexity? Choose the tightest upper bound. (A is an array of size n.)"
    if len(vars_) > 1:
        prompt += " The sizes " + ", ".join(vars_) + " are independent - don't assume they're equal."
    hints = [
        "Count how many times EACH loop runs on its own. Watch the update step: +1, ×2, ÷2 and i·i behave differently.",
        "Loops inside loops multiply; loops one after another add. If an inner bound depends on the outer variable, sum it instead.",
        "Write T as a sum of terms, then keep only the dominant term(s)." + (" Terms in different variables may both stay." if len(vars_) > 1 else ""),
    ]
    from engine.catalog import TOPIC_TAGS
    tags = list(TOPIC_TAGS.get(topic, [])) + ["big_o"]
    return {
        "id": f"gen-{family}-{seed}", "track": "complexity", "type": "generated", "topic": topic, "level": level,
        "title": f"Generated: {FAMILIES[fam].split(' (')[0].lower()}", "code": src, "prompt": prompt,
        "parts": [{"id": "answer", "kind": "choice", "wrap": "O", "label": "Tightest upper bound", "options": options, "answer": answer}],
        "hints": hints, "steps": steps, "highlights": [{"lines": [ln], "label": lab, "color": i % 4} for i, (ln, lab) in enumerate(marks)],
        "note": None, "tags": tags, "_spec": blocks, "family": fam, "seed": seed,
    }


# ---------------------------------------------------------------------------- exact simulator (used by tests)
def _iters(lp, env, outer):
    k = lp["kind"]
    if k == "lin":
        V = env[lp["var"]]
        s = lp.get("step", 1)
        return list(range(1, V + 1, s))
    if k == "const":
        return list(range(1, lp["c"] + 1))
    if k == "mul":
        out, i = [], 1
        while i < env[lp["var"]]:
            out.append(i)
            i *= lp["c"]
        return out
    if k == "div":
        out, i = [], env[lp["var"]]
        while i > 1:
            out.append(i)
            i = i / lp["c"]
        return out
    if k == "sqrt":
        out, i = [], 1
        while i * i <= env[lp["var"]]:
            out.append(i)
            i += 1
        return out
    if k == "dep_lin":
        return list(range(1, math.floor(outer) + 1))
    if k == "dep_log":
        out, j = [], 1
        while j < outer:
            out.append(j)
            j *= 2
        return out
    if k == "harm":
        return list(range(1, env[lp["var"]] + 1, outer))
    raise ValueError(k)


def _sim_chain(loops, env, outer=None):
    if not loops:
        return 1
    vals = _iters(loops[0], env, outer)
    if len(loops) == 1:
        return len(vals)
    return sum(_sim_chain(loops[1:], env, v) for v in vals)


def simulate(blocks, env):
    """Exact count of basic-operation executions (worst case for branches)."""
    total = 0
    for b in blocks:
        if b.get("cond"):
            for _ in _iters(b["outer"], env, None):
                total += max(_sim_chain(b["then"], env), _sim_chain(b["else"], env))
        else:
            total += _sim_chain(b["loops"], env)
    return total
