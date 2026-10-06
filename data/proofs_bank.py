"""Time Complexity Proofs: prove / disprove, proof construction, proof debugging, ratio & limit method.

Reference constants are deliberately simple (not the smallest possible) - the point is that ANY valid
c and n₀ prove the claim. The test suite checks every true claim's constants with the proof checker and
every claim's truth value against lim f(n)/g(n).
"""
from engine import proofs as P

PROMPT = ("Prove or disprove the claim. If it is true, give constants that satisfy the definition - they only need "
          "to be valid, not the smallest possible. If it is false, explain why no constants can work.")
REL_TAG = {"O": "big_o", "omega": "big_omega", "theta": "big_theta"}


def prove(id, level, topic, f, g, rel, truth, sol=None, why=(), intuition="", hints=(), f_text=None, g_text=None,
          note=None):
    F, G = P.parse_fn(f), P.parse_fn(g, "g(n)")
    ft, gt = f_text or P.show(F), g_text or P.show(G)
    claim = f"{ft} ∈ {P.REL_SYMBOL[rel]}({gt})"
    return {"id": id, "track": "proofs", "type": "proof", "topic": topic, "level": level, "title": claim,
            "rel": rel, "truth": truth, "f": f, "g": g, "f_text": ft, "g_text": gt, "prompt": PROMPT,
            "solution": {k: str(v) for k, v in (sol or {}).items()}, "why": list(why), "intuition": intuition,
            "hints": list(hints), "steps": [], "note": note, "tags": ["proofs", REL_TAG[rel]]}


def fill(id, level, rel, claim, template, blanks, steps, hints, disprove=False):
    return {"id": id, "track": "proofs", "type": "proof_fill", "topic": "pf_construct", "level": level,
            "title": f"Complete the proof: {claim}", "rel": rel, "claim": claim, "disprove": disprove,
            "prompt": "Fill in the missing pieces so that every line of the proof follows from the one before it.",
            "template": template.strip("\n"), "blanks": blanks, "steps": steps, "hints": hints,
            "tags": ["proofs", REL_TAG[rel]]}


def debug(id, level, rel, claim, proof_text, parts, steps, hints):
    for p in parts:
        p.setdefault("wrap", "")
    return {"id": id, "track": "proofs", "type": "proof_debug", "topic": "pf_debug", "level": level,
            "title": f"Find the flaw: {claim}", "rel": rel, "claim": claim, "proof_text": proof_text.strip("\n"),
            "prompt": "Here is an attempted proof. Find what is wrong with it.", "code": "", "parts": parts,
            "steps": steps, "hints": hints, "highlights": [], "tags": ["proofs", REL_TAG[rel]]}


def limit(id, level, rel, claim, proof_text, parts, steps, hints, prompt=None):
    for p in parts:
        p.setdefault("wrap", "")
    return {"id": id, "track": "proofs", "type": "proof_limit", "topic": "pf_limits", "level": level,
            "title": f"Ratio method: {claim}", "rel": rel, "claim": claim, "proof_text": proof_text.strip("\n"),
            "prompt": prompt or ("Investigate the ratio f(n)/g(n) as n grows. A table only builds intuition; the limit "
                                 "is a separate, rigorous argument; a proof from the definition uses c and n₀."),
            "code": "", "parts": parts, "steps": steps, "hints": hints, "highlights": [], "tags": ["proofs", REL_TAG[rel]]}


UPPER_HINTS = ["Write the inequality first: f(n) ≤ c·g(n).", "Bound each lower-order term by a multiple of g(n) once n ≥ 1.",
               "Add up the coefficients to get c; any larger c works too."]
FALSE_HINTS = ["Try to write f(n) ≤ c·g(n) and divide both sides by g(n).", "What happens to f(n)/g(n) as n grows?",
               "If f(n)/g(n) grows without bound, no fixed c can stay above it."]

