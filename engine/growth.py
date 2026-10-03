"""Growth-rate classes, ordering, and bound reasoning shared by the question engine."""
import math

ONE, LOGLOG, LOG, LOG2, SQRT, N, NLOG, N2, N2LOG, N3, EXP, FACT = (
    "1", "log log n", "log n", "log² n", "√n", "n", "n log n", "n²", "n² log n", "n³", "2ⁿ", "n!")

RANK = {ONE: 0, LOGLOG: 1, LOG: 2, LOG2: 3, SQRT: 4, N: 5, NLOG: 6, N2: 7, N2LOG: 8, N3: 9, EXP: 10, FACT: 11}

STD = [ONE, LOG, N, NLOG, N2, N3, EXP, FACT]
NO_THETA = "No single Θ bound exists"

WORDS = {
    ONE: "constant", LOGLOG: "log-log", LOG: "logarithmic", LOG2: "log-squared", SQRT: "square-root",
    N: "linear", NLOG: "linearithmic", N2: "quadratic", N2LOG: "n² log n", N3: "cubic",
    EXP: "exponential", FACT: "factorial",
}


def rank(c):
    return RANK[c]


def valid_upper(theta, classes):
    """Classes c such that f ∈ O(c) when f ∈ Θ(theta)."""
    return [c for c in classes if c in RANK and RANK[c] >= RANK[theta]]


def valid_lower(theta, classes):
    return [c for c in classes if c in RANK and RANK[c] <= RANK[theta]]


def why_upper(theta, c, subject="f(n)"):
    if RANK[c] > RANK[theta]:
        return f"Valid but loose: {c} grows strictly faster than {theta}, so {c} is an upper bound, just not a tight one."
    if RANK[c] == RANK[theta]:
        return f"Valid and tight: {subject} grows like {theta}, so O({c}) is the most informative upper bound."
    return f"Invalid: {c} grows strictly slower than {theta}, so no constant c makes {subject} ≤ c·{c} for all large n."


def why_lower(theta, c, subject="f(n)"):
    if RANK[c] < RANK[theta]:
        return f"Valid but loose: {subject} grows faster than {c}, so it is eventually ≥ c·{c}. True, but it understates the growth."
    if RANK[c] == RANK[theta]:
        return f"Valid and tight: {subject} is eventually ≥ c·{theta} for some c > 0."
    return f"Invalid: {c} grows strictly faster than {theta}, so {subject} cannot stay above c·{c}."


def why_theta(theta, c, subject="f(n)"):
    if c == theta:
        return f"Correct: {subject} is bounded above AND below by constant multiples of {theta}."
    if c == NO_THETA:
        return f"A single Θ bound does exist here: {subject} ∈ Θ({theta})."
    if RANK.get(c, -1) > RANK[theta]:
        return f"Θ({c}) would need {subject} ≥ c·{c} eventually, but {subject} only grows like {theta}. O({c}) holds; Ω({c}) does not."
    return f"Θ({c}) would need {subject} ≤ c·{c} eventually, but {subject} grows like {theta}, which is faster. Ω({c}) holds; O({c}) does not."


def eval_class(c, n):
    """Numeric value of a growth function (used by the visualizer tests)."""
    lg = math.log2(n) if n > 1 else 0.0
    return {
        ONE: 1, LOGLOG: math.log2(lg) if lg > 1 else 0, LOG: lg, LOG2: lg * lg, SQRT: math.sqrt(n),
        N: n, NLOG: n * lg, N2: n * n, N2LOG: n * n * lg, N3: n ** 3,
        EXP: 2 ** n if n < 1024 else math.inf, FACT: math.factorial(n) if n < 171 else math.inf,
    }[c]
