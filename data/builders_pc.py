"""Constructors for Pseudocode Lab exercises."""
import textwrap

from engine.catalog import TOPIC_TAGS


def code(s):
    return textwrap.dedent(s).strip("\n")


def _tags(topic):
    return ["pseudocode"] + list(TOPIC_TAGS.get(topic, []))


# ---- reusable rubric checks (patterns run on normalized, lower-cased code) ----
R = {
    "loop": ("Iteration", [r"\b(for|while)\b"], "Visit the elements with a for or while loop."),
    "return": ("Return value", [r"\breturn\s+\S"], "Return the result at the end."),
    "if": ("Selection (if)", [r"\bif\b"], "Use an if statement to test each element."),
    "init0": ("Initialization", [r"\b[a-z_]\w*\s*=\s*0\b"], "Initialize your counter / accumulator to 0 before the loop."),
    "inc": ("Counter update", [r"\b([a-z_]\w*)\s*=\s*\1\s*\+\s*1\b", r"\+\+", r"\+=\s*1\b", r"\bincrement\b",
                               r"\b([a-z_]\w*)\s*=\s*1\s*\+\s*\1\b"], "Add 1 to the counter when the condition holds."),
    "accum": ("Accumulation", [r"\b([a-z_]\w*)\s*=\s*\1\s*\+", r"\+=", r"\b([a-z_]\w*)\s*=\s*[a-z_]\w*(?:\[[^\]]*\])?\s*\+\s*\1\b"],
              "Add each element to a running total."),
    "even": ("Even test", [r"(mod|%)\s*2\s*==?\s*0", r"\beven\b"], "An integer x is even when x mod 2 = 0."),
    "neg": ("Negative test", [r"<\s*0\b", r"\b0\s*>(?!=)"], "A value x is negative when x < 0."),
    "pos": ("Positive test", [r">\s*0\b", r"\b0\s*<(?!=)"], "A value x is positive when x > 0."),
    "index": ("Array indexing", [r"\[[^\]]+\]", r"\bfor\s+(each\s+)?\w+\s+in\b"], "Access elements as A[i] (0-indexed)."),
    "first": ("Start from the first element", [r"=\s*[a-z_]\w*\[\s*0\s*\]"], "Initialize the best-so-far with the first element, not 0."),
    "divide": ("Division", [r"/", r"\bdiv\b"], "Divide the total by the number of elements."),
    "empty": ("Empty-input check", [r"==?\s*0", r"<\s*1\b", r"\bempty\b"], "Handle an empty array before dividing."),
    "swap": ("Swap", [r"\bswap\b", r"\bexchange\b", r"\btemp\b|\btmp\b"], "Exchange two elements (swap)."),
    "nested": ("Nested loops", [r"\b(for|while)\b[\s\S]*\n\s+[\s\S]*\b(for|while)\b"], "Compare pairs using a loop inside a loop."),
    "neg1": ("Not-found result", [r"return\s+-\s*1\b"], "Return -1 when the target isn't found."),
    "mid": ("Middle index", [r"\bmid\w*\s*=", r"\bmiddle\s*="], "Compute the middle index of the current range."),
    "halve": ("Halving the range", [r"\b(low|lo|left|l|start)\w*\s*=\s*\w+\s*\+\s*1", r"\b(high|hi|right|r|end)\w*\s*=\s*\w+\s*-\s*1"],
              "Move low or high past mid to discard half of the range."),
    "sqrt": ("Divisor loop", [r"\bmod\b|%"], "Test divisors with mod."),
    "rec_call": ("Recursive call", [r"\b(\w+)\s*\(.*\)[\s\S]*\b\1\s*\("], "The procedure must call itself on a smaller input."),
    "base": ("Base case", [r"\bif\b[^\n]*(==|<=|<)\s*[01]\b", r"\bif\b[^\n]*\b0\b"], "Stop the recursion with a base case (e.g. n = 0)."),
}


def rubric(*keys, extra=()):
    items = [{"label": R[k][0], "patterns": R[k][1], "hint": R[k][2]} for k in keys]
    for label, pats, hint in extra:
        items.append({"label": label, "patterns": pats, "hint": hint})
    return items


def _base(id, type_, topic, level, title, prompt, hints, explanation, entry, params, tests, solution):
    return {
        "id": id, "track": "pseudocode", "type": type_, "topic": topic, "level": level, "title": title,
        "prompt": prompt, "hints": hints, "steps": explanation, "entry": entry, "params": params,
        "tests": tests, "solution": code(solution), "tags": _tags(topic),
    }


def fill(id, topic, level, title, prompt, template, blanks, solution, entry, params, tests, hints, explanation):
    ex = _base(id, "fill", topic, level, title, prompt, hints, explanation, entry, params, tests, solution)
    ex["template"] = code(template)
    ex["blanks"] = [{"accept": b} for b in blanks]
    return ex


def order(id, topic, level, title, prompt, lines, entry, params, tests, hints, explanation):
    """lines: correct program, one statement per line, indentation included."""
    src = code(lines)
    ex = _base(id, "order", topic, level, title, prompt, hints, explanation, entry, params, tests, src)
    ex["lines"] = src.split("\n")
    return ex


def complete(id, topic, level, title, prompt, template, solution, entry, params, tests, rub, hints, explanation):
    ex = _base(id, "complete", topic, level, title, prompt, hints, explanation, entry, params, tests, solution)
    ex["template"] = code(template)
    ex["rubric"] = rub
    return ex


def write(id, topic, level, title, prompt, starter, solution, entry, params, tests, rub, hints, explanation):
    ex = _base(id, "write", topic, level, title, prompt, hints, explanation, entry, params, tests, solution)
    ex["starter"] = starter
    ex["rubric"] = rub
    return ex


def to_complexity(id, source, level, title, answer, options, hints, explanation, topic):
    return {
        "id": id, "track": "pseudocode", "type": "to_complexity", "topic": topic, "level": level,
        "title": title, "source": source,
        "prompt": "You built this algorithm in the Pseudocode Lab. Now analyze it: what is its worst-case time complexity?",
        "parts": [{"id": "answer", "kind": "choice", "wrap": "Θ", "label": "Worst-case running time",
                   "options": options, "answer": answer}],
        "hints": hints, "steps": explanation, "tags": _tags(topic) + ["big_o"],
    }


def T(*args, expect, check="return"):
    return {"args": list(args), "expect": expect, "check": check}