PROOFS = [
    # ============================================================ Level 1 - simple polynomial bounds
    prove("pf-o-n-n2", 1, "pf_poly", "n", "n^2", "O", True, {"c": 1, "n0": 1},
          ["For n ≥ 1, multiplying both sides of 1 ≤ n by n gives n ≤ n²."],
          "n² eventually dwarfs n.", ["We need n ≤ c·n² for every n ≥ n₀.", "Try c = 1. For which n is n ≤ n²?",
                                      "1 ≤ n, multiplied by n, gives n ≤ n²."]),
    prove("pf-o-n2-n3", 1, "pf_poly", "n^2", "n^3", "O", True, {"c": 1, "n0": 1},
          ["For n ≥ 1: n² = n²·1 ≤ n²·n = n³."],
          "A higher power grows faster.", ["We need n² ≤ c·n³.", "Try c = 1, n₀ = 1.", "Multiply 1 ≤ n by n²."]),
    prove("pf-w-n3-n2", 1, "pf_poly", "n^3", "n^2", "omega", True, {"c": 1, "n0": 1},
          ["For n ≥ 1: n² = n²·1 ≤ n²·n = n³, i.e. 1·n² ≤ n³."],
          "n³ grows at least as fast as n².", ["For Ω the inequality is c·g(n) ≤ f(n): c·n² ≤ n³.", "Try c = 1.",
                                               "Multiply 1 ≤ n by n²."]),
    prove("pf-t-5n-n", 1, "pf_poly", "5n", "n", "theta", True, {"c1": 5, "c2": 5, "n0": 1},
          ["5n is exactly 5·n, so 5·n ≤ 5n ≤ 5·n holds for every n ≥ 1 (any c₁ ≤ 5 ≤ c₂ works too)."],
          "A constant factor never changes the growth class.",
          ["Θ needs two inequalities: c₁·n ≤ 5n ≤ c₂·n.", "Both can use the same constant here.", "c₁ = c₂ = 5, n₀ = 1."]),
    prove("pf-o-1-n", 1, "pf_poly", "1", "n", "O", True, {"c": 1, "n0": 1},
          ["For n ≥ 1: 1 ≤ n = 1·n."],
          "A constant never grows, n does.", ["We need 1 ≤ c·n.", "Which n make 1 ≤ n true?", "c = 1, n₀ = 1."]),
    prove("pf-w-n-1", 1, "pf_poly", "n", "1", "omega", True, {"c": 1, "n0": 1},
          ["For n ≥ 1: 1·1 = 1 ≤ n."],
          "n grows past any constant.", ["For Ω: c·1 ≤ n.", "Choose c = 1.", "Then you need 1 ≤ n - true from n₀ = 1."]),

    # ============================================================ Level 2 - polynomial expressions
    prove("pf-o-3n7-n", 2, "pf_poly", "3n + 7", "n", "O", True, {"c": 10, "n0": 1},
          ["For n ≥ 1: 7 ≤ 7n.", "So 3n + 7 ≤ 3n + 7n = 10n."],
          "The constant 7 is soon negligible next to 3n.", UPPER_HINTS,
          note="c = 4 also works from n₀ = 7 (because 7 ≤ n there) - any valid pair is a proof."),
    prove("pf-t-4n2-n2", 2, "pf_poly", "4n^2 + 3n + 7", "n^2", "theta", True, {"c1": 4, "c2": 14, "n0": 1},
          ["Lower bound: 3n + 7 ≥ 0, so 4n² ≤ 4n² + 3n + 7.",
           "Upper bound: for n ≥ 1, 3n ≤ 3n² and 7 ≤ 7n², so 4n² + 3n + 7 ≤ 4n² + 3n² + 7n² = 14n²."],
          "The n² term dominates; the rest only changes constants.",
          ["Θ: c₁·n² ≤ 4n² + 3n + 7 ≤ c₂·n².", "Lower bound: drop the non-negative terms 3n + 7.",
           "Upper bound: bound 3n by 3n² and 7 by 7n²."]),
    prove("pf-o-2n3-n3", 2, "pf_poly", "2n^3 + 5n^2 + 100", "n^3", "O", True, {"c": 107, "n0": 1},
          ["For n ≥ 1: 5n² ≤ 5n³ and 100 ≤ 100n³.", "So 2n³ + 5n² + 100 ≤ 2n³ + 5n³ + 100n³ = 107n³."],
          "Lower-order terms and constants are swamped by n³.", UPPER_HINTS,
          note="A smaller c needs a larger n₀: c = 3 works from n₀ = 8. Both are valid proofs."),
    prove("pf-w-n2-3n", 2, "pf_poly", "n^2 + 3n", "n^2", "omega", True, {"c": 1, "n0": 1},
          ["3n ≥ 0 for n ≥ 1, so 1·n² ≤ n² + 3n."],
          "Adding a positive term can only make f bigger.",
          ["For Ω: c·n² ≤ n² + 3n.", "Is n² ≤ n² + 3n?", "Yes, since 3n ≥ 0 - so c = 1."]),
    prove("pf-o-5n2-n2", 2, "pf_poly", "5n^2 + 2n + 1", "n^2", "O", True, {"c": 8, "n0": 1},
          ["For n ≥ 1: 2n ≤ 2n² and 1 ≤ n².", "So 5n² + 2n + 1 ≤ 5n² + 2n² + n² = 8n²."],
          "n² dominates 2n + 1.", UPPER_HINTS),
    prove("pf-t-n2-100n", 2, "pf_poly", "n^2 + 100n", "n^2", "theta", True, {"c1": 1, "c2": 101, "n0": 1},
          ["Lower bound: 100n ≥ 0, so n² ≤ n² + 100n.", "Upper bound: for n ≥ 1, 100n ≤ 100n², so n² + 100n ≤ 101n²."],
          "Even a large coefficient on a lower-order term doesn't change the class.",
          ["Θ needs c₁·n² ≤ n² + 100n ≤ c₂·n².", "Lower: drop 100n.", "Upper: 100n ≤ 100n² for n ≥ 1."],
          note="With n₀ = 100 you could take c₂ = 2, since 100n ≤ n² once n ≥ 100."),
    prove("pf-w-4n3-n3", 2, "pf_poly", "4n^3 + n^2", "n^3", "omega", True, {"c": 4, "n0": 1},
          ["n² ≥ 0, so 4n³ ≤ 4n³ + n²."],
          "The leading term alone already gives the lower bound.",
          ["For Ω: c·n³ ≤ 4n³ + n².", "Drop the non-negative n².", "c = 4 (or anything smaller and positive)."]),
    prove("pf-t-3n2-n2", 2, "pf_poly", "3n^2 + 5n + 2", "n^2", "theta", True, {"c1": 3, "c2": 10, "n0": 1},
          ["Lower bound: 5n + 2 ≥ 0, so 3n² ≤ 3n² + 5n + 2.",
           "Upper bound: for n ≥ 1, 5n ≤ 5n² and 2 ≤ 2n², so 3n² + 5n + 2 ≤ 10n²."],
          "Constants and lower-order terms don't affect the growth class.",
          ["Write both: c₁·n² ≤ 3n² + 5n + 2 ≤ c₂·n².", "Lower: 5n + 2 ≥ 0.", "Upper: 5n ≤ 5n², 2 ≤ 2n² for n ≥ 1."]),
    prove("pf-w-n2m10n-n2", 2, "pf_poly", "n^2 - 10n", "n^2", "omega", True, {"c": "1/2", "n0": 20},
          ["For n ≥ 20: n/2 ≥ 10, so 10n ≤ n²/2.", "So n² − 10n ≥ n² − n²/2 = n²/2 (and n² − 10n ≥ 0 there too)."],
          "Subtracting 10n can't keep up with n² forever.",
          ["Here c = 1 can't work (n² ≤ n² − 10n is never true). Try c = 1/2.",
           "(1/2)n² ≤ n² − 10n ⇔ 10n ≤ n²/2 ⇔ n ≥ 20.", "So n₀ must be at least 20 - n₀ = 1 fails."]),
    prove("pf-o-np1sq-n2", 2, "pf_poly", "(n+1)^2", "n^2", "O", True, {"c": 4, "n0": 1},
          ["(n + 1)² = n² + 2n + 1.", "For n ≥ 1: 2n ≤ 2n² and 1 ≤ n², so n² + 2n + 1 ≤ 4n²."],
          "Shifting n by 1 doesn't change how fast n² grows.", ["Expand (n + 1)² first.", "Then bound 2n and 1 by multiples of n².",
                                                                "1 + 2 + 1 = 4."], f_text="(n + 1)²"),

    # ============================================================ Level 3 - comparing growth classes
    prove("pf-o-log-n", 3, "pf_growth", "log2(n)", "n", "O", True, {"c": 1, "n0": 1},
          ["For n ≥ 1: n < 2ⁿ (doubling at least once per step beats adding 1 per step).",
           "Taking log₂ of both sides: log₂ n < n = 1·n."],
          "log n grows much more slowly than n.",
          ["We need log₂ n ≤ c·n.", "Compare n with 2ⁿ.", "n ≤ 2ⁿ ⇒ log₂ n ≤ n."]),
    prove("pf-o-log-n2", 3, "pf_growth", "log2(n)", "n^2", "O", True, {"c": 1, "n0": 1},
          ["For n ≥ 1: log₂ n ≤ n (because n ≤ 2ⁿ).", "And n ≤ n² for n ≥ 1.", "So log₂ n ≤ n ≤ n² = 1·n²."],
          "log n grows much more slowly than n² - but this observation alone is not a proof.",
          ["Write the inequality: log₂ n ≤ c·n².", "Chain two simpler facts: log₂ n ≤ n and n ≤ n².",
           "c = 1 and n₀ = 1 work - you don't need the smallest constants."]),
    prove("pf-o-n-nlog", 3, "pf_growth", "n", "n log2(n)", "O", True, {"c": 1, "n0": 2},
          ["For n ≥ 2: log₂ n ≥ 1, so n = n·1 ≤ n·log₂ n."],
          "n log n grows a little faster than n.",
          ["We need n ≤ c·n log₂ n.", "Divide by n: when is 1 ≤ c·log₂ n?", "log₂ n ≥ 1 once n ≥ 2 - n₀ = 1 fails (log₂ 1 = 0)."],
          note="n₀ = 1 does NOT work: at n = 1, n log₂ n = 0 < 1."),
    prove("pf-o-nlog-n2", 3, "pf_growth", "n log2(n)", "n^2", "O", True, {"c": 1, "n0": 1},
          ["For n ≥ 1: log₂ n ≤ n.", "Multiplying by n ≥ 1: n log₂ n ≤ n·n = n²."],
          "n log n sits between n and n².",
          ["We need n log₂ n ≤ c·n².", "Divide by n: log₂ n ≤ c·n.", "You already know log₂ n ≤ n."]),
    prove("pf-o-n3-2n", 3, "pf_growth", "n^3", "2^n", "O", True, {"c": 1, "n0": 10},
          ["At n = 10: 10³ = 1000 ≤ 1024 = 2¹⁰.",
           "From n to n + 1, n³ is multiplied by ((n+1)/n)³ ≤ (1.1)³ ≈ 1.33 < 2 when n ≥ 10, while 2ⁿ doubles.",
           "So, by induction, n³ ≤ 2ⁿ for every n ≥ 10."],
          "Any polynomial is eventually overtaken by 2ⁿ - but only eventually, which is what n₀ is for.",
          ["Try c = 1. Is n³ ≤ 2ⁿ at n = 2? At n = 10?", "The inequality fails for n = 2, …, 9.",
           "So n₀ = 10; prove the rest by induction (2ⁿ doubles, n³ grows by less than ×2)."]),
    prove("pf-w-2n-n2", 3, "pf_growth", "2^n", "n^2", "omega", True, {"c": 1, "n0": 4},
          ["At n = 4: 4² = 16 ≤ 16 = 2⁴.",
           "From n to n + 1, n² is multiplied by ((n+1)/n)² ≤ (5/4)² < 2 when n ≥ 4, while 2ⁿ doubles.",
           "So n² ≤ 2ⁿ for every n ≥ 4."],
          "Exponential growth beats any polynomial eventually.",
          ["For Ω: c·n² ≤ 2ⁿ.", "With c = 1: check n = 3 and n = 4.", "Induction: 2ⁿ doubles, n² grows by less than ×2."]),
    prove("pf-o-2n-nf", 3, "pf_growth", "2^n", "n!", "O", True, {"c": 1, "n0": 4},
          ["At n = 4: 2⁴ = 16 ≤ 24 = 4!.", "From n to n + 1, 2ⁿ is multiplied by 2 but n! by n + 1 ≥ 5.",
           "So 2ⁿ ≤ n! for every n ≥ 4."],
          "Each factor of n! eventually exceeds 2.",
          ["Compare 2ⁿ and n! at n = 1, 2, 3, 4.", "From n = 4 on, n! grows by a factor n + 1 > 2 each step.",
           "c = 1, n₀ = 4."]),
    prove("pf-w-nlog-n", 3, "pf_growth", "n log2(n)", "n", "omega", True, {"c": 1, "n0": 2},
          ["For n ≥ 2: log₂ n ≥ 1, so 1·n ≤ n log₂ n."],
          "n log n grows at least as fast as n.",
          ["For Ω: c·n ≤ n log₂ n.", "Divide by n: c ≤ log₂ n.", "log₂ n ≥ 1 from n = 2."]),
    prove("pf-t-logsq-log", 3, "pf_growth", "log2(n^2)", "log2(n)", "theta", True, {"c1": 2, "c2": 2, "n0": 2},
          ["log₂(n²) = 2 log₂ n (log of a power).", "So 2·log₂ n ≤ log₂(n²) ≤ 2·log₂ n for every n ≥ 2."],
          "Squaring inside the log only doubles it.",
          ["Use the log rule log(a^k) = k·log a.", "Then both inequalities are equalities.", "c₁ = c₂ = 2."],
          f_text="log₂(n²)"),
    prove("pf-o-nlog5n-nlog", 3, "pf_growth", "n log2(n) + 5n", "n log2(n)", "O", True, {"c": 6, "n0": 2},
          ["For n ≥ 2: log₂ n ≥ 1, so 5n ≤ 5n log₂ n.", "So n log₂ n + 5n ≤ 6 n log₂ n."],
          "n is a lower-order term next to n log n.",
          ["Bound 5n by a multiple of n log₂ n.", "That needs log₂ n ≥ 1, i.e. n ≥ 2.", "c = 1 + 5 = 6, n₀ = 2."]),
    prove("pf-o-sqrt-n", 3, "pf_growth", "sqrt(n)", "n", "O", True, {"c": 1, "n0": 1},
          ["For n ≥ 1: √n ≥ 1, so √n = √n·1 ≤ √n·√n = n."],
          "√n grows more slowly than n.", ["We need √n ≤ c·n.", "n = √n·√n.", "c = 1, n₀ = 1."]),
    prove("pf-w-n2-nlog", 3, "pf_growth", "n^2", "n log2(n)", "omega", True, {"c": 1, "n0": 1},
          ["For n ≥ 1: log₂ n ≤ n, so 1·n log₂ n ≤ n·n = n²."],
          "n² grows faster than n log n.", ["For Ω: c·n log₂ n ≤ n².", "Divide by n.", "log₂ n ≤ n."]),
    prove("pf-o-7-log", 3, "pf_growth", "7", "log2(n)", "O", True, {"c": 7, "n0": 2},
          ["For n ≥ 2: log₂ n ≥ 1, so 7 ≤ 7 log₂ n."],
          "A constant is O of anything that eventually stays ≥ a positive number.",
          ["We need 7 ≤ c·log₂ n.", "log₂ 1 = 0, so n₀ = 1 can't work.", "From n = 2, log₂ n ≥ 1."]),

    # ============================================================ Level 4 - false statements (and one trap)
    prove("pf-f-n2-n", 4, "pf_false", "n^2", "n", "O", False, None,
          ["Suppose n² ≤ c·n for every n ≥ n₀, for some constants c > 0 and n₀ > 0.",
           "Dividing by n > 0: n ≤ c for every n ≥ n₀.",
           "But n = max(n₀, c) + 1 is ≥ n₀ and larger than c - a contradiction."],
          "n² eventually exceeds every multiple of n.", FALSE_HINTS),
    prove("pf-f-n3-n2", 4, "pf_false", "n^3", "n^2", "O", False, None,
          ["Suppose n³ ≤ c·n² for every n ≥ n₀.", "Dividing by n² > 0: n ≤ c for every n ≥ n₀.",
           "That fails for any n > max(n₀, c) - so no constants exist."],
          "n³/n² = n is unbounded.", FALSE_HINTS),
    prove("pf-f-2n-n3", 4, "pf_false", "2^n", "n^3", "O", False, None,
          ["Suppose 2ⁿ ≤ c·n³ for every n ≥ n₀, i.e. 2ⁿ / n³ ≤ c.",
           "From n to n + 1 the ratio 2ⁿ/n³ is multiplied by 2·(n/(n+1))³, which is more than 1.5 once n ≥ 10.",
           "So 2ⁿ/n³ grows without bound and eventually exceeds any c - a contradiction."],
          "Exponential beats every polynomial.", FALSE_HINTS),
    prove("pf-f-nf-2n", 4, "pf_false", "n!", "2^n", "O", False, None,
          ["Suppose n! ≤ c·2ⁿ for every n ≥ n₀, i.e. n!/2ⁿ ≤ c.",
           "n!/2ⁿ = (1/2)(2/2)(3/2)⋯(n/2) ≥ (1/2)·(3/2)ⁿ⁻² for n ≥ 2, which grows without bound.",
           "So n!/2ⁿ eventually exceeds c - a contradiction."],
          "Each new factor of n! is bigger than 2, so n! pulls away from 2ⁿ.", FALSE_HINTS),
    prove("pf-f-n-log", 4, "pf_false", "n", "log2(n)", "O", False, None,
          ["Suppose n ≤ c·log₂ n for every n ≥ n₀.", "Take n = 2ᵏ: then 2ᵏ ≤ c·k, i.e. 2ᵏ / k ≤ c for every large k.",
           "But 2ᵏ / k grows without bound - contradiction."],
          "n grows much faster than log n.", FALSE_HINTS),
    prove("pf-f-w-n-n2", 4, "pf_false", "n", "n^2", "omega", False, None,
          ["Suppose c·n² ≤ n for every n ≥ n₀, with c > 0.", "Dividing by n: c·n ≤ 1, i.e. n ≤ 1/c.",
           "That fails for every n > max(n₀, 1/c) - so no c > 0 works."],
          "n can't stay above a fixed fraction of n².",
          ["For Ω you'd need c·n² ≤ n.", "Divide both sides by n.", "c·n ≤ 1 can't hold for all large n."]),
    prove("pf-f-t-nlog-n", 4, "pf_false", "n log2(n)", "n", "theta", False, None,
          ["Θ needs both bounds. The lower bound 1·n ≤ n log₂ n is fine for n ≥ 2.",
           "The upper bound fails: n log₂ n ≤ c·n would mean log₂ n ≤ c for every n ≥ n₀,",
           "but log₂ n exceeds c as soon as n > 2ᶜ."],
          "n log n is a bit faster than n - enough to break the upper bound.",
          ["Check the two halves of Θ separately.", "Which one fails: n log₂ n ≤ c·n, or c·n ≤ n log₂ n?",
           "Divide by n."]),
    prove("pf-f-t-n2-n3", 4, "pf_false", "n^2", "n^3", "theta", False, None,
          ["The upper bound n² ≤ 1·n³ holds, but the lower bound fails:",
           "c·n³ ≤ n² would mean c·n ≤ 1, i.e. n ≤ 1/c - false for every n > 1/c."],
          "n² is in O(n³) but not in Ω(n³).",
          ["Θ = O and Ω. Which one holds?", "Try c·n³ ≤ n².", "Divide by n²."]),
    prove("pf-f-w-5-log", 4, "pf_false", "5", "log2(n)", "omega", False, None,
          ["Suppose c·log₂ n ≤ 5 for every n ≥ n₀, with c > 0.",
           "Then log₂ n ≤ 5/c, i.e. n ≤ 2^(5/c) - false for every larger n."],
          "A constant can't keep up with even the slowest-growing log.",
          ["For Ω you'd need c·log₂ n ≤ 5.", "log₂ n grows without bound.", "So c·log₂ n eventually passes 5."]),
    prove("pf-f-3n-2n", 4, "pf_false", "3^n", "2^n", "O", False, None,
          ["Suppose 3ⁿ ≤ c·2ⁿ for every n ≥ n₀, i.e. (3/2)ⁿ ≤ c.",
           "(3/2)ⁿ is multiplied by 1.5 at every step, so it grows without bound and exceeds c eventually."],
          "Different exponential bases are different growth classes.",
          ["Divide both sides by 2ⁿ.", "What does (3/2)ⁿ do as n grows?", "No fixed c bounds it."]),
    prove("pf-o-100n-n2", 4, "pf_growth", "100n", "n^2", "O", True, {"c": 100, "n0": 1},
          ["For n ≥ 1: n ≤ n², so 100n ≤ 100n².",
           "(Another valid choice: c = 1 and n₀ = 100, since 100n ≤ n·n once n ≥ 100.)"],
          "A big coefficient doesn't make 100n grow faster than n².",
          ["Don't be fooled by the coefficient: is the claim true?", "Option 1: put the 100 into c.",
           "Option 2: c = 1, but then n₀ must be 100."]),
]

