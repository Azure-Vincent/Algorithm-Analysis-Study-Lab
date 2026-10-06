"""Assemble the seed exercise bank into storable dictionaries."""
import copy

from engine.catalog import difficulty_of
from engine.pseudo import run_trace

from data import complexity_a, complexity_b, complexity_c, course_style_bank, proofs_bank, pseudocode_bank, trace_debug_bank

COLORS = 4


def _find_line(code, sub):
    occ = 1
    if "@" in sub:
        sub, occ = sub.rsplit("@", 1)
        occ = int(occ)
    sub = sub.rstrip("\n")
    hits = [i for i, line in enumerate(code.split("\n"), start=1) if sub in line]
    if len(hits) < occ:
        raise ValueError(f"highlight/snap text not found: {sub!r}")
    return hits[occ - 1]


def resolve_highlights(code, hl):
    out = []
    for idx, (subs, label) in enumerate(hl):
        if isinstance(subs, str):
            subs = [subs]
        out.append({"lines": [_find_line(code, s) for s in subs], "label": label, "color": idx % COLORS})
    return out


def raw_exercises():
    """Exercises as authored (including private test helpers like _sim)."""
    return (complexity_a.EXERCISES + complexity_b.EXERCISES + complexity_c.EXERCISES
            + pseudocode_bank.EXERCISES + trace_debug_bank.TRACES + trace_debug_bank.DEBUGS
            + course_style_bank.EXERCISES + proofs_bank.EXERCISES)


def finalize(ex, by_id):
    ex = {k: v for k, v in copy.deepcopy({k: v for k, v in ex.items() if not k.startswith("_")}).items()}
    ex["difficulty"] = difficulty_of(ex["level"])
    t = ex["type"]
    if ex["track"] == "complexity":
        ex["highlights"] = resolve_highlights(ex.get("code", ""), ex.get("highlights", [])) if ex.get("code") else []
    elif t == "trace":
        kind, where = ex["snap"]
        line = _find_line(ex["code"], where)
        res = run_trace(ex["code"], ex["inputs"], line if kind == "loop" else None, ex["watch"],
                        snap_after=line if kind == "after" else None)
        ex["rows"] = res["rows"]
        ex["snap_line"] = line
        ex["result"] = res["result"]
    elif t == "debug":
        ex["bug_line_numbers"] = sorted({_find_line(ex["buggy"], s) for s in ex["bug_lines"]})
    elif t == "to_complexity":
        src = by_id[ex["source"]]
        ex["code"] = src["solution"]
        ex["source_title"] = src["title"]
    return ex


def seed_exercises():
    raw = raw_exercises()
    by_id = {e["id"]: e for e in raw}
    if len(by_id) != len(raw):
        seen, dup = set(), []
        for e in raw:
            if e["id"] in seen:
                dup.append(e["id"])
            seen.add(e["id"])
        raise ValueError(f"duplicate exercise ids: {dup}")
    return [finalize(e, by_id) for e in raw] + tn_exercises()


def tn_exercises():
    """T(n) Analysis exercises, built from structured programs (see engine/tn.py)."""
    from data.tn_bank import SPECS
    from engine.tn import Exercise
    return [Exercise(spec).payload() for spec in SPECS]
