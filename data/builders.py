"""Small constructors that keep the exercise banks readable."""
import textwrap

from engine.catalog import TOPIC_TAGS
from engine.growth import (STD, NO_THETA, RANK, valid_upper, valid_lower,
                           why_upper, why_lower, why_theta)

WRAP_TAG = {"O": "big_o", "Θ": "big_theta", "Ω": "big_omega"}

IDENTIFY_PROMPT = {
    "O": "What is the time complexity? Choose the tightest (smallest correct) upper bound.",
    "Θ": "What is the tight bound Θ on the running time?",
    "Ω": "What is the tightest (largest correct) lower bound Ω on the running time?",
}


def code(s):
    return textwrap.dedent(s).strip("\n")


def _tags(topic, wraps=(), extra=()):
    t = list(TOPIC_TAGS.get(topic, []))
    for w in wraps:
        if w in WRAP_TAG and WRAP_TAG[w] not in t:
            t.append(WRAP_TAG[w])
    for e in extra:
        if e not in t:
            t.append(e)
    return t


def ident(id, level, topic, title, src, answer, hints, steps, hl=(), options=None, wrap="O",
          prompt=None, note=None, mode="identify"):
    opts = list(options or STD)
    assert answer in opts, (id, answer)
    return {
        "id": id, "track": "complexity", "type": mode, "topic": topic, "level": level,
        "title": title, "code": code(src),
        "prompt": prompt or (
            IDENTIFY_PROMPT[wrap] if mode == "identify" else
            "Derive the running time yourself. Use the scratch area to write down the count for each "
            "section (e.g. 'outer loop = n'), combine them, then choose the result."),
        "parts": [{"id": "answer", "kind": "choice", "wrap": wrap,
                   "label": {"O": "Tightest upper bound", "Θ": "Tight bound", "Ω": "Tightest lower bound"}[wrap],
                   "options": opts, "answer": answer}],
        "hints": hints, "steps": steps, "highlights": [list(h) for h in hl],
        "scratch": mode == "analyze", "note": note, "tags": _tags(topic, [wrap]),
    }


def analyze(*a, **k):
    k["mode"] = "analyze"
    return ident(*a, **k)


def count_ex(id, level, topic, title, src, op, at, sim, expr_options, expr_answer, answer, hints,
             steps, hl=(), expr_fn=None, options=None, note=None):
    """Mode D: exact count for a concrete size -> general expression -> complexity."""
    exact = sim(**at)
    at_txt = ", ".join(f"{k} = {v}" for k, v in at.items())
    ex = {
        "id": id, "track": "complexity", "type": "count", "topic": topic, "level": level,
        "title": title, "code": code(src),
        "prompt": f"Focus on the important operation `{op}`. Count first, then generalize, then simplify.",
        "parts": [
            {"id": "exact", "kind": "number", "label": f"For {at_txt}, exactly how many times does `{op}` execute?",
             "answer": exact},
            {"id": "expr", "kind": "choice", "wrap": "", "label": "Which expression gives that count in general?",
             "options": expr_options, "answer": expr_answer},
            {"id": "answer", "kind": "choice", "wrap": "Θ", "label": "Therefore, what is the complexity?",
             "options": list(options or STD), "answer": answer},
        ],
        "staged": True, "hints": hints, "steps": steps, "highlights": [list(h) for h in hl], "note": note,
        "tags": _tags(topic, ["Θ", "O"]),
    }
    ex["_sim"] = sim
    ex["_expr_fn"] = expr_fn
    ex["_at"] = at
    return ex