CONSTRUCT = [
    fill("pf-c-3n2", 2, "O", "3n + 2 ∈ O(n)", """
Prove:       3n + 2 ∈ O(n)
Goal:        3n + 2 ≤ [[0]] n
For n ≥ 1:   2 ≤ 2n
Therefore:   3n + 2 ≤ 3n + 2n = [[1]] n
So choose:   c = [[2]]   and   n₀ = [[3]]
Hence        3n + 2 ∈ O(n).
""", [{"accept": ["5", "c"], "show": "5"}, {"accept": ["5"]}, {"range": [5, 10 ** 9], "lo_open": False, "show": "5", "skill": "choose_c"},
      {"range": [1, 10 ** 9], "lo_open": False, "show": "1", "skill": "choose_n0"}],
        ["For n ≥ 1, 2 ≤ 2n, so 3n + 2 ≤ 3n + 2n = 5n.", "c = 5 and n₀ = 1 satisfy the definition (any c ≥ 5 works with n₀ = 1).",
         "Therefore 3n + 2 ∈ O(n)."],
        ["Add 3n + 2n.", "c is the coefficient you just found.", "The bound 2 ≤ 2n starts at n = 1."]),
    fill("pf-c-5n2", 2, "O", "5n² + 2n + 1 ∈ O(n²)", """
Prove:       5n² + 2n + 1 ∈ O(n²)
For n ≥ 1:   2n ≤ [[0]] n²     and     1 ≤ [[1]] n²
Therefore:   5n² + 2n + 1 ≤ 5n² + 2n² + n² = [[2]] n²
So choose:   c = [[3]]   and   n₀ = [[4]]
""", [{"accept": ["2"]}, {"accept": ["1"]}, {"accept": ["8"]}, {"range": [8, 10 ** 9], "lo_open": False, "show": "8", "skill": "choose_c"},
      {"range": [1, 10 ** 9], "lo_open": False, "show": "1", "skill": "choose_n0"}],
        ["For n ≥ 1: 2n ≤ 2n² and 1 ≤ n².", "So 5n² + 2n + 1 ≤ 8n²: c = 8, n₀ = 1."],
        ["n ≤ n² when n ≥ 1.", "Add the coefficients 5 + 2 + 1.", "Any c ≥ 8 works with n₀ = 1."]),
    fill("pf-c-omega", 2, "omega", "n² + 3n ∈ Ω(n²)", """
Prove:       n² + 3n ∈ Ω(n²)
For n ≥ 1:   3n ≥ [[0]]
Therefore:   n² + 3n ≥ n² = [[1]] · n²
So choose:   c = [[2]]   and   n₀ = [[3]]
""", [{"accept": ["0"]}, {"accept": ["1"]}, {"range": [0, 1], "show": "1", "skill": "choose_c"},
      {"range": [1, 10 ** 9], "lo_open": False, "show": "1", "skill": "choose_n0"}],
        ["3n ≥ 0, so n² + 3n ≥ 1·n².", "c = 1 (any 0 < c ≤ 1 works) and n₀ = 1."],
        ["3n is never negative for n ≥ 1.", "For a lower bound, dropping a non-negative term is allowed.", "c can be 1 or smaller."]),
    fill("pf-c-theta", 2, "theta", "3n² + 5n + 2 ∈ Θ(n²)", """
Prove:        3n² + 5n + 2 ∈ Θ(n²)       (needs a lower AND an upper bound)
Lower bound:  5n + 2 ≥ 0,  so  3n² + 5n + 2 ≥ [[0]] n²      →  c₁ = [[1]]
Upper bound:  for n ≥ 1,  5n ≤ 5n²  and  2 ≤ 2n²,
              so  3n² + 5n + 2 ≤ [[2]] n²                     →  c₂ = [[3]]
Both bounds hold for every n ≥ n₀ = [[4]],  so  3n² + 5n + 2 ∈ Θ(n²).
""", [{"accept": ["3"]}, {"range": [0, 3], "show": "3", "skill": "choose_c"}, {"accept": ["10"]},
      {"range": [10, 10 ** 9], "lo_open": False, "show": "10", "skill": "choose_c"},
      {"range": [1, 10 ** 9], "lo_open": False, "show": "1", "skill": "choose_n0"}],
        ["Lower: 3n² ≤ 3n² + 5n + 2, so c₁ = 3.", "Upper: 3n² + 5n + 2 ≤ 3n² + 5n² + 2n² = 10n², so c₂ = 10.",
         "Both for n ≥ 1, so Θ(n²)."],
        ["Lower bound: keep just the leading term.", "Upper bound: add the coefficients 3 + 5 + 2.", "Both bounds start at n = 1."]),
    fill("pf-c-nlog", 3, "O", "n log₂ n + 5n ∈ O(n log₂ n)", """
Prove:       n log₂ n + 5n ∈ O(n log₂ n)
For n ≥ 2:   log₂ n ≥ [[0]]
so           5n ≤ [[1]] · n log₂ n
Therefore:   n log₂ n + 5n ≤ [[2]] · n log₂ n
So choose:   c = [[3]]   and   n₀ = [[4]]
""", [{"accept": ["1"]}, {"accept": ["5"]}, {"accept": ["6"]}, {"range": [6, 10 ** 9], "lo_open": False, "show": "6", "skill": "choose_c"},
      {"range": [2, 10 ** 9], "lo_open": False, "show": "2", "skill": "choose_n0"}],
        ["For n ≥ 2, log₂ n ≥ 1, so 5n ≤ 5n log₂ n.", "Then n log₂ n + 5n ≤ 6 n log₂ n: c = 6, n₀ = 2.",
         "n₀ = 1 would fail: at n = 1, n log₂ n = 0 but 5n = 5."],
        ["log₂ 2 = 1.", "Multiply 1 ≤ log₂ n by 5n.", "n₀ = 1 doesn't work here - why?"]),
    fill("pf-c-log", 3, "O", "log₂ n ∈ O(n²)", """
Prove:       log₂ n ∈ O(n²)
For n ≥ 1:   log₂ n ≤ [[0]]          (because n ≤ 2ⁿ)
and          n ≤ [[1]]               (multiply 1 ≤ n by n)
So           log₂ n ≤ n² = [[2]] · n²
Choose:      c = [[3]]   and   n₀ = [[4]]
""", [{"accept": ["n"]}, {"accept": ["n^2"]}, {"accept": ["1"]}, {"range": [1, 10 ** 9], "lo_open": False, "show": "1", "skill": "choose_c"},
      {"range": [1, 10 ** 9], "lo_open": False, "show": "1", "skill": "choose_n0"}],
        ["log₂ n ≤ n ≤ n² for n ≥ 1, so c = 1 and n₀ = 1 work.",
         "Intuition (log n grows much more slowly than n²) suggested the claim; this chain of inequalities PROVES it."],
        ["Take log₂ of n ≤ 2ⁿ.", "n·n = n².", "No constant needed beyond 1."]),
    fill("pf-c-false", 4, "O", "n² ∉ O(n)", """
Claim:       n² ∈ O(n)   - show it is FALSE.
Suppose      n² ≤ c·n   for every n ≥ n₀   (some c > 0, n₀ > 0).
Divide by n: n ≤ [[0]]   for every n ≥ n₀.
Take         n = max(n₀, c) + 1.  This n is ≥ n₀, but n > [[1]] - a contradiction.
Example:     with c = 10 and n₀ = 1 the inequality first fails at n = [[2]].
So no constants exist and n² ∉ O(n).
""", [{"accept": ["c"], "skill": "disprove"}, {"accept": ["c"], "skill": "disprove"}, {"accept": ["11"], "skill": "disprove"}],
        ["n² ≤ c·n ⇔ n ≤ c (dividing by n > 0).", "No fixed c is ≥ every n, so the inequality fails for large n.",
         "With c = 10: 10² = 100 ≤ 100 still holds, 11² = 121 > 110 fails."],
        ["n²/n = n.", "The contradiction is with the same constant.", "Check n = 10 and n = 11."], disprove=True),
]

