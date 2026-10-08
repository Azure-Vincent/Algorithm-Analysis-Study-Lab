"""Server-side grading. Answers never leave the server until a submission or a solution request."""
from __future__ import annotations

import random
import re

from engine.pseudo import fmt, PseudoError
from engine.sandbox import run_tests  # student code always runs in an isolated, limited process

MARKER_RE = re.compile(r"^\s*//\s*complete this section\s*$", re.I)
PARTS_TYPES = {"to_complexity", "proof_debug", "proof_limit"}      # answered through multiple-choice / number parts
MATH_KINDS = {"expr", "work", "theta", "constant"}                # free-form math answers (engine.mathfound)
SECRET_PART_KEYS = ("answer", "why", "traps", "model")


def is_parts(ex):
    return ex["track"] in ("complexity", "math") or ex["type"] in PARTS_TYPES


# ============================================================================ public views
def public_view(ex):
    t = ex["type"]
    base = {k: ex.get(k) for k in ("id", "track", "type", "topic", "level", "difficulty", "title", "prompt", "source")}
    base["hint_count"] = len(ex.get("hints", []))
    if is_parts(ex):
        base.update(code=ex.get("code", ""), formula=ex.get("formula"), staged=ex.get("staged", False),
                    scratch=ex.get("scratch", False), algos=ex.get("algos"), source_title=ex.get("source_title"),
                    proof_text=ex.get("proof_text"), claim=ex.get("claim"))
        parts = []
        for p in ex["parts"]:
            q = {k: v for k, v in p.items() if k not in SECRET_PART_KEYS}
            if p["kind"] == "order":
                opts = list(p["options"])
                random.Random(ex["id"]).shuffle(opts)
                if opts == p["answer"]:
                    opts.reverse()
                q["options"] = opts
            parts.append(q)
        base["parts"] = parts
    elif t == "fill":
        base.update(template=ex["template"], blank_count=len(ex["blanks"]))
    elif t == "order":
        items = []
        for i, line in enumerate(ex["lines"]):
            stripped = line.lstrip(" ")
            items.append({"id": i, "text": stripped, "indent": (len(line) - len(stripped)) // 4})
        rng = random.Random(ex["id"])
        shuffled = items[:]
        for _ in range(5):
            rng.shuffle(shuffled)
            if [x["id"] for x in shuffled] != list(range(len(items))):
                break
        base["items"] = shuffled
    elif t == "complete":
        header, footer, indent = split_template(ex["template"])
        base.update(header=header, footer=footer, indent=indent)
    elif t == "write":
        base.update(starter=ex.get("starter", ""), params=ex.get("params"))
    elif t == "debug":
        base.update(code=ex["buggy"])
    elif t == "trace":
        base.update(code=ex["code"], inputs={k: fmt(v) for k, v in ex["inputs"].items()}, watch=ex["watch"],
                    snap_line=ex["snap_line"], snap_kind=ex["snap"][0], row_count=len(ex["rows"]))
    return base


def split_template(template):
    lines = template.split("\n")
    for i, line in enumerate(lines):
        if MARKER_RE.match(line):
            indent = len(line) - len(line.lstrip(" "))
            return "\n".join(lines[:i]), "\n".join(lines[i + 1:]), indent
    raise ValueError("template has no '// Complete this section' marker")


def assemble_complete(template, body):
    header, footer, indent = split_template(template)
    body_lines = body.replace("\t", "    ").split("\n")
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()
    nonblank = [ln for ln in body_lines if ln.strip()]
    common = min((len(ln) - len(ln.lstrip(" ")) for ln in nonblank), default=0)
    re_body = [(" " * indent + ln[common:]) if ln.strip() else "" for ln in body_lines]
    parts = [header] + re_body + ([footer] if footer else [])
    return "\n".join(parts), header.count("\n") + 1


# ============================================================================ helpers
def norm_blank(s):
    s = (s or "").strip().lower()
    for a, b in (("≤", "<="), ("≥", ">="), ("≠", "!="), ("<>", "!="), (":=", "="), ("←", "="), ("−", "-")):
        s = s.replace(a, b)
    s = re.sub(r"\s+", "", s)
    while s.startswith("(") and s.endswith(")") and _balanced(s[1:-1]):
        s = s[1:-1]
    return s


def _balanced(s):
    d = 0
    for ch in s:
        d += ch == "("
        d -= ch == ")"
        if d < 0:
            return False
    return d == 0


def pretty(s):
    s = re.sub(r"\s*(<=|>=|==|!=|[+*/<>]|(?<=[\w\)\]])-)\s*", r" \1 ", s)
    s = re.sub(r"\bdiv\b", " div ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_cell(s):
    s = str(s if s is not None else "").strip().lower()
    s = s.replace("−", "-")
    s = re.sub(r"[\[\]\(\)\s]", "", s)
    s = re.sub(r"-(inf|infinity)\b", "-∞", s)
    s = re.sub(r"^(inf|infinity)$", "∞", s)
    parts = []
    for p in s.split(","):
        if re.fullmatch(r"-?\d+\.0+", p):
            p = p.split(".")[0]
        parts.append(p)
    return ",".join(parts)


def norm_code(code):
    s = code.lower()
    for a, b in (("←", "="), ("<-", "="), (":=", "="), ("≤", "<="), ("≥", ">="), ("≠", "!="), ("−", "-")):
        s = s.replace(a, b)
    s = re.sub(r"//.*", "", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s


def check_rubric(code, rubric):
    n = norm_code(code)
    out = []
    for item in rubric:
        ok = any(re.search(p, n) for p in item["patterns"])
        out.append({"label": item["label"], "ok": ok, "hint": item["hint"]})
    return out


def parse_number(v):
    if v is None:
        return None
    s = str(v).strip().replace(",", "").replace("_", "").replace(" ", "")
    try:
        return float(s)
    except ValueError:
        return None


def _wrap(p, v):
    w = p.get("wrap", "")
    if isinstance(v, list):
        return ", ".join(_wrap(p, x) for x in v) if v else "(none selected)"
    if v is None or v == "":
        return "(no answer)"
    return f"{w}({v})" if w and v not in ("No single Θ bound exists",) else str(v)


# ============================================================================ complexity parts
def _answer_text(p):
    if p["kind"] == "order":
        return " < ".join(p["answer"])
    if p["kind"] == "work":
        return " → ".join(p["model"])
    return _wrap(p, p["answer"])


def grade_part(p, value):
    k = p["kind"]
    if k in MATH_KINDS:
        from engine import mathfound
        return mathfound.grade_part(p, value if isinstance(value, (str, int, float)) else "")
    res = {"id": p["id"], "label": p["label"], "kind": k}
    if k == "choice":
        ok = value == p["answer"]
        res.update(correct=ok, expected=_wrap(p, p["answer"]), given=_wrap(p, value))
        if p.get("why") and value in p["why"]:
            res["why"] = p["why"][value]
    elif k == "multi":
        sel = set(value or [])
        ans = set(p["answer"])
        ok = sel == ans
        details = []
        for opt in p["options"]:
            details.append({"option": _wrap(p, opt), "selected": opt in sel, "valid": opt in ans,
                            "why": (p.get("why") or {}).get(opt, "")})
        res.update(correct=ok, expected=_wrap(p, [o for o in p["options"] if o in ans]),
                   given=_wrap(p, [o for o in p["options"] if o in sel]), details=details)
    elif k == "number":
        num = parse_number(value)
        ok = num is not None and abs(num - float(p["answer"])) < 1e-6
        res.update(correct=ok, expected=f"{p['answer']:,}" if isinstance(p["answer"], int) else str(p["answer"]),
                   given=str(value) if value not in (None, "") else "(no answer)")
    elif k == "order":
        ok = list(value or []) == list(p["answer"])
        res.update(correct=ok, expected=" < ".join(p["answer"]), given=" < ".join(value or []))
    else:
        raise ValueError(k)
    return res


def grade_parts(ex, answer):
    vals = (answer or {}).get("parts", {})
    results = [grade_part(p, vals.get(p["id"])) for p in ex["parts"]]
    correct = all(r["correct"] for r in results)
    return {
        "correct": correct, "parts": results,
        "answer_text": "; ".join(f"{r['label']}: {r['given']}" for r in results),
        "correct_text": "; ".join(f"{r['label']}: {r['expected']}" for r in results),
    }


# ============================================================================ main entry
def grade(ex, answer):
    t = ex["type"]
    if is_parts(ex):
        res = grade_parts(ex, answer)
        if (answer or {}).get("scratch"):
            res["answer_text"] += f" | scratch: {answer['scratch'][:300]}"
    elif t == "fill":
        res = grade_fill(ex, answer)
    elif t == "order":
        res = grade_order(ex, answer)
    elif t in ("complete", "write"):
        res = grade_code(ex, answer)
    elif t == "debug":
        res = grade_debug(ex, answer)
    elif t == "trace":
        res = grade_trace(ex, answer)
    else:
        raise ValueError(t)
    res["solution"] = solution_payload(ex)
    return res


def solution_payload(ex):
    t = ex["type"]
    sol = {"steps": ex.get("steps", []), "note": ex.get("note")}
    if is_parts(ex):
        sol["highlights"] = ex.get("highlights", [])
        sol["answers"] = [{"id": p["id"], "label": p["label"], "answer": _answer_text(p), "raw": p["answer"]} for p in ex["parts"]]
        sol["code"] = ex.get("code", "")
    elif t == "trace":
        sol["rows"] = [[fmt(r[w]) for w in ex["watch"]] for r in ex["rows"]]
        sol["watch"] = ex["watch"]
        sol["code"] = ex["code"]
    elif t == "debug":
        sol["code"] = ex["solution"]
        sol["buggy"] = ex["buggy"]
        sol["bug_lines"] = ex["bug_line_numbers"]
    elif t == "fill":
        sol["code"] = ex["solution"]
        sol["blanks"] = [pretty(b["accept"][0]) for b in ex["blanks"]]
    else:
        sol["code"] = ex["solution"]
    return sol


def correct_text(ex):
    t = ex["type"]
    if is_parts(ex):
        return "; ".join(f"{p['label']}: {_answer_text(p)}" for p in ex["parts"])
    if t == "trace":
        return " | ".join(", ".join(f"{w}={fmt(r[w])}" for w in ex["watch"]) for r in ex["rows"])
    if t == "fill":
        return "; ".join(f"blank {i + 1}: {pretty(b['accept'][0])}" for i, b in enumerate(ex["blanks"]))
    return ex.get("solution", "")


# ============================================================================ pseudocode graders
def grade_fill(ex, answer):
    given = list((answer or {}).get("blanks", []))
    given += [""] * (len(ex["blanks"]) - len(given))
    per = []
    for i, b in enumerate(ex["blanks"]):
        ok = norm_blank(given[i]) in [norm_blank(a) for a in b["accept"]]
        per.append({"index": i, "given": given[i], "correct": ok, "expected": pretty(b["accept"][0])})
    correct = all(p["correct"] for p in per)
    tests = None
    note = None
    if not correct and ex.get("tests") and all(g.strip() for g in given):
        filled = ex["template"]
        for i, g in enumerate(given):
            filled = filled.replace(f"[[{i}]]", g.strip())
        tests = run_tests(filled, ex["tests"], ex.get("entry"), ex.get("params"))
        if tests["runnable"] and tests["passed"] == tests["total"]:
            correct = True
            note = "Your blanks differ from the reference answer but the completed code passes every test - accepted."
            for p in per:
                p["correct"] = True
    return {"correct": correct, "blanks": per, "tests": tests, "note": note,
            "answer_text": "; ".join(f"blank {p['index'] + 1}: {p['given'] or '(empty)'}" for p in per),
            "correct_text": correct_text(ex)}


def grade_order(ex, answer):
    order = list((answer or {}).get("order", []))
    n = len(ex["lines"])
    if sorted(order) != list(range(n)):
        return {"correct": False, "error": "Place every line exactly once.", "positions": [],
                "answer_text": str(order), "correct_text": ex["solution"]}
    positions = [{"pos": i, "id": oid, "correct": oid == i} for i, oid in enumerate(order)]
    correct = order == list(range(n))
    note = None
    assembled = "\n".join(ex["lines"][i] for i in order)
    tests = None
    if not correct and ex.get("tests"):
        tests = run_tests(assembled, ex["tests"], ex.get("entry"), ex.get("params"))
        if tests["runnable"] and tests["passed"] == tests["total"]:
            correct = True
            note = "Your order differs from the reference but produces a correct algorithm - accepted."
    return {"correct": correct, "positions": positions, "tests": tests, "note": note, "assembled": assembled,
            "answer_text": assembled, "correct_text": ex["solution"]}


def grade_code(ex, answer):
    body = (answer or {}).get("code", "")
    if ex["type"] == "complete":
        full, offset = assemble_complete(ex["template"], body)
    else:
        full, offset = body, 0
    rub = check_rubric(body, ex.get("rubric", []))
    tests = run_tests(full, ex["tests"], ex.get("entry"), ex.get("params"))
    structure_only = False
    if tests["runnable"]:
        correct = tests["passed"] == tests["total"]
    else:
        structure_only = True
        correct = bool(rub) and all(r["ok"] for r in rub) and bool(body.strip())
    err_line = tests.get("error_line")
    if err_line and offset:
        tests["error"] = re.sub(r"^Line \d+", f"Line {err_line - offset}" if err_line > offset else "Template", tests["error"])
    for r in tests.get("results", []):
        if r.get("error") and offset:
            m = re.match(r"^Line (\d+)", r["error"])
            if m:
                ln = int(m.group(1))
                r["error"] = re.sub(r"^Line \d+", f"Line {ln - offset}" if ln > offset else "Template", r["error"])
    return {"correct": correct, "rubric": rub, "tests": tests, "structure_only": structure_only,
            "assembled": full, "answer_text": body, "correct_text": ex["solution"]}


def grade_debug(ex, answer):
    line = (answer or {}).get("line")
    code = (answer or {}).get("code", "")
    line_ok = line is not None and int(line) in ex["bug_line_numbers"]
    sig = lambda c: [ln.rstrip() for ln in c.replace("\t", "    ").split("\n") if ln.strip()]
    unchanged = sig(code) == sig(ex["buggy"])
    tests = run_tests(code, ex["tests"], ex.get("entry"), ex.get("params"))
    if tests["runnable"]:
        fix_ok = tests["passed"] == tests["total"] and not unchanged
    else:
        fix_ok = norm_code(code).split() == norm_code(ex["solution"]).split()
    return {"correct": line_ok and fix_ok, "line_ok": line_ok, "line": line, "fix_ok": fix_ok, "unchanged": unchanged,
            "tests": tests, "answer_text": f"line {line}; code:\n{code}", "correct_text": ex["solution"]}


def grade_trace(ex, answer):
    rows = (answer or {}).get("rows", [])
    table = []
    all_ok = True
    for ri, exp_row in enumerate(ex["rows"]):
        given_row = rows[ri] if ri < len(rows) else []
        cells = []
        for ci, w in enumerate(ex["watch"]):
            exp = fmt(exp_row[w])
            g = given_row[ci] if ci < len(given_row) else ""
            ok = norm_cell(g) == norm_cell(exp)
            all_ok &= ok
            cells.append({"given": g, "expected": exp, "correct": ok})
        table.append(cells)
    wrong = sum(1 for r in table for c in r if not c["correct"])
    return {"correct": all_ok, "table": table, "wrong_cells": wrong,
            "answer_text": " | ".join(", ".join(f"{w}={c['given'] or '?'}" for w, c in zip(ex["watch"], r)) for r in table),
            "correct_text": correct_text(ex)}


def check_part(ex, part_id, value):
    for p in ex["parts"]:
        if p["id"] == part_id:
            return grade_part(p, value)
    raise KeyError(part_id)


__all__ = ["public_view", "grade", "check_part", "solution_payload", "correct_text", "PseudoError"]