def bounds_ex(id, level, title, f, theta, steps, hints, classes=None, o_valid=None, om_valid=None,
              prompt=None, subject="f(n)", src="", note=None, topic="bounds"):
    classes = list(classes or ["1", "log n", "n", "n log n", "n²", "n³", "2ⁿ"])
    if theta is not None:
        o_ok = valid_upper(theta, classes)
        om_ok = valid_lower(theta, classes)
        why_o = {c: why_upper(theta, c, subject) for c in classes}
        why_om = {c: why_lower(theta, c, subject) for c in classes}
        th_opts = classes
        why_th = {c: why_theta(theta, c, subject) for c in classes}
    else:
        o_ok, om_ok = o_valid, om_valid
        why_o = {c: ("Valid: every input finishes within c·" + c + " steps." if c in o_ok else
                     "Invalid: some inputs need more than c·" + c + " steps.") for c in classes}
        why_om = {c: ("Valid: every input needs at least c·" + c + " steps." if c in om_ok else
                      "Invalid: some inputs finish faster than c·" + c + ".") for c in classes}
        th_opts = classes + [NO_THETA]
        why_th = {c: ("Correct: the tightest upper bound and the tightest lower bound differ, so no single Θ describes every input."
                      if c == NO_THETA else f"Θ({c}) would need both O({c}) and Ω({c}) to hold for all inputs.")
                  for c in th_opts}
    return {
        "id": id, "track": "complexity", "type": "bounds", "topic": topic, "level": level,
        "title": title, "code": code(src) if src else "", "formula": f,
        "prompt": prompt or f"Consider {subject} = {f}. Several upper and lower bounds can be mathematically "
                            "valid, but only one Θ bound is tight. Answer each part separately.",
        "parts": [
            {"id": "O", "kind": "multi", "wrap": "O", "label": f"Select EVERY valid upper bound: {subject} ∈ O(?)",
             "options": classes, "answer": o_ok, "why": why_o},
            {"id": "T", "kind": "choice", "wrap": "Θ", "label": f"Which is the tight bound? {subject} ∈ Θ(?)",
             "options": th_opts, "answer": theta if theta is not None else NO_THETA, "why": why_th},
            {"id": "W", "kind": "multi", "wrap": "Ω", "label": f"Select EVERY valid lower bound: {subject} ∈ Ω(?)",
             "options": classes, "answer": om_ok, "why": why_om},
        ],
        "hints": hints, "steps": steps, "highlights": [], "note": note,
        "tags": _tags(topic, ["O", "Θ", "Ω"]),
    }


def statements_ex(id, level, title, prompt, statements, hints, steps, src="", topic="bounds", formula=None):
    """statements: list of (text, is_true, why)."""
    return {
        "id": id, "track": "complexity", "type": "bounds", "topic": topic, "level": level,
        "title": title, "code": code(src) if src else "", "formula": formula, "prompt": prompt,
        "parts": [{"id": "S", "kind": "multi", "wrap": "", "label": "Select every TRUE statement",
                   "options": [s[0] for s in statements], "answer": [s[0] for s in statements if s[1]],
                   "why": {s[0]: s[2] for s in statements}}],
        "hints": hints, "steps": steps, "highlights": [], "note": None,
        "tags": _tags(topic, ["O", "Θ", "Ω"]),
    }


def cases_ex(id, level, title, src, best, avg, worst, hints, steps, hl=(), statement=None, options=None,
             prompt=None, note=None):
    opts = list(options or ["1", "log n", "n", "n log n", "n²", "n³", "2ⁿ"])
    parts = [
        {"id": "best", "kind": "choice", "wrap": "Θ", "label": "Best case", "options": opts, "answer": best},
        {"id": "avg", "kind": "choice", "wrap": "Θ", "label": "Average case", "options": opts, "answer": avg},
        {"id": "worst", "kind": "choice", "wrap": "Θ", "label": "Worst case", "options": opts, "answer": worst},
    ]
    if statement:
        q, choices, correct, why = statement
        parts.append({"id": "rel", "kind": "choice", "wrap": "", "label": q, "options": choices,
                      "answer": correct, "why": why})
    return {
        "id": id, "track": "complexity", "type": "cases", "topic": "cases", "level": level,
        "title": title, "code": code(src),
        "prompt": prompt or "The running time depends on the input. Give a tight bound for each case separately.",
        "parts": parts, "hints": hints, "steps": steps, "highlights": [list(h) for h in hl], "note": note,
        "tags": _tags("cases", ["Θ", "O", "Ω"]),
    }


def compare_ex(id, level, title, prompt, parts, hints, steps, algos=None, src="", note=None):
    for p in parts:
        p.setdefault("wrap", "")
    return {
        "id": id, "track": "complexity", "type": "compare", "topic": "growth_rates", "level": level,
        "title": title, "code": code(src) if src else "", "prompt": prompt, "parts": parts,
        "algos": algos, "hints": hints, "steps": steps, "highlights": [], "note": note,
        "tags": _tags("growth_rates", ["O"]),
    }