DEBUGS = [
    debug("pf-d-finite", 2, "O", "n² ∈ O(n)", """
Claim:   n² ∈ O(n)
Choose c = 10.
Then n² ≤ 10n.
Therefore n² ∈ O(n).
""", [{"id": "flaw", "kind": "choice", "label": "What is wrong with this proof?", "skill": "disprove",
       "options": ["n² ≤ 10n only holds up to n = 10 - Big O needs it for EVERY n ≥ n₀",
                   "c = 10 is too small; c = 100 would make the proof correct",
                   "A Big O proof must use c = 1", "Nothing - the proof is correct"],
       "answer": "n² ≤ 10n only holds up to n = 10 - Big O needs it for EVERY n ≥ n₀",
       "why": {"c = 10 is too small; c = 100 would make the proof correct": "n² ≤ 100n fails from n = 101 - every fixed c fails eventually.",
               "A Big O proof must use c = 1": "Any positive c is allowed.",
               "Nothing - the proof is correct": "Try n = 11: 121 > 110."}},
      {"id": "fail", "kind": "number", "label": "What is the first n where n² ≤ 10n fails?", "answer": 11, "skill": "choose_c"}],
        ["n² ≤ 10n ⇔ n ≤ 10, so it holds for n = 1 … 10 and fails from n = 11.",
         "Big O requires the inequality for ALL n ≥ n₀, not on a finite range - and since n²/n = n is unbounded, every c fails.",
         "So the claim is false."],
        ["Test n = 11.", "Would any larger c fix it?", "A finite range is never enough."]),
    debug("pf-d-reversed", 1, "O", "n ∈ O(n²)", """
Claim:   n ∈ O(n²)
Choose c = 1 and n₀ = 1.
For n ≥ 1:   n² ≤ 1·n.
So n ∈ O(n²).
""", [{"id": "flaw", "kind": "choice", "label": "What is wrong with this proof?",
       "options": ["The inequality is reversed: Big O needs n ≤ c·n² (and n² ≤ n is false for n ≥ 2)",
                   "n₀ must be 0", "c must be larger than 1", "Nothing - the proof is correct"],
       "answer": "The inequality is reversed: Big O needs n ≤ c·n² (and n² ≤ n is false for n ≥ 2)",
       "why": {"n₀ must be 0": "n₀ > 0 in the definition; n₀ = 1 is fine.",
               "c must be larger than 1": "c = 1 works for the CORRECT inequality n ≤ n².",
               "Nothing - the proof is correct": "At n = 2: 4 ≤ 2 is false."}}],
        ["f(n) ∈ O(g(n)) needs f(n) ≤ c·g(n): here n ≤ c·n², not n² ≤ c·n.",
         "With the right direction, c = 1 and n₀ = 1 work: n ≤ n² for n ≥ 1."],
        ["Which function goes on the small side for O?", "Try n = 2 in the written inequality.", "f ≤ c·g."]),
    debug("pf-d-intuition", 3, "O", "log₂ n ∈ O(n²)", """
Claim:   log₂ n ∈ O(n²)
log n grows much more slowly than n² - on a graph n² shoots up while log n stays almost flat.
Therefore log₂ n ∈ O(n²).
""", [{"id": "flaw", "kind": "choice", "label": "What is wrong with this proof?",
       "options": ["It is intuition only: no constants c, n₀ are given and no inequality is shown for every n ≥ n₀",
                   "The claim is false", "A graph is a formal proof if it covers large enough n",
                   "It should prove Θ instead of O"],
       "answer": "It is intuition only: no constants c, n₀ are given and no inequality is shown for every n ≥ n₀",
       "why": {"The claim is false": "The claim is true - only the argument is missing.",
               "A graph is a formal proof if it covers large enough n": "A graph shows finitely many points; the definition is about all n ≥ n₀.",
               "It should prove Θ instead of O": "log₂ n ∉ Θ(n²); O is the right claim."}},
      {"id": "fix", "kind": "choice", "label": "Which line proves the claim from the DEFINITION (constants c and n₀)?",
       "options": ["For n ≥ 1, log₂ n ≤ n ≤ n², so c = 1 and n₀ = 1 work",
                   "log₂ 1024 = 10 ≤ 1024² = 1,048,576",
                   "lim log₂ n / n² = 0"],
       "answer": "For n ≥ 1, log₂ n ≤ n ≤ n², so c = 1 and n₀ = 1 work",
       "why": {"log₂ 1024 = 10 ≤ 1024² = 1,048,576": "One value of n proves nothing about all n ≥ n₀.",
               "lim log₂ n / n² = 0": "That's a valid LIMIT argument - but it doesn't use c and n₀."}}],
        ["Intuition (growth comparison) suggests the claim but proves nothing.",
         "A definition proof gives c and n₀ and shows the inequality for every n ≥ n₀: log₂ n ≤ n ≤ n² for n ≥ 1.",
         "A limit argument (lim log₂ n / n² = 0) is a third, separate kind of argument."],
        ["Where are c and n₀?", "Is a picture a proof?", "Which option names constants?"]),
    debug("pf-d-theta-one", 2, "theta", "3n² + 5n ∈ Θ(n²)", """
Claim:   3n² + 5n ∈ Θ(n²)
For n ≥ 1, 5n ≤ 5n², so 3n² + 5n ≤ 8n².
Choose c = 8, n₀ = 1.
Therefore 3n² + 5n ∈ Θ(n²).
""", [{"id": "flaw", "kind": "choice", "label": "What is wrong with this proof?",
       "options": ["It only proves the upper bound (O); Θ also needs a lower bound c₁·n² ≤ 3n² + 5n",
                   "8 is not a valid constant", "The inequality 5n ≤ 5n² is false", "Nothing - the proof is correct"],
       "answer": "It only proves the upper bound (O); Θ also needs a lower bound c₁·n² ≤ 3n² + 5n",
       "why": {"8 is not a valid constant": "8 is a fine upper constant.",
               "The inequality 5n ≤ 5n² is false": "It's true for n ≥ 1.",
               "Nothing - the proof is correct": "You have proven an upper bound, but Θ requires both an upper and lower bound."}},
      {"id": "c1", "kind": "choice", "label": "Which constant completes the missing lower bound (for n ≥ 1)?", "skill": "choose_c",
       "options": ["c₁ = 3", "c₁ = 8", "c₁ = 4"], "answer": "c₁ = 3",
       "why": {"c₁ = 8": "8n² ≤ 3n² + 5n fails for n ≥ 2.", "c₁ = 4": "4n² ≤ 3n² + 5n fails for n ≥ 6."}}],
        ["You have proven an upper bound, but Θ requires both an upper and a lower bound.",
         "Lower bound: 5n ≥ 0, so 3n² ≤ 3n² + 5n - c₁ = 3 works for n ≥ 1.", "With c₁ = 3, c₂ = 8, n₀ = 1 the Θ proof is complete."],
        ["Θ = O AND Ω.", "Which half is shown?", "Drop the 5n for the lower bound."]),
    debug("pf-d-n0", 3, "O", "n³ ∈ O(2ⁿ)", """
Claim:   n³ ∈ O(2ⁿ)
Choose c = 1 and n₀ = 1.
For every n ≥ 1:   n³ ≤ 2ⁿ.
So n³ ∈ O(2ⁿ).
""", [{"id": "flaw", "kind": "choice", "label": "What is wrong with this proof?",
       "options": ["The claim is true, but n³ ≤ 2ⁿ is false for n = 2, …, 9 - n₀ = 1 is too small",
                   "The claim is false: 2ⁿ never catches up with n³", "c = 1 is too large", "Nothing - the proof is correct"],
       "answer": "The claim is true, but n³ ≤ 2ⁿ is false for n = 2, …, 9 - n₀ = 1 is too small",
       "why": {"The claim is false: 2ⁿ never catches up with n³": "From n = 10, 2ⁿ ≥ n³ (1024 ≥ 1000).",
               "c = 1 is too large": "A larger c can only help an upper bound.",
               "Nothing - the proof is correct": "At n = 2: 8 > 4."}},
      {"id": "n0", "kind": "number", "label": "With c = 1, what is the smallest valid integer n₀?", "answer": 10, "skill": "choose_n0"}],
        ["n³ ≤ 2ⁿ fails at n = 2 (8 > 4) through n = 9 (729 > 512).", "It holds from n = 10 (1000 ≤ 1024) on, so n₀ = 10.",
         "The choice of n₀ is part of the proof: the inequality must hold for EVERY n ≥ n₀."],
        ["Compute n³ and 2ⁿ for n = 2, 5, 9, 10.", "Where does 2ⁿ catch up?", "n₀ = 10."]),
    debug("pf-d-c-depends", 4, "O", "n² ∈ O(n)", """
Claim:   n² ∈ O(n)
For each n, choose c = n.
Then n² = n·n ≤ c·n.
So n² ∈ O(n).
""", [{"id": "flaw", "kind": "choice", "label": "What is wrong with this proof?", "skill": "disprove",
       "options": ["c must be ONE fixed constant chosen before n - here c changes with n",
                   "c = n is negative for small n", "The algebra n·n = n² is wrong", "Nothing - the proof is correct"],
       "answer": "c must be ONE fixed constant chosen before n - here c changes with n",
       "why": {"c = n is negative for small n": "n > 0, so c = n > 0 - positivity isn't the problem.",
               "The algebra n·n = n² is wrong": "The algebra is right; the logic isn't.",
               "Nothing - the proof is correct": "If c could depend on n, every function would be O(1)!"}}],
        ["The definition says: there EXIST constants c and n₀ such that for EVERY n ≥ n₀ … - c is fixed first.",
         "Letting c grow with n proves nothing; in fact n² ∉ O(n)."],
        ["Read the order of the quantifiers in the definition.", "Is c allowed to depend on n?", "With that trick everything would be O(1)."]),
    debug("pf-d-lower-big-c", 2, "omega", "n² + 3n ∈ Ω(n²)", """
Claim:   n² + 3n ∈ Ω(n²)
Choose c = 2 and n₀ = 1.
For n ≥ 1:   2n² ≤ n² + 3n.
So n² + 3n ∈ Ω(n²).
""", [{"id": "flaw", "kind": "choice", "label": "What is wrong with this proof?", "skill": "choose_c",
       "options": ["c = 2 is too large: 2n² ≤ n² + 3n means n² ≤ 3n, which fails for n > 3",
                   "Ω proofs need c ≥ 2", "The claim is false", "Nothing - the proof is correct"],
       "answer": "c = 2 is too large: 2n² ≤ n² + 3n means n² ≤ 3n, which fails for n > 3",
       "why": {"Ω proofs need c ≥ 2": "Any c > 0 is allowed; for a lower bound smaller c is easier.",
               "The claim is false": "c = 1 works: n² ≤ n² + 3n.",
               "Nothing - the proof is correct": "At n = 4: 32 > 28."}},
      {"id": "fail", "kind": "number", "label": "With c = 2, at which n does the inequality first fail?", "answer": 4, "skill": "choose_c"}],
        ["2n² ≤ n² + 3n ⇔ n² ≤ 3n ⇔ n ≤ 3 - true only on a finite range.",
         "For a lower bound, choose c no larger than the leading coefficient: c = 1 works for every n ≥ 1."],
        ["Subtract n² from both sides.", "Try n = 4.", "For Ω, a smaller c is safer."]),
    debug("pf-d-finite-test", 3, "O", "2ⁿ ∈ O(n³)", """
Claim:   2ⁿ ∈ O(n³)
We checked n = 1, 2, …, 9 and 2ⁿ ≤ 10·n³ every time.
So c = 10 and n₀ = 1 work, and 2ⁿ ∈ O(n³).
""", [{"id": "flaw", "kind": "choice", "label": "What is wrong with this proof?", "skill": "disprove",
       "options": ["Testing finitely many n proves nothing: 2ⁿ ≤ 10n³ fails for larger n, and the claim is false",
                   "They should have tested up to n = 20 to be sure", "c = 10 should be c = 1", "Nothing - the proof is correct"],
       "answer": "Testing finitely many n proves nothing: 2ⁿ ≤ 10n³ fails for larger n, and the claim is false",
       "why": {"They should have tested up to n = 20 to be sure": "No finite test is ever enough - and here it fails at n = 16.",
               "c = 10 should be c = 1": "No c works: 2ⁿ/n³ is unbounded.",
               "Nothing - the proof is correct": "At n = 16: 65,536 > 40,960."}},
      {"id": "fail", "kind": "number", "label": "What is the first n where 2ⁿ ≤ 10·n³ fails?", "answer": 16, "skill": "choose_c"}],
        ["Finite testing (tables, graphs) builds intuition but is never a proof.",
         "2ⁿ ≤ 10n³ first fails at n = 16 (65,536 > 40,960), and 2ⁿ/n³ grows without bound, so the claim is false."],
        ["Compute 2¹⁶ and 10·16³.", "Can any test of finitely many n prove a statement about ALL n ≥ n₀?", "What does 2ⁿ/n³ do?"]),
]

LIMITS = [
    limit("pf-l-log-n2", 3, "O", "log₂ n vs n²", """
n                1      2       4       8       16       32
log₂ n / n²      0      0.25    0.125   0.047   0.0156   0.0049
""", [{"id": "trend", "kind": "choice", "label": "As n grows, the ratio log₂ n / n² …",
       "options": ["shrinks toward 0", "approaches a positive constant", "grows without bound"], "answer": "shrinks toward 0"},
      {"id": "lim", "kind": "choice", "label": "lim (n→∞) log₂ n / n² =", "options": ["0", "1", "∞"], "answer": "0"},
      {"id": "rel", "kind": "multi", "label": "Which statements does this limit support?",
       "options": ["log₂ n ∈ O(n²)", "log₂ n ∈ Ω(n²)", "log₂ n ∈ Θ(n²)"], "answer": ["log₂ n ∈ O(n²)"]}],
        ["The table suggests the ratio shrinks - intuition, not proof.", "lim log₂ n / n² = 0 (e.g. by L'Hôpital: (1/(n ln 2))/(2n) → 0).",
         "A limit of 0 means f grows strictly slower: f ∈ O(g) but not Ω(g) or Θ(g)."],
        ["Read the table from left to right.", "The numerator grows very slowly.", "Limit 0 ⇒ O but not Ω."]),
    limit("pf-l-poly", 3, "theta", "3n² + 5n + 2 vs n²", """
(3n² + 5n + 2) / n²  =  3 + 5/n + 2/n²
n:      1      10      100      1000
ratio:  10     3.52    3.0502   3.005
""", [{"id": "lim", "kind": "choice", "label": "lim (n→∞) (3n² + 5n + 2)/n² =", "options": ["0", "3", "10", "∞"], "answer": "3"},
      {"id": "rel", "kind": "multi", "label": "Which statements does this limit support?",
       "options": ["3n² + 5n + 2 ∈ O(n²)", "3n² + 5n + 2 ∈ Ω(n²)", "3n² + 5n + 2 ∈ Θ(n²)"],
       "answer": ["3n² + 5n + 2 ∈ O(n²)", "3n² + 5n + 2 ∈ Ω(n²)", "3n² + 5n + 2 ∈ Θ(n²)"]}],
        ["5/n → 0 and 2/n² → 0, so the ratio → 3.", "A finite positive limit gives Θ - and therefore both O and Ω."],
        ["Divide each term by n².", "5/n and 2/n² vanish.", "0 < L < ∞ ⇒ Θ."]),
    limit("pf-l-2n-n3", 4, "O", "2ⁿ vs n³", """
n           5       10       20          40
2ⁿ / n³     0.26    1.02     131.07      17,179.9
""", [{"id": "lim", "kind": "choice", "label": "lim (n→∞) 2ⁿ / n³ =", "options": ["0", "a positive constant", "∞"], "answer": "∞"},
      {"id": "o", "kind": "choice", "label": "Can 2ⁿ ∈ O(n³) be proven?", "skill": "disprove",
       "options": ["No - the ratio exceeds every fixed c", "Yes, with c = 18,000", "Yes, with a large enough n₀"],
       "answer": "No - the ratio exceeds every fixed c",
       "why": {"Yes, with c = 18,000": "At n = 41 the ratio is already larger, and it keeps growing.",
               "Yes, with a large enough n₀": "A larger n₀ makes it worse: the ratio only grows."}},
      {"id": "rel", "kind": "multi", "label": "Which statements are true?",
       "options": ["2ⁿ ∈ O(n³)", "2ⁿ ∈ Ω(n³)", "2ⁿ ∈ Θ(n³)"], "answer": ["2ⁿ ∈ Ω(n³)"]}],
        ["The ratio starts below 1 but explodes: 2ⁿ/n³ → ∞.", "A limit of ∞ means f grows strictly faster: Ω only.",
         "So 2ⁿ ∈ O(n³) is FALSE - no constant c bounds the ratio."],
        ["Small n can mislead - look further right.", "Each step doubles the numerator.", "Limit ∞ ⇒ Ω but not O."]),
    limit("pf-l-nf-2n", 5, "O", "n! vs 2ⁿ", """
n!/2ⁿ = (1/2)·(2/2)·(3/2)·(4/2)···(n/2)
n:        2      4      8        16
n!/2ⁿ:    0.5    1.5    157.5    319,334,400
""", [{"id": "lim", "kind": "choice", "label": "lim (n→∞) n! / 2ⁿ =", "options": ["0", "1/2", "∞"], "answer": "∞"},
      {"id": "reason", "kind": "choice", "label": "Why?", "skill": "disprove",
       "options": ["Every factor k/2 with k ≥ 3 is > 1, and they keep getting larger",
                   "Because the table's last value is very large", "Because n! has more digits"],
       "answer": "Every factor k/2 with k ≥ 3 is > 1, and they keep getting larger",
       "why": {"Because the table's last value is very large": "A table is intuition; the product argument is the reason.",
               "Because n! has more digits": "Not a rigorous reason."}},
      {"id": "rel", "kind": "multi", "label": "Which statements are true?",
       "options": ["n! ∈ O(2ⁿ)", "n! ∈ Ω(2ⁿ)", "n! ∈ Θ(2ⁿ)"], "answer": ["n! ∈ Ω(2ⁿ)"]}],
        ["n!/2ⁿ is a product of factors k/2; from k = 3 every factor exceeds 1.5, so the product → ∞.",
         "So n! ∈ Ω(2ⁿ) but not O(2ⁿ) or Θ(2ⁿ)."],
        ["Write the ratio as a product.", "How big is each factor?", "Limit ∞ ⇒ Ω only."]),
    limit("pf-l-nlog-n", 5, "theta", "n log₂ n vs n", """
(n log₂ n) / n  =  log₂ n
n:       2     16     1024     2²⁰
ratio:   1     4      10       20
""", [{"id": "lim", "kind": "choice", "label": "lim (n→∞) (n log₂ n)/n =", "options": ["0", "1", "∞"], "answer": "∞"},
      {"id": "theta", "kind": "choice", "label": "So is n log₂ n ∈ Θ(n)?",
       "options": ["No - only the lower bound holds; the ratio log₂ n is unbounded",
                   "Yes - log₂ n grows so slowly it counts as a constant", "Yes, with c₂ = 20"],
       "answer": "No - only the lower bound holds; the ratio log₂ n is unbounded",
       "why": {"Yes - log₂ n grows so slowly it counts as a constant": "Slow growth is still unbounded growth.",
               "Yes, with c₂ = 20": "n log₂ n ≤ 20n fails once n > 2²⁰."}}],
        ["The ratio is log₂ n, which grows without bound (slowly!).", "So n log₂ n ∈ Ω(n) but not O(n) - hence not Θ(n)."],
        ["Simplify the ratio first.", "Is log₂ n bounded?", "Θ needs a bounded, positive ratio."]),
    limit("pf-l-kinds", 3, "O", "three kinds of argument", """
Four arguments about  log₂ n ∈ O(n²):
(a) log n grows much more slowly than n², as the graph shows.
(b) For n ≥ 1, log₂ n ≤ n ≤ n², so c = 1 and n₀ = 1 satisfy the definition.
(c) lim log₂ n / n² = 0, and a limit of 0 implies f ∈ O(g).
(d) The table shows log₂ n ≤ n² for n = 1, 2, 4, …, 1024.
""", [{"id": "a", "kind": "choice", "label": "(a) is …", "options": ["intuition (not a proof)", "a proof from the definition", "a limit argument"],
       "answer": "intuition (not a proof)"},
      {"id": "b", "kind": "choice", "label": "(b) is …", "options": ["intuition (not a proof)", "a proof from the definition", "a limit argument"],
       "answer": "a proof from the definition", "skill": "choose_c"},
      {"id": "c", "kind": "choice", "label": "(c) is …", "options": ["intuition (not a proof)", "a proof from the definition", "a limit argument"],
       "answer": "a limit argument"},
      {"id": "d", "kind": "choice", "label": "(d) is …", "options": ["intuition (not a proof)", "a proof from the definition", "a limit argument"],
       "answer": "intuition (not a proof)"}],
        ["(a) and (d) build intuition: a graph or table covers finitely many n.",
         "(b) proves the claim from the definition by exhibiting c and n₀.",
         "(c) is a different rigorous route, via the limit theorem."],
        ["Does the argument mention c and n₀?", "Does it cover ALL n ≥ n₀?", "A limit is a separate tool."],
        prompt="Classify each argument. Only some of them are proofs - and they are different kinds of proof."),
    limit("pf-l-theorem", 5, "theta", "the limit test", """
Suppose  L = lim (n→∞) f(n)/g(n)  exists (f, g positive).
""", [{"id": "zero", "kind": "multi", "label": "If L = 0, which hold?", "options": ["f ∈ O(g)", "f ∈ Ω(g)", "f ∈ Θ(g)"],
       "answer": ["f ∈ O(g)"]},
      {"id": "pos", "kind": "multi", "label": "If 0 < L < ∞, which hold?", "options": ["f ∈ O(g)", "f ∈ Ω(g)", "f ∈ Θ(g)"],
       "answer": ["f ∈ O(g)", "f ∈ Ω(g)", "f ∈ Θ(g)"]},
      {"id": "inf", "kind": "multi", "label": "If L = ∞, which hold?", "options": ["f ∈ O(g)", "f ∈ Ω(g)", "f ∈ Θ(g)"],
       "answer": ["f ∈ Ω(g)"]},
      {"id": "c", "kind": "choice", "label": "If 0 < L < ∞, which c always works for the upper bound (with a large enough n₀)?",
       "skill": "choose_c", "options": ["any c > L", "c = L/2", "only c = L"], "answer": "any c > L",
       "why": {"c = L/2": "Eventually f/g is close to L > L/2, so f ≤ (L/2)·g fails.",
               "only c = L": "c = L may or may not work; every c > L does."}}],
        ["L = 0 ⇒ O only; 0 < L < ∞ ⇒ Θ (so O and Ω); L = ∞ ⇒ Ω only.",
         "Why: if f/g → L then eventually f/g < L + 1, i.e. f ≤ (L + 1)·g - exactly the definition with c = L + 1."],
        ["f/g → 0 means f is eventually tiny compared with g.", "A positive finite limit pins f between two multiples of g.",
         "Eventually f/g < c for any c > L."], prompt="The limit test turns a ratio into a conclusion. Make sure you know which."),
]

EXERCISES = PROOFS + CONSTRUCT + DEBUGS + LIMITS
