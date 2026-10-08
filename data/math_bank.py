"""Discrete Math Foundations exercise bank: the algebra that algorithm analysis leans on.

Every exercise is built on the multiple-part system. Answer kinds graded by engine.mathfound:
    expr      an expression, accepted in any equivalent form (optionally in a required form)
    work      shown working, one transformation per line - every line must equal the start
    theta     an asymptotic class Θ(g)
    constant  a witness C, checked against the definition
plus the usual choice / number parts. The test suite checks every answer, trap, model line and constant.
Variety matters more than volume: each item exercises a different rule, pitfall or shape of expression.
"""

EXP_RULES = ["Product rule: aᵐ · aⁿ = aᵐ⁺ⁿ", "Quotient rule: aᵐ / aⁿ = aᵐ⁻ⁿ", "Power of a power: (aᵐ)ⁿ = aᵐⁿ",
             "Power of a product: (ab)ⁿ = aⁿbⁿ", "Negative exponent: a⁻ⁿ = 1/aⁿ"]
LOG_RULES = ["Product rule: log(xy) = log x + log y", "Quotient rule: log(x/y) = log x − log y",
             "Power rule: log(xᵏ) = k · log x", "Inverse rule: log₂(2ˣ) = x", "Change of base: log_b x = log x / log b"]
ALG_RULES = ["Distribute: a(b + c) = ab + ac", "Combine like terms", "Factor out a common factor", "Expand a product of brackets (FOIL)"]
VALID = ["Valid", "Invalid"]
INPUT_NOTE = ("Type answers with ^ for powers, * or a space for multiplication, and log(...) for log base 2 "
              "(ln for natural log, log10 for base 10). Any equivalent form is accepted unless the step asks for a specific form.")

EXERCISES = []


# ============================================================================ part builders
def expr(label, answer, form=None, traps=(), skill=None):
    p = {"kind": "expr", "label": label, "answer": answer}
    if form:
        p["form"] = form
    if traps:
        p["traps"] = [list(t) for t in traps]
    if skill:
        p["skill"] = skill
    return p


def work(label, start, model, min_lines=2):
    return {"kind": "work", "label": label, "start": start, "model": list(model), "answer": model[-1], "min_lines": min_lines}


def theta(label, answer):
    return {"kind": "theta", "label": label, "answer": answer, "wrap": "Θ"}


def const(label, f, g, n0, answer, side="upper"):
    return {"kind": "constant", "label": label, "f": f, "g": g, "n0": n0, "answer": answer, "side": side}


def choice(label, options, answer, why=None, skill=None):
    p = {"kind": "choice", "wrap": "", "label": label, "options": list(options), "answer": answer}
    if why:
        p["why"] = dict(why)
    if skill:
        p["skill"] = skill
    return p


def num(label, answer):
    return {"kind": "number", "label": label, "answer": answer}


def order(label, options, answer):
    return {"kind": "order", "label": label, "options": list(options), "answer": list(answer)}


def _ex(id, topic, type_, level, title, prompt, parts, hints, steps, formula=None, code="", staged=False,
        proof_text=None, note=None, skills=None):
    for i, p in enumerate(parts, start=1):
        p.setdefault("id", f"p{i}")
    ex = {"id": id, "track": "math", "type": type_, "topic": topic, "level": level, "title": title,
          "prompt": prompt, "formula": formula, "code": code, "parts": parts, "staged": staged,
          "hints": list(hints), "steps": list(steps), "note": note, "highlights": [],
          "proof_text": proof_text, "tags": ["math", topic]}
    if skills:
        ex["skills"] = list(skills)
    EXERCISES.append(ex)
    return ex


def simp(id, topic, level, title, formula, answer, form=None, traps=(), hints=(), steps=(), prompt=None,
         label="Simplified form", extra=(), skills=None):
    return _ex(id, topic, "math_simplify", level, title, prompt or f"Simplify. {INPUT_NOTE}",
               [expr(label, answer, form, traps)] + list(extra), hints, steps, formula=formula, skills=skills)


def rule(id, topic, level, formula, options, rule_answer, answer, form=None, traps=(), why=None, hints=(), steps=(),
         title=None, label="Apply it: the result"):
    return _ex(id, topic, "math_rule", level, title or f"What rule do I use? {formula}",
               "First decide which rule applies - then apply it. " + INPUT_NOTE,
               [choice("Which rule do you use first?", options, rule_answer, why), expr(label, answer, form, traps)],
               hints, steps, formula=formula)


def staged(id, topic, level, title, formula, parts, hints, steps, prompt=None):
    return _ex(id, topic, "math_steps", level, title,
               prompt or "Step-by-step: choose the rule, then make one transformation at a time. Each step is checked before the next unlocks. " + INPUT_NOTE,
               parts, hints, steps, formula=formula, staged=True)


def valid(id, topic, level, claim, is_valid, reasons, reason, hints=(), steps=(), verdict_why=None, title=None):
    return _ex(id, topic, "math_valid", level, title or f"Valid or invalid? {claim}",
               "Decide whether the statement is valid for all allowed values, then pick the reason.",
               [choice("Valid or invalid?", VALID, "Valid" if is_valid else "Invalid", verdict_why),
                choice("Why?", reasons, reason)], hints, steps, formula=claim)


def mistake(id, topic, level, title, lines, bad, fix, form=None, hints=(), steps=(), traps=(), prompt=None, label=None):
    text = "\n".join(f"Line {i}:  {ln}" for i, ln in enumerate(lines, start=1))
    return _ex(id, topic, "math_mistake", level, f"Find the mistake: {title}",
               prompt or "One line of this work misapplies a rule. Find the FIRST incorrect line, then write what that line should say. " + INPUT_NOTE,
               [choice("Which line contains the first mistake?", [f"Line {i}" for i in range(1, len(lines) + 1)], f"Line {bad}"),
                expr(label or f"Correct version of line {bad}", fix, form, traps)], hints, steps, proof_text=text)


def apply(id, topic, level, title, parts, hints, steps, code="", formula=None, prompt=None, skills=None):
    return _ex(id, topic, "math_apply", level, title,
               prompt or "Algorithm analysis application: identify the pattern, choose the formula, simplify, then give the growth rate. " + INPUT_NOTE,
               parts, hints, steps, code=code, formula=formula, skills=skills)


def shown(id, topic, level, title, formula, start, model, final, form=None, hints=(), extra=(), traps=(), min_lines=2):
    return _ex(id, topic, "math_work", level, title,
               "Simplify, showing your work: write one transformation per line (each line must equal the original). "
               "Then give the final simplified form. " + INPUT_NOTE,
               [work("Your working (one step per line)", start, model, min_lines), expr("Final simplified form", final, form, traps)]
               + list(extra), hints, ["Start: " + formula] + [f"= {m}" for m in model], formula=formula)


def bound(id, topic, level, title, formula, parts, hints, steps, prompt=None):
    return _ex(id, topic, "math_bound", level, title,
               prompt or "Inequalities: choose a constant that makes the inequality true for every n from the given n₀ on. Any valid constant is accepted.",
               parts, hints, steps, formula=formula)


# ============================================================================ Algebra fundamentals / distribution
simp("mf_alg_dist1", "math_algebra", 1, "Distribute a constant", "3(n + 4)", "3n + 12", "expanded",
     traps=[("3n + 4", "Distribute to EVERY term inside the bracket: 3·n and 3·4.")],
     hints=["Distribution: a(b + c) = ab + ac.", "Multiply 3 by n, then 3 by 4."], steps=["3(n + 4) = 3·n + 3·4", "= 3n + 12"])
simp("mf_alg_dist2", "math_algebra", 1, "Distribute a negative", "−2(x − 5)", "-2x + 10", "expanded",
     traps=[("-2x - 10", "(−2)·(−5) = +10: a negative times a negative is positive."), ("-2x - 5", "The −2 multiplies the 5 as well.")],
     hints=["Multiply −2 by each term, keeping signs.", "(−2)·x = −2x and (−2)·(−5) = ?"], steps=["−2(x − 5) = (−2)·x + (−2)·(−5)", "= −2x + 10"])
simp("mf_alg_foil", "math_algebra", 2, "Expand two brackets", "(n + 1)(n + 2)", "n^2 + 3n + 2", "expanded",
     traps=[("n^2 + 2", "Don't forget the cross terms n·2 and 1·n."), ("n^2 + 3n + 3", "The constant term is 1·2 = 2.")],
     hints=["Every term in the first bracket multiplies every term in the second.", "n·n + n·2 + 1·n + 1·2, then combine like terms."],
     steps=["(n + 1)(n + 2) = n·n + n·2 + 1·n + 1·2", "= n² + 2n + n + 2", "= n² + 3n + 2"])
simp("mf_alg_square", "math_algebra", 2, "Square a binomial", "(n − 1)²", "n^2 - 2n + 1", "expanded",
     traps=[("n^2 - 1", "(a − b)² ≠ a² − b². Write it as (n − 1)(n − 1) and expand."), ("n^2 + 1", "(a − b)² ≠ a² + b²: the middle term −2n is missing.")],
     hints=["(n − 1)² means (n − 1)(n − 1).", "(a − b)² = a² − 2ab + b²."], steps=["(n − 1)² = (n − 1)(n − 1)", "= n² − n − n + 1", "= n² − 2n + 1"])
simp("mf_alg_minus_bracket", "math_algebra", 1, "Subtract a bracket", "5 − (n − 3)", "8 - n", "expanded",
     traps=[("2 - n", "Subtracting a bracket flips EVERY sign inside: −(n − 3) = −n + 3.")],
     hints=["−(n − 3) = −1·(n − 3).", "−1·n = −n and −1·(−3) = +3."], steps=["5 − (n − 3) = 5 − n + 3", "= 8 − n"])
simp("mf_alg_two_dist", "math_algebra", 2, "Two distributions", "2(3n − 1) − 3(n − 2)", "3n + 4", "combined",
     traps=[("3n - 8", "−3·(−2) = +6, not −6."), ("3n - 4", "Check both constants: 2·(−1) = −2 and −3·(−2) = +6.")],
     hints=["Distribute each bracket separately, watching the sign in front of the 3.", "6n − 2 − 3n + 6, then combine."],
     steps=["2(3n − 1) − 3(n − 2) = 6n − 2 − 3n + 6", "= 3n + 4"])
rule("mf_alg_rule_factor", "math_algebra", 2, "4n² + 8n  (write it as a product)", ALG_RULES, ALG_RULES[2], "4n(n + 2)", "factored",
     traps=[("4n(n + 8)", "Each term must be divided by the common factor: 8n ÷ 4n = 2.")],
     why={ALG_RULES[0]: "Distribution goes the other way (product → sum). Here you want sum → product."},
     hints=["Which factor do both terms share?", "Both terms contain 4n."], steps=["4n² + 8n = 4n·n + 4n·2", "= 4n(n + 2)"])
valid("mf_alg_valid_sq", "math_algebra", 2, "(a + b)² = a² + b²", False,
      ["It is missing the cross term 2ab", "Exponents distribute over addition", "It only fails for negative numbers"],
      "It is missing the cross term 2ab", hints=["Try a = b = 1.", "(1 + 1)² = 4, but 1² + 1² = 2."],
      steps=["(a + b)² = (a + b)(a + b) = a² + 2ab + b².", "So the claim drops 2ab - invalid (a = b = 1 gives 4 ≠ 2)."])
mistake("mf_alg_mistake1", "math_algebra", 2, "distributing a subtraction", ["4(n + 2) − (n − 1)", "= 4n + 8 − n − 1", "= 3n + 7"], 2,
        "4n + 8 - n + 1", traps=[("4n + 8 - n - 1", "That's the line as written - look at the sign of the 1.")],
        hints=["Check each sign when the bracket (n − 1) is subtracted.", "−(n − 1) = −n + 1."],
        steps=["Line 2 should be 4n + 8 − n + 1 (subtracting −1 gives +1).", "Then line 3 becomes 3n + 9."])
apply("mf_alg_apply", "math_algebra", 2, "A loop with setup work",
      [expr("Write T(n) = 3(n − 1) + 2 in expanded form", "3n - 1", "expanded"), theta("Growth rate of T(n)", "n")],
      ["Distribute the 3 over (n − 1).", "3n − 3 + 2; keep the dominant term for Θ."],
      ["T(n) = 3(n − 1) + 2 = 3n − 3 + 2 = 3n − 1", "Dominant term 3n, drop the constant 3: Θ(n)."],
      code="total := 0          // 2 setup steps\nfor i := 2 to n\n    3 basic steps", prompt=(
          "The loop body runs n − 1 times with 3 steps each, plus 2 setup steps, so T(n) = 3(n − 1) + 2. " + INPUT_NOTE))

# ============================================================================ Exponent rules
rule("mf_exp_product", "math_exp", 1, "x² · x³", EXP_RULES, EXP_RULES[0], "x^5", "power",
     traps=[("x^6", "Multiplying powers with the same base ADDS exponents. x⁶ would be (x²)³.")],
     why={EXP_RULES[2]: "Power of a power is for (x²)³ - a power raised to a power. Here two powers are multiplied."},
     hints=["Same base, multiplied.", "aᵐ · aⁿ = aᵐ⁺ⁿ: 2 + 3."], steps=["Same base x, multiplication → add exponents.", "x² · x³ = x²⁺³ = x⁵"])
rule("mf_exp_powpow", "math_exp", 1, "(x²)³", EXP_RULES, EXP_RULES[2], "x^6", "power",
     traps=[("x^5", "That would be x² · x³. A power raised to a power MULTIPLIES exponents.")],
     why={EXP_RULES[0]: "The product rule needs two powers multiplied together, like x² · x³."},
     hints=["A power is being raised to another power.", "(aᵐ)ⁿ = aᵐ·ⁿ: 2 · 3."], steps=["(x²)³ = x² · x² · x²", "= x²·³ = x⁶"])
rule("mf_exp_quot", "math_exp", 1, "x⁷ / x³", EXP_RULES, EXP_RULES[1], "x^4", "power",
     traps=[("x^(7/3)", "Dividing powers SUBTRACTS exponents; it doesn't divide them."), ("x^10", "That adds the exponents - division subtracts.")],
     hints=["Same base, divided.", "aᵐ / aⁿ = aᵐ⁻ⁿ: 7 − 3."], steps=["x⁷ / x³ = x⁷⁻³", "= x⁴"])
rule("mf_exp_double_sq", "math_exp", 2, "(2ⁿ)²", EXP_RULES, EXP_RULES[2], "2^(2n)", "power",
     traps=[("2^(n^2)", "(2ⁿ)² multiplies the exponents: n · 2 = 2n, not n²."), ("2^(n+2)", "Exponents multiply here, not add."),
            ("2*2^n", "Squaring is not doubling: (2ⁿ)² = 2ⁿ · 2ⁿ.")],
     hints=["It's a power raised to the power 2.", "(aᵐ)ⁿ = aᵐⁿ, so (2ⁿ)² = 2^(n·2)."],
     steps=["(2ⁿ)² = 2ⁿ·² = 2²ⁿ", "Equivalently 4ⁿ, since 2²ⁿ = (2²)ⁿ."])
simp("mf_exp_same_base_n", "math_exp", 2, "Multiply 2ⁿ by itself", "2ⁿ · 2ⁿ", "2^(2n)", "power",
     traps=[("2^(n^2)", "Multiplying powers ADDS exponents: n + n = 2n."), ("4^(2n)", "Keep the base 2 and add exponents: 2ⁿ⁺ⁿ."),
            ("2*2^n", "2ⁿ · 2ⁿ is a square, not 2ⁿ + 2ⁿ.")],
     hints=["Product rule: same base, add exponents.", "n + n = ?"], steps=["2ⁿ · 2ⁿ = 2ⁿ⁺ⁿ", "= 2²ⁿ (= 4ⁿ)"])
rule("mf_exp_split_plus", "math_exp", 2, "2ⁿ⁺¹  (rewrite as a multiple of 2ⁿ)", EXP_RULES, EXP_RULES[0], "2*2^n", "split_exp",
     traps=[("2^n + 1", "2ⁿ⁺¹ = 2ⁿ · 2¹, not 2ⁿ + 1."), ("2^n + 2", "Read the product rule backwards: 2ⁿ⁺¹ = 2ⁿ · 2.")],
     title="What rule do I use? Rewrite 2ⁿ⁺¹ in terms of 2ⁿ", label="2ⁿ⁺¹ written as (constant) · 2ⁿ",
     hints=["Read the product rule backwards: aᵐ⁺ⁿ = aᵐ · aⁿ.", "2ⁿ⁺¹ = 2ⁿ · 2¹."], steps=["2ⁿ⁺¹ = 2ⁿ · 2¹", "= 2 · 2ⁿ"])
simp("mf_exp_split_minus", "math_exp", 2, "Rewrite 2ⁿ⁻¹", "2ⁿ⁻¹", "2^n/2", "split_exp", label="2ⁿ⁻¹ written in terms of 2ⁿ",
     traps=[("2^n - 1", "2ⁿ⁻¹ is HALF of 2ⁿ, not 2ⁿ minus 1."), ("2*2^n", "Subtracting 1 in the exponent divides by 2.")],
     hints=["Quotient rule backwards: aᵐ⁻ⁿ = aᵐ / aⁿ.", "2ⁿ⁻¹ = 2ⁿ / 2¹."], steps=["2ⁿ⁻¹ = 2ⁿ / 2¹", "= 2ⁿ / 2  (= ½ · 2ⁿ)"])
rule("mf_exp_negative", "math_exp", 1, "x⁻³  (write with a positive exponent)", EXP_RULES, EXP_RULES[4], "1/x^3", "positive_exp",
     traps=[("-x^3", "A negative exponent means a reciprocal, not a negative number."), ("-3x", "x⁻³ is 1/x³.")],
     hints=["A negative exponent flips the power into the denominator.", "a⁻ⁿ = 1/aⁿ."], steps=["x⁻³ = 1 / x³"])
rule("mf_exp_product_power", "math_exp", 2, "(3x²y)²", EXP_RULES, EXP_RULES[3], "9x^4y^2", "monomial",
     traps=[("3x^4y^2", "The coefficient is squared too: 3² = 9."), ("9x^4y", "y is inside the bracket, so it is squared too.")],
     hints=["Every factor inside the bracket gets the exponent 2.", "3² · (x²)² · y²."], steps=["(3x²y)² = 3² · (x²)² · y²", "= 9x⁴y²"])
staged("mf_exp_steps1", "math_exp", 2, "Step by step: (x³ · x⁵) / x²", "(x³ · x⁵) / x²", [
    choice("Step 1 · Which rule simplifies the numerator x³ · x⁵?", EXP_RULES, EXP_RULES[0]),
    expr("Step 2 · The numerator after that rule", "x^8", "power", [("x^15", "Multiplying powers ADDS exponents: 3 + 5.")]),
    choice("Step 3 · Which rule handles x⁸ / x²?", EXP_RULES, EXP_RULES[1]),
    expr("Step 4 · Final result", "x^6", "power", [("x^4", "8 − 2 = 6."), ("x^10", "Division subtracts exponents.")])],
    ["Work on the numerator first.", "x³ · x⁵ = x⁸; then divide by x²."], ["x³ · x⁵ = x³⁺⁵ = x⁸  (product rule)", "x⁸ / x² = x⁸⁻² = x⁶  (quotient rule)"])
valid("mf_exp_valid_sum", "math_exp", 2, "2ⁿ + 2ⁿ = 4ⁿ", False,
      ["2ⁿ + 2ⁿ = 2 · 2ⁿ = 2ⁿ⁺¹, which is far smaller than 4ⁿ", "Adding powers multiplies the bases", "It is valid only for n = 1"],
      "2ⁿ + 2ⁿ = 2 · 2ⁿ = 2ⁿ⁺¹, which is far smaller than 4ⁿ",
      hints=["Adding two equal things doubles them.", "Try n = 3: 8 + 8 = 16, but 4³ = 64."],
      steps=["2ⁿ + 2ⁿ = 2 · 2ⁿ = 2ⁿ⁺¹.", "4ⁿ = 2²ⁿ. These are equal only at n = 1, so the claim is invalid."])
valid("mf_exp_valid_mul", "math_exp", 2, "2ⁿ · 3ⁿ = 6ⁿ", True,
      ["Power of a product: aⁿbⁿ = (ab)ⁿ", "Product rule: add the bases", "It is invalid because the bases differ"],
      "Power of a product: aⁿbⁿ = (ab)ⁿ", hints=["The exponents match, the bases differ.", "Read (ab)ⁿ = aⁿbⁿ backwards."],
      steps=["Same exponent n: 2ⁿ · 3ⁿ = (2 · 3)ⁿ = 6ⁿ - valid."])
mistake("mf_exp_mistake", "math_exp", 2, "a power of a product", ["(x²y³)² · x", "= x⁴y⁵ · x", "= x⁵y⁵"], 2, "x^4*y^6*x",
        traps=[("x^4*y^5*x", "Look at y: (y³)² - do you add or multiply the exponents?")],
        hints=["Check what happened to y³ when squared.", "(y³)² = y³·² = y⁶ - exponents multiply."],
        steps=["Line 2 should be x⁴y⁶ · x - power of a power multiplies: (y³)² = y⁶.", "Then line 3 is x⁵y⁶."])
apply("mf_exp_apply", "math_exp", 3, "Comparing exponential step counts", [
    expr("Algorithm A does 2ⁿ⁺² steps. Write it as (constant) · 2ⁿ", "4*2^n", "split_exp", [("2^n + 2", "2ⁿ⁺² = 2ⁿ · 2².")]),
    choice("Algorithm B does 4 · 2ⁿ steps. Compare A and B.", ["They do exactly the same number of steps", "A does more steps", "B does more steps"],
           "They do exactly the same number of steps"),
    theta("Growth rate of both", "2^n")],
    ["Split the exponent with the product rule.", "2ⁿ⁺² = 2ⁿ · 2² = 4 · 2ⁿ."], ["2ⁿ⁺² = 2² · 2ⁿ = 4 · 2ⁿ - identical to B.", "Constant factors don't change the class: Θ(2ⁿ)."])
simp("mf_exp_cube_double", "math_exp", 3, "Cube of a power of 2", "(2ⁿ)³ / 2ⁿ", "2^(2n)", "power",
     traps=[("2^(n^3)", "(2ⁿ)³ = 2³ⁿ: multiply exponents n · 3."), ("2^(3n)", "You still have to divide by 2ⁿ.")],
     hints=["First (2ⁿ)³ with power of a power.", "2³ⁿ / 2ⁿ: subtract exponents."], steps=["(2ⁿ)³ = 2³ⁿ", "2³ⁿ / 2ⁿ = 2³ⁿ⁻ⁿ = 2²ⁿ"])

# ============================================================================ Logarithm rules
LOG_NOTE = "Here log means log base 2."
rule("mf_log_power1", "math_log", 1, "log(n²)", LOG_RULES, LOG_RULES[2], "2log(n)", "log_simple",
     traps=[("log(n)^2", "log(n²) = 2 log n. (log n)² is a different function - the square of the log.")],
     why={LOG_RULES[0]: "There is no product inside the log, only a power."}, hints=["The exponent sits inside the log.", "log(xᵏ) = k log x."],
     steps=["log(n²) = 2 · log n  (power rule)"])
simp("mf_log_xlogx4", "math_log", 1, "Pull an exponent out", "x · log(x⁴)", "4x log(x)", "log_simple",
     traps=[("x*log(4*x)", "The exponent comes OUT as a multiplier: log(x⁴) = 4 log x, not log(4x)."),
            ("x*log(x)^4", "log(x⁴) is not (log x)⁴.")],
     hints=["Power rule: log(xᵏ) = k log x.", "x · 4 log x - now tidy the coefficient."], steps=["x · log(x⁴) = x · 4 log x", "= 4x log x"])
simp("mf_log_nlogn3", "math_log", 1, "n log(n³)", "n · log(n³)", "3n log(n)", "log_simple",
     traps=[("n*log(3*n)", "log(n³) = 3 log n: the exponent multiplies the log."), ("n^3*log(n)", "Only the argument of the log was cubed.")],
     hints=["Apply the power rule inside.", "n · 3 log n."], steps=["n log(n³) = n · 3 log n = 3n log n"])
simp("mf_log_n2logn5", "math_log", 2, "n² log(n⁵)", "n² · log(n⁵)", "5n^2 log(n)", "log_simple",
     traps=[("n^10*log(n)", "The 5 belongs to the log's argument; it comes out as a factor of the log, not of n²."),
            ("n^2*log(5*n)", "Power rule: log(n⁵) = 5 log n.")],
     hints=["Only the argument n⁵ changes.", "log(n⁵) = 5 log n."], steps=["n² log(n⁵) = n² · 5 log n = 5n² log n"])
rule("mf_log_inverse", "math_log", 1, "log₂(2ⁿ)", LOG_RULES, LOG_RULES[3], "n",
     traps=[("n*log(n)", "log₂(2ⁿ) asks: 2 to what power gives 2ⁿ? Just n.")],
     why={LOG_RULES[2]: "The power rule gives n · log₂ 2 = n · 1 - the same answer, the long way."},
     hints=["log₂ undoes 2^(…).", "2 to the power n is 2ⁿ."], steps=["log₂(2ⁿ) = n · log₂ 2 = n · 1 = n"])
simp("mf_log_ln2n", "math_log", 2, "A log of 2ⁿ in another base", "ln(2ⁿ)", "n ln(2)", "log_simple",
     traps=[("n", "That's log₂(2ⁿ). In base e, the factor ln 2 stays."), ("ln(2*n)", "The exponent n comes out in front.")],
     prompt="Simplify (ln is the natural log). " + INPUT_NOTE, hints=["Power rule works in every base.", "ln(2ⁿ) = n · ln 2."],
     steps=["ln(2ⁿ) = n · ln 2  (≈ 0.693n)", "Compare: log₂(2ⁿ) = n · log₂ 2 = n."])
rule("mf_log_product", "math_log", 2, "log(8n)", LOG_RULES, LOG_RULES[0], "3 + log(n)", "log_simple",
     traps=[("8*log(n)", "8 is a FACTOR, not an exponent: log(8n) = log 8 + log n."), ("log(8)*log(n)", "log(xy) = log x + log y, not a product.")],
     why={LOG_RULES[2]: "There's no exponent: 8n is a product."}, hints=["8n is a product inside the log.", "log 8 + log n, and log₂ 8 = 3."],
     steps=["log(8n) = log 8 + log n  (product rule)", "= 3 + log n  (2³ = 8)"])
rule("mf_log_quotient", "math_log", 2, "log(n/4)", LOG_RULES, LOG_RULES[1], "log(n) - 2", "log_simple",
     traps=[("log(n)/2", "log(n/4) = log n − log 4. Logs turn division into SUBTRACTION, not division.")],
     hints=["A quotient inside a log.", "log n − log 4, and log₂ 4 = 2."], steps=["log(n/4) = log n − log 4  (quotient rule)", "= log n − 2"])
staged("mf_log_steps1", "math_log", 2, "Step by step: log(n³ · 2ⁿ)", "log(n³ · 2ⁿ)", [
    choice("Step 1 · Which rule do you apply first?", LOG_RULES, LOG_RULES[0]),
    expr("Step 2 · After splitting the product", "log(n^3) + log(2^n)", traps=[("log(n^3)*log(2^n)", "The product rule gives a SUM of logs.")]),
    choice("Step 3 · Which rule simplifies each piece now?", LOG_RULES, LOG_RULES[2]),
    expr("Step 4 · Final simplified form", "3log(n) + n", "log_simple", [("3*n*log(n)", "The two pieces are added: 3 log n + n.")])],
    ["Split the product first.", "Then log(n³) = 3 log n and log(2ⁿ) = n."],
    ["log(n³ · 2ⁿ) = log(n³) + log(2ⁿ)  (product rule)", "= 3 log n + n log 2 = 3 log n + n  (power rule, log₂ 2 = 1)"])
simp("mf_log_x2y3", "math_log", 2, "Expand a log of a product of powers", "log(x² y³)", "2log(x) + 3log(y)", "log_simple",
     traps=[("6*log(x*y)", "Each factor keeps its own exponent: 2 log x + 3 log y."), ("log(x)^2 + log(y)^3", "log(x²) = 2 log x, not (log x)².")],
     hints=["Product rule first, then the power rule on each piece.", "log(x²) + log(y³)."], steps=["log(x²y³) = log(x²) + log(y³)", "= 2 log x + 3 log y"])
simp("mf_log_change_base", "math_log", 3, "Change of base", "log₈ n", "log(n)/3", label="log₈ n written using log₂ (type log(n) for log₂ n)",
     traps=[("3*log(n)", "log₂ n = 3 · log₈ n, so log₈ n = log₂ n ÷ 3 - you multiplied instead.")],
     prompt="Change of base: log_b x = log₂ x / log₂ b. " + INPUT_NOTE,
     hints=["log₈ n = log₂ n / log₂ 8.", "log₂ 8 = 3."], steps=["log₈ n = log₂ n / log₂ 8", "= log₂ n / 3"])
valid("mf_log_valid_base", "math_log", 2, "log₁₀ n ∈ Θ(log₂ n)", True,
      ["Logs in different bases differ only by a constant factor", "log₁₀ n grows faster", "Base 10 is bigger, so log₁₀ n is a higher class"],
      "Logs in different bases differ only by a constant factor",
      hints=["Change of base: log₁₀ n = log₂ n / log₂ 10.", "log₂ 10 ≈ 3.32 is a constant."],
      steps=["log₁₀ n = log₂ n / log₂ 10 ≈ 0.301 · log₂ n.", "A constant factor never changes Θ - so the base of a log is irrelevant in Θ(log n)."])
simp("mf_log_theta_nlog4", "math_log", 2, "Simplify, then classify", "n · log(n⁴) + n", "4n log(n) + n", "log_simple",
     extra=[theta("Growth rate", "n log(n)")], traps=[("n*log(4*n) + n", "log(n⁴) = 4 log n.")],
     hints=["Power rule on log(n⁴).", "4n log n dominates n."], steps=["n log(n⁴) + n = 4n log n + n", "Dominant term 4n log n → Θ(n log n)"])
simp("mf_log_sum_logs", "math_log", 2, "Add two logs", "log(n²) + log(n³)", "5log(n)", "log_simple",
     traps=[("6*log(n)", "2 log n + 3 log n = 5 log n (or use the product rule: log(n⁵))."), ("log(n^6)", "log a + log b = log(ab): n² · n³ = n⁵, not n⁶.")],
     hints=["Power rule on each, then combine like terms.", "2 log n + 3 log n."], steps=["log(n²) + log(n³) = 2 log n + 3 log n = 5 log n"])
simp("mf_log_sqrt", "math_log", 2, "Log of a square root", "log(√n)", "log(n)/2", "log_simple",
     traps=[("sqrt(log(n))", "log(√n) is not √(log n). √n = n^(1/2)."), ("2*log(n)", "√n = n^(1/2), so the factor is ½.")],
     hints=["Write √n as a power.", "√n = n^(1/2); now the power rule."], steps=["log(√n) = log(n^(1/2))", "= ½ log n"])
simp("mf_log_quot_powers", "math_log", 3, "Logs of a quotient of powers", "log(n⁵ / n²)", "3log(n)", "log_simple",
     traps=[("log(n^5)/log(n^2)", "log(a/b) = log a − log b, not a quotient of logs."), ("5/2*log(n)", "That divides the logs instead of subtracting.")],
     hints=["Either simplify n⁵/n² first, or use the quotient rule.", "log(n³) = 3 log n."], steps=["log(n⁵/n²) = log(n⁵) − log(n²) = 5 log n − 2 log n = 3 log n"])
simp("mf_log_n_log_8n", "math_log", 3, "Product rule inside a T(n)", "n · log(8n)", "n log(n) + 3n", "expanded",
     extra=[theta("Growth rate", "n log(n)")], traps=[("8*n*log(n)", "log(8n) = log 8 + log n = 3 + log n.")],
     hints=["Product rule: log(8n) = log 8 + log n.", "Then distribute the n."], steps=["n log(8n) = n(3 + log n)", "= n log n + 3n  → Θ(n log n)"])
# common log mistakes - valid or invalid?
LOGR = ["Product rule: log(xy) = log x + log y", "Quotient rule: log(x/y) = log x − log y", "Power rule: log(xᵏ) = k log x",
        "There is no rule for the log of a sum"]
valid("mf_log_v_sum", "math_log", 2, "log(a + b) = log a + log b", False, LOGR, LOGR[3],
      hints=["Which rule mentions a sum INSIDE the log?", "Try a = b = 1: log 2 = 1, but log 1 + log 1 = 0."],
      steps=["The product rule is about log(ab), not log(a + b).", "a = b = 1: log 2 = 1 ≠ 0. Invalid - log(a + b) does not split."])
valid("mf_log_v_prod", "math_log", 2, "log(ab) = log a · log b", False, LOGR, LOGR[0],
      hints=["What does the product rule actually say?", "Try a = b = 2: log 4 = 2, but 1 · 1 = 1."],
      steps=["Product rule: log(ab) = log a + log b - a SUM.", "a = b = 2: 2 ≠ 1. Invalid."])
valid("mf_log_v_quot", "math_log", 2, "log(a/b) = log a / log b", False, LOGR, LOGR[1],
      hints=["What does the quotient rule actually say?", "Try a = 8, b = 2: log 4 = 2, but 3/1 = 3."],
      steps=["Quotient rule: log(a/b) = log a − log b.", "a = 8, b = 2: 2 ≠ 3. Invalid. (log a / log b is a change of base: log_b a.)"])
valid("mf_log_v_power", "math_log", 1, "log(a⁵) = 5 log a", True, LOGR, LOGR[2],
      hints=["An exponent inside the log.", "Power rule."], steps=["Power rule: log(a⁵) = 5 log a. Valid (for a > 0)."])
valid("mf_log_v_sq", "math_log", 2, "(log n)² = 2 log n", False,
      ["(log n)² squares the log; the power rule needs the exponent inside the log", "Power rule: the exponent comes out", "They're equal for n ≥ 2"],
      "(log n)² squares the log; the power rule needs the exponent inside the log",
      hints=["Where is the exponent - inside or outside the log?", "n = 16: (log 16)² = 16, but 2 log 16 = 8."],
      steps=["2 log n = log(n²). (log n)² is log n times log n.", "n = 16: 16 ≠ 8. Invalid."])
valid("mf_log_v_8n", "math_log", 2, "log₂(8n) = 3 + log₂ n", True, LOGR, LOGR[0],
      hints=["8n is a product.", "log₂ 8 = 3."], steps=["log₂(8n) = log₂ 8 + log₂ n = 3 + log₂ n. Valid."])
valid("mf_log_v_theta", "math_log", 2, "log(n²) ∈ Θ(log n)", True,
      ["log(n²) = 2 log n, a constant multiple of log n", "n² grows faster, so log(n²) is a higher class", "Logs of polynomials are Θ(n)"],
      "log(n²) = 2 log n, a constant multiple of log n", hints=["Use the power rule first.", "2 log n vs log n: constant factor."],
      steps=["log(n²) = 2 log n, and constants don't change Θ. Valid - so log(n^k) ∈ Θ(log n) for any constant k."])
mistake("mf_log_mistake1", "math_log", 2, "log rules", ["log(4n²)", "= log 4 · log(n²)", "= 2 · 2 log n", "= 4 log n"], 2,
        "log(4) + log(n^2)", traps=[("log(4)*log(n^2)", "That's line 2 as written - the product rule gives a sum.")],
        hints=["Check the product rule in line 2.", "log(xy) = log x + log y."],
        steps=["Line 2 should be log 4 + log(n²).", "= 2 + 2 log n."])

# ============================================================================ Polynomial simplification
simp("mf_poly_combine", "math_poly", 1, "Combine like terms", "3n² + 5n − n² + 4n", "2n^2 + 9n", "combined",
     traps=[("11n^2", "Only LIKE terms combine: n² terms with n² terms, n terms with n terms."), ("4n^2 + 9n", "3n² − n² = 2n².")],
     hints=["Group the n² terms and the n terms.", "(3 − 1)n² + (5 + 4)n."], steps=["3n² − n² = 2n²;  5n + 4n = 9n", "= 2n² + 9n"])
simp("mf_poly_tn1", "math_poly", 1, "A T(n)-style sum", "1 + (n + 1) + n + n", "3n + 2", "combined",
     traps=[("3n + 1", "There are two constants: 1 and the 1 inside (n + 1)."), ("4n + 2", "Count the n terms: n (in the bracket), n, n = 3n.")],
     hints=["Remove the brackets, then add the n terms and the constants separately.", "n + n + n and 1 + 1."], steps=["1 + (n + 1) + n + n = 1 + n + 1 + n + n", "= 3n + 2"])
simp("mf_poly_dist_combine", "math_poly", 2, "Distribute and combine", "2 + 3(n + 1) + 2n", "5n + 5", "combined",
     traps=[("5n + 3", "3(n + 1) = 3n + 3, so the constants are 2 + 3 = 5.")],
     hints=["Distribute the 3 first.", "2 + 3n + 3 + 2n."], steps=["2 + 3(n + 1) + 2n = 2 + 3n + 3 + 2n", "= 5n + 5"])
simp("mf_poly_cancel", "math_poly", 2, "Something cancels", "n(n + 1) − n²", "n", "combined",
     traps=[("2n^2 + n", "Subtract n², don't add it."), ("n^2 + n", "n(n + 1) = n² + n; then subtract n².")],
     hints=["Expand n(n + 1).", "n² + n − n²."], steps=["n(n + 1) − n² = n² + n − n²", "= n"])
simp("mf_poly_diff_squares", "math_poly", 3, "Difference of two squares", "(n + 1)² − (n − 1)²", "4n", "combined",
     traps=[("2", "Expand both squares fully: (n + 1)² = n² + 2n + 1."), ("2n^2 + 2", "Subtracting the second square flips all its signs.")],
     hints=["Expand each square.", "(n² + 2n + 1) − (n² − 2n + 1)."], steps=["(n + 1)² − (n − 1)² = (n² + 2n + 1) − (n² − 2n + 1)", "= n² + 2n + 1 − n² + 2n − 1 = 4n"])
shown("mf_poly_work1", "math_poly", 2, "Simplify a T(n), showing work", "1 + (n + 1) + n(n + 1) + n·n",
      "1 + (n + 1) + n(n + 1) + n*n", ["1 + n + 1 + n^2 + n + n^2", "2n^2 + 2n + 2"], "2n^2 + 2n + 2", "combined",
      hints=["First remove brackets by distributing.", "Then group n² terms, n terms and constants."])
mistake("mf_poly_mistake", "math_poly", 2, "subtracting a polynomial", ["2n² + 3n − (n² − n)", "= 2n² + 3n − n² − n", "= n² + 2n"], 2,
        "2n^2 + 3n - n^2 + n", hints=["What happens to −n when the bracket is subtracted?", "−(−n) = +n."],
        steps=["Line 2 should be 2n² + 3n − n² + n.", "So the result is n² + 4n."])
valid("mf_poly_valid", "math_poly", 1, "3n + 2n² = 5n³", False,
      ["3n and 2n² are not like terms, so they cannot be combined", "Add coefficients and exponents", "It is valid for n = 1"],
      "3n and 2n² are not like terms, so they cannot be combined",
      hints=["Like terms have the same variable AND the same exponent.", "n = 2: 6 + 8 = 14, but 5 · 8 = 40."], steps=["n and n² are different kinds of term; 3n + 2n² is already simplified. Invalid."])
staged("mf_poly_steps", "math_poly", 2, "Step by step: 2 + (n + 1) + 2n + 3n", "T(n) = 2 + (n + 1) + 2n + 3n", [
    choice("Step 1 · What do you do first?", ["Remove the brackets", "Multiply all the terms", "Factor out n"], "Remove the brackets"),
    expr("Step 2 · Without brackets", "2 + n + 1 + 2n + 3n", traps=[("2 + n + 2n + 3n", "Keep the 1 from the bracket.")]),
    choice("Step 3 · Next?", ALG_RULES, ALG_RULES[1]),
    expr("Step 4 · Final T(n)", "6n + 3", "combined", [("5n + 3", "n + 2n + 3n = 6n.")])],
    ["Brackets first.", "Then add n terms (n + 2n + 3n) and constants (2 + 1)."], ["2 + (n + 1) + 2n + 3n = 2 + n + 1 + 2n + 3n", "= 6n + 3"])
simp("mf_poly_cubic", "math_poly", 3, "Expand and combine a cubic", "n(n + 1)(n + 2)", "n^3 + 3n^2 + 2n", "expanded",
     traps=[("n^3 + 2n", "Expand (n + 1)(n + 2) = n² + 3n + 2 first, then multiply by n.")],
     hints=["Multiply two brackets first.", "(n + 1)(n + 2) = n² + 3n + 2; times n."], steps=["(n + 1)(n + 2) = n² + 3n + 2", "n(n² + 3n + 2) = n³ + 3n² + 2n"])

# ============================================================================ Factoring
simp("mf_fac_nn1", "math_factor", 1, "Factor out n", "n² + n", "n(n + 1)", "factored", label="Factored form",
     traps=[("n(n)", "n ÷ n = 1, so the bracket keeps a + 1.")], hints=["Both terms contain n.", "n² + n = n·n + n·1."],
     steps=["n² + n = n·n + n·1", "= n(n + 1)"])
simp("mf_fac_3n", "math_factor", 1, "Factor out the greatest common factor", "3n² + 6n", "3n(n + 2)", "factored", label="Factored form",
     traps=[("3n(n + 6)", "Divide BOTH terms by 3n: 6n ÷ 3n = 2."), ("3(n^2 + 6n)", "6n ÷ 3 = 2n, and you can also take out n.")],
     hints=["What do 3n² and 6n share?", "Both are divisible by 3n."], steps=["3n² + 6n = 3n·n + 3n·2", "= 3n(n + 2)"])
simp("mf_fac_dos", "math_factor", 2, "Difference of squares", "n² − 1", "(n - 1)(n + 1)", "factored", label="Factored form",
     traps=[("(n - 1)^2", "(n − 1)² = n² − 2n + 1. A difference of squares gives (n − 1)(n + 1).")],
     hints=["a² − b² = (a − b)(a + b).", "Here a = n, b = 1."], steps=["n² − 1 = n² − 1²", "= (n − 1)(n + 1)"])
simp("mf_fac_trinomial", "math_factor", 2, "Factor a trinomial", "n² + 5n + 6", "(n + 2)(n + 3)", "factored", label="Factored form",
     traps=[("(n + 1)(n + 6)", "1 · 6 = 6, but 1 + 6 = 7, not 5.")], hints=["Find two numbers that multiply to 6 and add to 5.", "2 and 3."],
     steps=["2 · 3 = 6 and 2 + 3 = 5", "n² + 5n + 6 = (n + 2)(n + 3)"])
simp("mf_fac_cubic", "math_factor", 2, "Factor out a power", "n³ − n²", "n^2(n - 1)", "factored", label="Factored form",
     traps=[("n(n^2 - 1)", "That's not fully factored - n² is common to both terms (and n(n² − 1) ≠ n³ − n²)."),
            ("n^2(n + 1)", "Watch the sign: n³ − n² = n²(n − 1).")],
     hints=["The smallest power of n in both terms is n².", "n³ ÷ n² = n, n² ÷ n² = 1."], steps=["n³ − n² = n²·n − n²·1", "= n²(n − 1)"])
simp("mf_fac_exp", "math_factor", 3, "Factor out 2ⁿ", "2ⁿ⁺² + 2ⁿ", "5*2^n", "split_exp", label="Written as (constant) · 2ⁿ",
     traps=[("2^(2n+2)", "You can't add exponents across a +. Factor: 2ⁿ(2² + 1)."), ("4*2^n", "Don't drop the second term: 2ⁿ(4 + 1).")],
     hints=["2ⁿ⁺² = 4 · 2ⁿ.", "4 · 2ⁿ + 1 · 2ⁿ = 2ⁿ(4 + 1)."], steps=["2ⁿ⁺² + 2ⁿ = 4 · 2ⁿ + 1 · 2ⁿ", "= 2ⁿ(4 + 1) = 5 · 2ⁿ"])
mistake("mf_fac_mistake", "math_factor", 2, "factoring out 3n", ["6n² + 9n", "= 3n(2n + 9)"], 2, "3n(2n + 3)", "factored",
        hints=["Multiply the answer back out to check it.", "3n · 9 = 27n, not 9n."], steps=["9n ÷ 3n = 3, so 6n² + 9n = 3n(2n + 3)."])
simp("mf_fac_sum_formula", "math_factor", 3, "Factor a sum formula", "n(n + 1)/2 + (n + 1)", "(n + 1)(n + 2)/2", "factored", label="Factored form",
     traps=[("(n + 1)(n + 1)/2", "(n + 1) = 2(n + 1)/2, so the bracket gets n + 2.")],
     hints=["Both terms contain (n + 1).", "(n + 1)·[n/2 + 1] = (n + 1)(n + 2)/2."], steps=["n(n + 1)/2 + (n + 1) = (n + 1)(n/2 + 1)", "= (n + 1)(n + 2)/2"])

# ============================================================================ Fractions & rational expressions
simp("mf_frac_expand1", "math_frac", 1, "Expand n(n + 1)/2", "n(n + 1)/2", "(n^2 + n)/2", "expanded", label="Expanded form",
     traps=[("(n^2 + 1)/2", "n · 1 = n, not 1."), ("n^2/2 + 1/2", "n(n + 1) = n² + n, so it's n²/2 + n/2.")],
     hints=["Distribute n over (n + 1) in the numerator.", "(n² + n)/2 = n²/2 + n/2 also counts."], steps=["n(n + 1)/2 = (n² + n)/2", "= n²/2 + n/2"])
simp("mf_frac_expand2", "math_frac", 1, "Expand n(n − 1)/2", "n(n − 1)/2", "(n^2 - n)/2", "expanded", label="Expanded form",
     traps=[("(n^2 + n)/2", "n(n − 1) = n² − n.")], hints=["Distribute n.", "n · (−1) = −n."], steps=["n(n − 1)/2 = (n² − n)/2 = n²/2 − n/2"])
simp("mf_frac_plus_n", "math_frac", 2, "Add n to a fraction", "n(n − 1)/2 + n", "n^2/2 + n/2", "expanded", label="Expanded form",
     traps=[("(n^2 - n + n)/2", "n is 2n/2 in halves, not n/2."), ("n^2/2 - n/2 + n/2", "Combine: −n/2 + n = +n/2.")],
     extra=[theta("Growth rate", "n^2")], hints=["Expand first: (n² − n)/2.", "−n/2 + n = −n/2 + 2n/2 = n/2."],
     steps=["n(n − 1)/2 + n = n²/2 − n/2 + n", "= n²/2 + n/2  → Θ(n²)"])
simp("mf_frac_factor", "math_frac", 2, "Factor a fraction", "(n² + n)/2", "n(n + 1)/2", "factored", label="Factored form",
     hints=["Factor the numerator.", "n² + n = n(n + 1)."], steps=["(n² + n)/2 = n(n + 1)/2"])
simp("mf_frac_single", "math_frac", 3, "Combine two fractions", "1/n + 1/(n + 1)", "(2n + 1)/(n(n + 1))", "single_fraction", label="As a single fraction",
     traps=[("2/(2n + 1)", "You can't add denominators. Use the common denominator n(n + 1)."), ("2/(n(n + 1))", "The numerators become (n + 1) + n.")],
     hints=["Common denominator: n(n + 1).", "(n + 1)/(n(n + 1)) + n/(n(n + 1))."], steps=["1/n + 1/(n + 1) = (n + 1)/(n(n + 1)) + n/(n(n + 1))", "= (2n + 1)/(n(n + 1))"])
simp("mf_frac_cancel", "math_frac", 2, "Cancel a common factor", "(6n² + 3n)/(3n)", "2n + 1", "combined",
     traps=[("2n + 3n", "Divide EACH term of the numerator by 3n."), ("6n^2 + 1", "6n² ÷ 3n = 2n.")],
     hints=["Factor the numerator: 3n(2n + 1).", "Cancel 3n."], steps=["(6n² + 3n)/(3n) = 3n(2n + 1)/(3n)", "= 2n + 1"])
valid("mf_frac_valid", "math_frac", 1, "(n + 4)/2 = n + 2", False,
      ["Both terms must be divided: (n + 4)/2 = n/2 + 2", "You may cancel any number with the denominator", "It is valid when n is even"],
      "Both terms must be divided: (n + 4)/2 = n/2 + 2", hints=["Division distributes over every term.", "n = 2: 6/2 = 3, but 2 + 2 = 4."],
      steps=["(n + 4)/2 = n/2 + 4/2 = n/2 + 2. The claim divided only the 4. Invalid."])
mistake("mf_frac_mistake", "math_frac", 2, "adding n to a fraction", ["n(n + 1)/2 + n", "= (n² + n)/2 + n", "= (n² + n + n)/2", "= (n² + 2n)/2"], 3,
        "(n^2 + n + 2n)/2", traps=[("(n^2 + n + n)/2", "That's line 3 as written: n over 2 is 2n/2.")],
        hints=["To put n over 2 it must become 2n/2.", "(n² + n)/2 + 2n/2."], steps=["Line 3 should be (n² + n + 2n)/2 = (n² + 3n)/2."])
simp("mf_frac_halves", "math_frac", 1, "Add halves", "n/2 + n/2 + 1", "n + 1", "combined",
     traps=[("n/4 + 1", "Same denominator: add numerators. n/2 + n/2 = 2n/2 = n."), ("2n + 1", "n/2 + n/2 = n, not 2n.")],
     hints=["Two halves make a whole.", "n/2 + n/2 = 2n/2."], steps=["n/2 + n/2 + 1 = 2n/2 + 1 = n + 1"])

# ============================================================================ Arithmetic sequences
_ex("mf_aseq_d", "math_aseq", "math_simplify", 1, "Common difference", "Find the common difference and the next term.",
    [num("Common difference d", 4), num("Next term", 19)], ["Subtract consecutive terms.", "7 − 3 = 4; add d to 15."],
    ["d = 7 − 3 = 11 − 7 = 15 − 11 = 4", "Next term: 15 + 4 = 19"], formula="3, 7, 11, 15, …")
_ex("mf_aseq_nth", "math_aseq", "math_simplify", 2, "nth term formula", "An arithmetic sequence has a₁ = 5 and d = 3. " + INPUT_NOTE,
    [expr("aₙ as a formula in n", "3n + 2", "combined", [("3n + 5", "aₙ = a₁ + (n − 1)d - the first term has zero d's added.")]), num("a₁₀", 32)],
    ["aₙ = a₁ + (n − 1)d.", "5 + 3(n − 1) = 3n + 2."], ["aₙ = 5 + (n − 1)·3 = 3n + 2", "a₁₀ = 3·10 + 2 = 32"], formula="a₁ = 5,  d = 3")
_ex("mf_aseq_missing", "math_aseq", "math_simplify", 1, "Missing terms", "Fill in the two missing terms of the arithmetic sequence.",
    [num("Second term", 7), num("Third term", 10)], ["From 4 to 13 takes 3 equal steps.", "d = (13 − 4)/3 = 3."],
    ["13 = 4 + 3d → d = 3", "4, 7, 10, 13"], formula="4, __, __, 13")
_ex("mf_aseq_count_even", "math_aseq", "math_simplify", 2, "Number of terms: 2, 4, …, 2n", "How many terms are in the sequence? " + INPUT_NOTE,
    [expr("Number of terms", "n", traps=[("2n", "The terms are 2·1, 2·2, …, 2·n: one per value 1..n."), ("n - 1", "Count: (last − first)/d + 1.")])],
    ["Write each term as 2·k.", "(2n − 2)/2 + 1."], ["2, 4, …, 2n = 2·1, 2·2, …, 2·n", "(2n − 2)/2 + 1 = n terms"], formula="2, 4, 6, …, 2n")
_ex("mf_aseq_odd", "math_aseq", "math_simplify", 2, "The odd numbers 1, 3, …, 2n − 1", "Answer both. " + INPUT_NOTE,
    [expr("The kth term (use k)", "2k - 1", traps=[("2k + 1", "Check k = 1: the first term is 1.")]),
     expr("Number of terms up to 2n − 1", "n", traps=[("2n - 1", "Count: ((2n − 1) − 1)/2 + 1.")])],
    ["d = 2, a₁ = 1.", "a_k = 1 + 2(k − 1) = 2k − 1; solve 2k − 1 = 2n − 1."], ["a_k = 1 + (k − 1)·2 = 2k − 1", "2k − 1 = 2n − 1 → k = n, so n terms"],
    formula="1, 3, 5, …, 2n − 1")
_ex("mf_aseq_count_num", "math_aseq", "math_simplify", 2, "Count the terms", "How many terms are in this arithmetic sequence?",
    [num("Number of terms", 32)], ["Number of terms = (last − first)/d + 1.", "(100 − 7)/3 + 1."], ["d = 3", "(100 − 7)/3 + 1 = 31 + 1 = 32"],
    formula="7, 10, 13, …, 100")
_ex("mf_aseq_k_to_n", "math_aseq", "math_simplify", 2, "Number of integers from k to n", "How many integers are in k, k + 1, …, n (k ≤ n)? " + INPUT_NOTE,
    [expr("Number of terms", "n - k + 1", traps=[("n - k", "Off by one: from 3 to 5 there are 3 numbers, not 2.")])],
    ["Try a small case: k = 3, n = 5.", "(n − k)/1 + 1."], ["(n − k)/1 + 1 = n − k + 1"], formula="k, k + 1, …, n")
mistake("mf_aseq_mistake", "math_aseq", 2, "counting terms", ["5, 8, 11, …, 50", "number of terms = (50 − 5)/3", "= 15"], 2,
        "(50 - 5)/3 + 1", traps=[("(50 - 5)/3", "That's the number of GAPS between terms.")],
        hints=["How many terms does 5, 8 have? Check the formula on it.", "Terms = gaps + 1."], steps=["Line 2 should be (50 − 5)/3 + 1 = 16."])
apply("mf_aseq_apply", "math_aseq", 3, "A loop stepping by 3", [
    choice("The values of i form…", ["an arithmetic sequence", "a geometric sequence", "neither"], "an arithmetic sequence"),
    num("Iterations when n = 30", 10),
    expr("Iterations for n a multiple of 3", "n/3", traps=[("n", "i grows by 3 each time."), ("n/3 + 1", "i = 3, 6, …, n: that's n/3 values.")]),
    theta("Growth rate", "n")],
    ["i takes the values 3, 6, 9, …", "Number of terms = (n − 3)/3 + 1."], ["i = 3, 6, …, n: arithmetic with d = 3", "(n − 3)/3 + 1 = n/3 iterations → Θ(n)"],
    code="i := 3\nwhile i ≤ n\n    work\n    i := i + 3")

# ============================================================================ Arithmetic series & summations
_ex("mf_ser_gauss", "math_aseries", "math_simplify", 1, "1 + 2 + … + n", "Give a closed form. " + INPUT_NOTE,
    [expr("Closed form", "n(n + 1)/2", traps=[("n^2", "Close, but the exact sum is n(n + 1)/2."), ("n(n - 1)/2", "That's 1 + … + (n − 1).")]),
     theta("Growth rate", "n^2")],
    ["Pair the first and last terms.", "n/2 pairs, each summing to n + 1."], ["1 + 2 + … + n = n(n + 1)/2 = (n² + n)/2", "→ Θ(n²)"],
    formula="1 + 2 + 3 + … + n")
_ex("mf_ser_to_n1", "math_aseries", "math_simplify", 2, "1 + 2 + … + (n − 1)", "Give a closed form. " + INPUT_NOTE,
    [expr("Closed form", "n(n - 1)/2", traps=[("n(n + 1)/2", "That sum stops at n; this one stops at n − 1.")])],
    ["Use the formula with n − 1 in place of n.", "(n − 1)·n/2."], ["Replace n by n − 1 in m(m + 1)/2: (n − 1)n/2", "= (n² − n)/2"],
    formula="1 + 2 + … + (n − 1)")
_ex("mf_ser_sn", "math_aseries", "math_simplify", 2, "Sₙ = n(a₁ + aₙ)/2", "Sum the first n terms of 3, 7, 11, … (aₙ = 4n − 1). " + INPUT_NOTE,
    [expr("Sₙ", "2n^2 + n", traps=[("n(4n + 2)", "Don't forget to divide by 2."), ("4n^2 + 2n", "Divide by 2.")]), theta("Growth rate", "n^2")],
    ["Sₙ = n(a₁ + aₙ)/2.", "n(3 + 4n − 1)/2 = n(4n + 2)/2."], ["Sₙ = n(3 + (4n − 1))/2 = n(4n + 2)/2", "= 2n² + n → Θ(n²)"],
    formula="3 + 7 + 11 + … + (4n − 1)")
_ex("mf_ser_odd_sum", "math_aseries", "math_simplify", 2, "Sum of the first n odd numbers", "Give a closed form. " + INPUT_NOTE,
    [expr("Σᵢ₌₁ⁿ (2i − 1)", "n^2", traps=[("n(n + 1)", "Σ 2i = n(n + 1), but you also subtract Σ 1 = n.")])],
    ["Split: 2 Σ i − Σ 1.", "2 · n(n + 1)/2 − n."], ["Σ(2i − 1) = 2 · n(n + 1)/2 − n", "= n² + n − n = n²"], formula="Σᵢ₌₁ⁿ (2i − 1)")
_ex("mf_ser_3i", "math_aseries", "math_simplify", 2, "Pull a constant out of a sum", "Give a closed form. " + INPUT_NOTE,
    [expr("Σᵢ₌₁ⁿ 3i", "3n(n + 1)/2", traps=[("3n", "Σ 3i = 3 Σ i, and Σ i = n(n + 1)/2."), ("n(n + 1)/2", "Keep the factor 3.")])],
    ["Constants factor out of a sum.", "3 · Σ i."], ["Σ 3i = 3 Σ i = 3n(n + 1)/2"], formula="Σᵢ₌₁ⁿ 3i")
_ex("mf_ser_5050", "math_aseries", "math_simplify", 1, "1 + 2 + … + 100", "Compute the sum.", [num("Sum", 5050)],
    ["n(n + 1)/2 with n = 100.", "100 · 101 / 2."], ["100 · 101 / 2 = 5050"], formula="1 + 2 + … + 100")
_ex("mf_ser_num", "math_aseries", "math_simplify", 2, "A finite arithmetic series", "Compute the sum.",
    [num("Number of terms", 16), num("Sum", 440)], ["First count terms: (50 − 5)/3 + 1.", "S = n(a₁ + aₙ)/2 = 16 · 55 / 2."],
    ["(50 − 5)/3 + 1 = 16 terms", "S = 16(5 + 50)/2 = 440"], formula="5 + 8 + 11 + … + 50")
apply("mf_ser_nested", "math_aseries", 3, "Nested loop: j up to i", [
    choice("The inner-loop counts over all i form…", ["1 + 2 + … + n (an arithmetic series)", "n + n + … + n", "1 + 2 + 4 + … (geometric)"],
           "1 + 2 + … + n (an arithmetic series)"),
    expr("Total number of times 'work' runs", "n(n + 1)/2", traps=[("n^2", "The inner loop runs i times, not n times.")]),
    theta("Growth rate", "n^2")],
    ["For a fixed i, the inner loop runs i times.", "Σᵢ₌₁ⁿ i."], ["Inner loop runs i times: total = 1 + 2 + … + n", "= n(n + 1)/2 → Θ(n²)"],
    code="for i := 1 to n\n    for j := 1 to i\n        work")
apply("mf_ser_nested2", "math_aseries", 3, "Nested loop: j from i + 1", [
    expr("Times 'work' runs when i = 1", "n - 1"),
    expr("Total number of times 'work' runs", "n(n - 1)/2", traps=[("n(n + 1)/2", "When i = n the inner loop runs 0 times: (n − 1) + … + 1 + 0.")]),
    theta("Growth rate", "n^2")],
    ["For a fixed i, j runs from i + 1 to n: n − i times.", "(n − 1) + (n − 2) + … + 1 + 0."],
    ["Inner count n − i: total = Σᵢ₌₁ⁿ (n − i) = (n − 1) + … + 0", "= n(n − 1)/2 → Θ(n²)"], code="for i := 1 to n\n    for j := i + 1 to n\n        work")
_ex("mf_ser_i_plus_2", "math_aseries", "math_simplify", 3, "Split a sum", "Give a closed form, expanded. " + INPUT_NOTE,
    [expr("Σᵢ₌₁ⁿ (i + 2)", "(n^2 + 5n)/2", "expanded", [("n(n + 1)/2 + 2", "Σ 2 = 2 + 2 + … + 2 = 2n, not 2.")])],
    ["Σ(i + 2) = Σ i + Σ 2.", "Σᵢ₌₁ⁿ 2 = 2n."], ["Σ(i + 2) = n(n + 1)/2 + 2n", "= (n² + n + 4n)/2 = (n² + 5n)/2"], formula="Σᵢ₌₁ⁿ (i + 2)")
valid("mf_ser_valid", "math_aseries", 2, "1 + 2 + … + n = n²/2", False,
      ["The exact sum is n(n + 1)/2 = n²/2 + n/2", "Sums of n terms always equal n²/2", "It is valid for every even n"],
      "The exact sum is n(n + 1)/2 = n²/2 + n/2", hints=["Try n = 2.", "1 + 2 = 3, but 2²/2 = 2."],
      steps=["Exact: n(n + 1)/2. n²/2 is the leading term (same Θ(n²)) but not equal. Invalid."])
staged("mf_ser_steps", "math_aseries", 3, "Step by step: Σᵢ₌₁ⁿ (4i + 1)", "Σᵢ₌₁ⁿ (4i + 1)", [
    choice("Step 1 · First move", ["Split the sum: 4 Σ i + Σ 1", "Multiply out (4i + 1)²", "Use the geometric formula"], "Split the sum: 4 Σ i + Σ 1"),
    expr("Step 2 · Substitute the known sums", "4n(n + 1)/2 + n", traps=[("4n(n + 1)/2 + 1", "Σᵢ₌₁ⁿ 1 = n.")]),
    expr("Step 3 · Simplified (expanded)", "2n^2 + 3n", "expanded", [("2n^2 + 2n", "2n(n + 1) + n = 2n² + 2n + n.")])],
    ["Σ(a + b) = Σa + Σb, constants factor out.", "4 · n(n + 1)/2 + n."], ["Σ(4i + 1) = 4 Σ i + Σ 1 = 4 · n(n + 1)/2 + n", "= 2n² + 2n + n = 2n² + 3n"])

# ============================================================================ Geometric sequences
_ex("mf_geo_ratio", "math_gseq", "math_simplify", 1, "Common ratio", "Find the common ratio and the next term.",
    [num("Common ratio r", 3), num("Next term", 162)], ["Divide consecutive terms.", "6 / 2 = 3."], ["r = 6/2 = 18/6 = 3", "54 · 3 = 162"],
    formula="2, 6, 18, 54, …")
_ex("mf_geo_nth", "math_gseq", "math_simplify", 2, "nth term of the powers of 2", "Give a formula for the nth term (first term is n = 1). " + INPUT_NOTE,
    [expr("aₙ", "2^(n - 1)", traps=[("2^n", "Check n = 1: the first term is 1 = 2⁰."), ("2n", "This sequence multiplies by 2; it doesn't add 2.")])],
    ["aₙ = a₁ · rⁿ⁻¹.", "a₁ = 1, r = 2."], ["aₙ = 1 · 2ⁿ⁻¹ = 2ⁿ⁻¹  (= 2ⁿ/2)"], formula="1, 2, 4, 8, 16, …")
_ex("mf_geo_count", "math_gseq", "math_simplify", 2, "How many powers of 2 up to n?", "n is a power of 2. How many terms are in 1, 2, 4, …, n? " + INPUT_NOTE,
    [expr("Number of terms", "log(n) + 1", traps=[("log(n)", "Count 2⁰ too: exponents 0, 1, …, log n."), ("n/2", "Doubling reaches n much faster than adding.")])],
    ["The terms are 2⁰, 2¹, …, 2ᵏ with 2ᵏ = n.", "k = log₂ n; exponents 0..k."], ["1, 2, …, n = 2⁰, …, 2ᵏ where k = log₂ n", "k + 1 = log₂ n + 1 terms"],
    formula="1, 2, 4, …, n")
apply("mf_geo_doubling", "math_gseq", 3, "A doubling loop", [
    choice("The values of i form…", ["a geometric sequence with ratio 2", "an arithmetic sequence with difference 2", "neither"], "a geometric sequence with ratio 2"),
    num("Iterations when n = 64", 6),
    expr("Iterations for n a power of 2", "log(n)", traps=[("n/2", "i doubles; it doesn't step by 2."), ("log(n) + 1", "The loop stops when i = n (i < n fails).")]),
    theta("Growth rate", "log(n)")],
    ["i = 1, 2, 4, 8, …: after k iterations i = 2ᵏ.", "The loop stops when 2ᵏ ≥ n."],
    ["After k iterations i = 2ᵏ; the loop stops at 2ᵏ = n", "k = log₂ n iterations → Θ(log n)"], code="i := 1\nwhile i < n\n    work\n    i := 2i")
apply("mf_geo_halving", "math_gseq", 3, "A halving loop", [
    choice("The values of i form…", ["a geometric sequence with ratio ½", "an arithmetic sequence with difference −2", "neither"], "a geometric sequence with ratio ½"),
    num("Iterations when n = 32", 5), theta("Growth rate", "log(n)")],
    ["i = n, n/2, n/4, …", "After k iterations i = n/2ᵏ; stop when it reaches 1."], ["i = n/2ᵏ after k iterations; stops when n/2ᵏ = 1", "k = log₂ n → Θ(log n)"],
    code="i := n\nwhile i > 1\n    work\n    i := i / 2")
_ex("mf_geo_sum", "math_gseq", "math_simplify", 3, "A geometric series", "Give a closed form. " + INPUT_NOTE,
    [expr("1 + 2 + 4 + … + 2ᵏ", "2^(k + 1) - 1", traps=[("2^k - 1", "There are k + 1 terms: the sum is 2ᵏ⁺¹ − 1."), ("2^(k + 1)", "Check k = 0: the sum is 1.")])],
    ["Geometric series: a(rᵐ − 1)/(r − 1) with m terms.", "k + 1 terms, a = 1, r = 2."], ["Σⱼ₌₀ᵏ 2ʲ = (2ᵏ⁺¹ − 1)/(2 − 1) = 2ᵏ⁺¹ − 1"], formula="1 + 2 + 4 + … + 2ᵏ")
valid("mf_geo_valid", "math_gseq", 3, "1 + 2 + 4 + … + n = 2n − 1 (n a power of 2), so it is Θ(n)", True,
      ["Geometric sum: 2ᵏ⁺¹ − 1 with 2ᵏ = n", "It has n terms, so it's Θ(n²)", "Geometric series are always Θ(2ⁿ)"],
      "Geometric sum: 2ᵏ⁺¹ − 1 with 2ᵏ = n", hints=["n = 2ᵏ; sum is 2ᵏ⁺¹ − 1.", "2ᵏ⁺¹ = 2n."],
      steps=["1 + … + 2ᵏ = 2ᵏ⁺¹ − 1 = 2n − 1 → Θ(n). Valid - the last term dominates a doubling series."])
apply("mf_geo_tripling", "math_gseq", 3, "A tripling loop", [
    num("Iterations when n = 81", 5), theta("Growth rate", "log(n)")],
    ["i = 1, 3, 9, 27, 81 - count them.", "After k iterations i = 3ᵏ; log₃ n is still Θ(log n)."],
    ["i = 1, 3, 9, 27, 81: 5 iterations (i ≤ n includes 81)", "3ᵏ ≤ n → k ≈ log₃ n = log₂ n / log₂ 3 → Θ(log n)"],
    code="i := 1\nwhile i ≤ n\n    work\n    i := 3i")
mistake("mf_geo_mistake", "math_gseq", 3, "counting a doubling loop",
        ["i takes the values 1, 2, 4, …, n", "these increase by 2 each time", "so the loop runs n/2 times"], 2, "2^k",
        prompt="Find the first incorrect line. Then: after k iterations, what is i? " + INPUT_NOTE, label="Value of i after k iterations",
        traps=[("2k", "i is MULTIPLIED by 2 each time (geometric), not increased by 2.")],
        hints=["Look at how 1 → 2 → 4 changes.", "Multiplying by 2 each time means i = 2ᵏ after k steps."],
        steps=["Line 2 is wrong: the values are multiplied by 2 (geometric), not increased by 2.", "i = 2ᵏ, so the loop runs log₂ n times."])

# ============================================================================ Growth-rate simplification
GROW = [("mf_gr_poly", 1, "3n² + 5n + 100", "n^2", "Keep the highest power; drop its coefficient."),
        ("mf_gr_tri", 1, "n(n + 1)/2", "n^2", "Expand: n²/2 + n/2."),
        ("mf_gr_nlog", 2, "5n log(n³) + 2n", "n log(n)", "log(n³) = 3 log n, so 15n log n + 2n."),
        ("mf_gr_exp", 2, "2ⁿ⁺¹ + n³", "2^n", "2ⁿ⁺¹ = 2 · 2ⁿ, and exponentials beat polynomials."),
        ("mf_gr_log", 2, "log(n²) + 7", "log(n)", "log(n²) = 2 log n."),
        ("mf_gr_frac", 2, "(n² + n)/n", "n", "Divide each term by n first.")]
for gid, lv, f, ans, h in GROW:
    _ex(gid, "math_growth", "math_simplify", lv, f"Growth rate of {f}", "Give the tight bound Θ(…). Simplify first, then keep only the dominant term.",
        [theta("Growth rate", ans)], [h, "Drop constant factors and lower-order terms."], [h, f"→ Θ({ans})"], formula=f)
_ex("mf_gr_order", "math_growth", "math_simplify", 2, "Order growth rates", "Order from slowest-growing to fastest-growing.",
    [order("Slowest → fastest", ["n", "log n", "n²", "2ⁿ", "n log n"], ["log n", "n", "n log n", "n²", "2ⁿ"])],
    ["log n < n.", "n < n log n < n² < 2ⁿ."], ["log n < n < n log n < n² < 2ⁿ"])
valid("mf_gr_valid_4n", "math_growth", 3, "Θ(2²ⁿ) = Θ(2ⁿ)", False,
      ["2²ⁿ = 4ⁿ, and 4ⁿ/2ⁿ = 2ⁿ → ∞ - a constant in the exponent matters", "Constants never matter in Θ", "They differ only by the factor 2"],
      "2²ⁿ = 4ⁿ, and 4ⁿ/2ⁿ = 2ⁿ → ∞ - a constant in the exponent matters", hints=["Rewrite 2²ⁿ with the power-of-a-power rule.", "Ratio 4ⁿ/2ⁿ."],
      steps=["2²ⁿ = (2²)ⁿ = 4ⁿ; 4ⁿ/2ⁿ = 2ⁿ is unbounded. Invalid: a constant FACTOR can be dropped, a constant multiplier IN THE EXPONENT cannot."])
valid("mf_gr_valid_log3", "math_growth", 2, "Θ(log(n³)) = Θ(log n)", True,
      ["log(n³) = 3 log n: a constant factor", "n³ grows faster than n", "Logs of powers are always Θ(n)"], "log(n³) = 3 log n: a constant factor",
      hints=["Power rule: log(n³) = ? · log n.", "A constant factor doesn't change Θ."], steps=["log(n³) = 3 log n → Θ(log n). Valid."])
rule("mf_gr_rule", "math_growth", 1, "7n² + 3n  (simplify for Θ)", ["Drop constant factors and lower-order terms", "Add the coefficients", "Keep every term"],
     "Drop constant factors and lower-order terms", "n^2", label="The simplified growth function g(n) in Θ(g(n))",
     traps=[("7n^2", "Θ also drops the constant factor 7."), ("n", "The dominant term is n².")],
     hints=["Which term dominates for large n?", "7n² → drop the 7."], steps=["7n² + 3n: dominant term 7n², drop the 7 → Θ(n²)"])

# ============================================================================ Inequalities
bound("mf_ineq_lin", "math_ineq", 2, "Choose C: 3n + 5 ≤ C·n", "3n + 5 ≤ C·n  for all n ≥ 5",
      [const("C", "3n + 5", "n", 5, "4")], ["For n ≥ 5, 5 ≤ n.", "3n + 5 ≤ 3n + n = 4n."], ["For n ≥ 5: 5 ≤ n, so 3n + 5 ≤ 3n + n = 4n", "C = 4 works (any C ≥ 4 does)."])
bound("mf_ineq_quad", "math_ineq", 2, "Choose C: n² + 10n ≤ C·n²", "n² + 10n ≤ C·n²  for all n ≥ 10",
      [const("C", "n^2 + 10n", "n^2", 10, "2")], ["For n ≥ 10, 10n ≤ n · n.", "n² + 10n ≤ n² + n² = 2n²."], ["For n ≥ 10: 10n ≤ n², so n² + 10n ≤ 2n²", "C = 2 works."])
bound("mf_ineq_lower", "math_ineq", 3, "Choose C: 2n² − 3n ≥ C·n²", "2n² − 3n ≥ C·n²  for all n ≥ 3",
      [const("C (C > 0)", "2n^2 - 3n", "n^2", 3, "1", side="lower")], ["You need a lower bound: make C small.", "For n ≥ 3, 3n ≤ n²."],
      ["For n ≥ 3: 3n ≤ n², so 2n² − 3n ≥ 2n² − n² = n²", "C = 1 works."])
bound("mf_ineq_nlogn", "math_ineq", 3, "Choose C: 4n log n + n ≤ C·n log n", "4n log n + n ≤ C·n log n  for all n ≥ 2",
      [const("C", "4n log(n) + n", "n log(n)", 2, "5")], ["For n ≥ 2, log₂ n ≥ 1, so n ≤ n log n.", "4n log n + n log n."],
      ["n ≥ 2 ⇒ log n ≥ 1 ⇒ n ≤ n log n", "4n log n + n ≤ 5n log n: C = 5"])
_ex("mf_ineq_n0", "math_ineq", "math_bound", 2, "Find n₀", "With C = 2, find the smallest integer n₀ such that n + 8 ≤ 2n for all n ≥ n₀.",
    [num("n₀", 8)], ["Solve n + 8 ≤ 2n.", "Subtract n from both sides."], ["n + 8 ≤ 2n ⇔ 8 ≤ n", "n₀ = 8"], formula="n + 8 ≤ 2n")
valid("mf_ineq_v_100n", "math_ineq", 2, "n² ≤ 100n for all n ≥ 1", False,
      ["It fails once n > 100", "n² is always smaller than 100n", "Inequalities between polynomials always hold eventually"], "It fails once n > 100",
      hints=["Divide both sides by n.", "n ≤ 100?"], steps=["n² ≤ 100n ⇔ n ≤ 100. False for n = 101. Invalid."])
valid("mf_ineq_v_log", "math_ineq", 2, "log₂ n ≤ n for all n ≥ 1", True,
      ["n < 2ⁿ for every n ≥ 1, so log₂ n < n", "log n is negative for n ≥ 1", "It only holds for n ≥ 16"], "n < 2ⁿ for every n ≥ 1, so log₂ n < n",
      hints=["Apply 2^(…) to both sides.", "Is n ≤ 2ⁿ?"], steps=["log₂ n ≤ n ⇔ n ≤ 2ⁿ, true for every n ≥ 1. Valid."])
valid("mf_ineq_v_neg", "math_ineq", 2, "−2n ≤ 6  ⇒  n ≤ −3", False,
      ["Dividing by a negative number reverses the inequality", "You must add 2 to both sides", "It is valid"], "Dividing by a negative number reverses the inequality",
      hints=["What happens when you divide both sides by −2?", "n = 0 satisfies −2n ≤ 6."], steps=["−2n ≤ 6 ⇔ n ≥ −3 (flip when dividing by −2). Invalid."])
mistake("mf_ineq_mistake", "math_ineq", 3, "bounding n² + 4n", ["n² + 4n", "≤ n² + 4   (for n ≥ 1)", "≤ 5n²"], 2, "n^2 + 4n^2",
        prompt="Find the first incorrect line. Then write a valid replacement for that line's right-hand side (an upper bound for n ≥ 1 that the next line can use). " + INPUT_NOTE,
        label="A valid line 2", traps=[("n^2 + 4", "4n ≤ 4 is false for n > 1.")], hints=["Is 4n ≤ 4 for n ≥ 1?", "For n ≥ 1, n ≤ n², so 4n ≤ 4n²."],
        steps=["Line 2 is false: 4n > 4 when n > 1.", "Use 4n ≤ 4n² (n ≥ 1): n² + 4n ≤ n² + 4n² = 5n²."])

# ============================================================================ Math used in T(n)
simp("mf_tn_basic", "math_tn", 1, "Simplify a loop's T(n)", "T(n) = 1 + (n + 1) + n + n", "3n + 2", "combined",
     traps=[("3n + 1", "Two constants: 1 and the 1 in (n + 1).")], extra=[theta("Growth rate", "n")],
     hints=["1 (initialize) + (n + 1) (tests) + n + n (body).", "Add n terms and constants separately."], steps=["T(n) = 1 + n + 1 + n + n = 3n + 2 → Θ(n)"])
simp("mf_tn_sum", "math_tn", 3, "A T(n) with a summation", "T(n) = 1 + Σᵢ₌₁ⁿ (1 + i)", "(n^2 + 3n + 2)/2", "expanded",
     traps=[("1 + n(n + 1)/2", "Σ(1 + i) = Σ 1 + Σ i = n + n(n + 1)/2.")], extra=[theta("Growth rate", "n^2")],
     hints=["Split the summation.", "1 + n + n(n + 1)/2, then a common denominator."],
     steps=["T(n) = 1 + n + n(n + 1)/2", "= (2 + 2n + n² + n)/2 = (n² + 3n + 2)/2 → Θ(n²)"])
simp("mf_tn_shift", "math_tn", 1, "Loop from 2 to n", "T(n) = 3 + 2(n − 1) + 4", "2n + 5", "combined",
     traps=[("2n + 6", "2(n − 1) = 2n − 2, so 3 − 2 + 4 = 5.")], hints=["Distribute 2(n − 1).", "3 + 2n − 2 + 4."], steps=["T(n) = 3 + 2n − 2 + 4 = 2n + 5"])
simp("mf_tn_tri", "math_tn", 2, "Dependent loop T(n)", "T(n) = n(n − 1)/2 + n + 1", "n^2/2 + n/2 + 1", "expanded",
     extra=[theta("Growth rate", "n^2")], traps=[("n^2/2 - n/2 + 1", "−n/2 + n = +n/2.")],
     hints=["Expand n(n − 1)/2.", "n²/2 − n/2 + n + 1."], steps=["T(n) = n²/2 − n/2 + n + 1 = n²/2 + n/2 + 1 → Θ(n²)"])
simp("mf_tn_log", "math_tn", 2, "Logarithmic T(n)", "T(n) = 3 log(n²) + 2", "6log(n) + 2", "log_simple",
     extra=[theta("Growth rate", "log(n)")], traps=[("3*log(n)^2 + 2", "log(n²) = 2 log n, not (log n)².")],
     hints=["Power rule.", "3 · 2 log n."], steps=["T(n) = 3 · 2 log n + 2 = 6 log n + 2 → Θ(log n)"])
shown("mf_tn_work", "math_tn", 2, "Simplify T(n), showing work", "T(n) = (n + 1) + n(n + 1) + n²", "(n + 1) + n(n + 1) + n^2",
      ["n + 1 + n^2 + n + n^2", "2n^2 + 2n + 1"], "2n^2 + 2n + 1", "combined", extra=[theta("Growth rate", "n^2")],
      hints=["Distribute n(n + 1).", "Group the n², n and constant terms."])
apply("mf_tn_apply_nlogn", "math_tn", 4, "Doubling outer loop, linear inner loop", [
    choice("The outer loop's values of i form…", ["a geometric sequence (doubling)", "an arithmetic sequence", "neither"], "a geometric sequence (doubling)"),
    expr("Outer iterations (n a power of 2)", "log(n) + 1", traps=[("log(n)", "i ≤ n includes i = n: exponents 0..log n.")]),
    expr("Total times 'work' runs", "n log(n) + n", traps=[("n^2", "The outer loop runs about log n times, not n.")]),
    theta("Growth rate", "n log(n)")],
    ["i = 1, 2, 4, …, n.", "Each outer iteration does n inner iterations: n(log n + 1)."],
    ["Outer: i = 2⁰, …, 2^(log n): log n + 1 iterations", "Total: n(log n + 1) = n log n + n → Θ(n log n)"],
    code="i := 1\nwhile i ≤ n\n    for j := 1 to n\n        work\n    i := 2i")
staged("mf_tn_steps", "math_tn", 3, "Step by step: T(n) = 1 + (n + 1) + Σᵢ₌₁ⁿ (i + 1)", "T(n) = 1 + (n + 1) + Σᵢ₌₁ⁿ (i + 1)", [
    choice("Step 1 · How do you handle the summation?", ["Split it: Σ i + Σ 1, then use n(n + 1)/2", "It equals n + 1", "Use the geometric series formula"],
           "Split it: Σ i + Σ 1, then use n(n + 1)/2"),
    expr("Step 2 · The summation as a closed form", "n(n + 1)/2 + n", traps=[("n(n + 1)/2 + 1", "Σᵢ₌₁ⁿ 1 = n.")]),
    expr("Step 3 · T(n), expanded", "(n^2 + 5n + 4)/2", "expanded", [("(n^2 + 3n + 4)/2", "1 + (n + 1) adds another n: n/2 + n + n = 5n/2.")]),
    theta("Step 4 · Growth rate", "n^2")],
    ["Σ(i + 1) = Σ i + Σ 1.", "1 + n + 1 + n(n + 1)/2 + n, over a common denominator 2."],
    ["Σ(i + 1) = n(n + 1)/2 + n", "T(n) = 2 + n + n(n + 1)/2 + n = (n² + 5n + 4)/2 → Θ(n²)"])

# ============================================================================ Mixed simplification (intermediate work required)
shown("mf_mix_logs", "math_mixed", 3, "Log rules twice", "x log(x⁴) + 2x log(x²)", "x*log(x^4) + 2x*log(x^2)",
      ["4x log(x) + 4x log(x)", "8x log(x)"], "8x log(x)", "log_simple",
      hints=["Power rule on each log.", "4x log x + 4x log x."])
shown("mf_mix_exp", "math_mixed", 3, "Exponents in a quotient", "(2ⁿ)² / 2ⁿ⁻¹", "(2^n)^2 / 2^(n-1)", ["2^(2n) / 2^(n-1)", "2^(2n - (n-1))", "2^(n+1)"],
      "2^(n + 1)", traps=[("2^(n - 1)", "2n − (n − 1) = n + 1: subtracting a negative.")], hints=["(2ⁿ)² = 2²ⁿ.", "Quotient rule: 2n − (n − 1)."])
shown("mf_mix_fracs", "math_mixed", 3, "Difference of two sum formulas", "n(n + 1)/2 − n(n − 1)/2", "n(n + 1)/2 - n(n - 1)/2",
      ["(n^2 + n)/2 - (n^2 - n)/2", "(n^2 + n - n^2 + n)/2", "n"], "n", "combined",
      traps=[("0", "Subtracting (n² − n) gives +n, so the numerator is 2n.")], hints=["Expand both numerators.", "Common denominator 2: subtract numerators carefully."])
shown("mf_mix_logs2", "math_mixed", 3, "Combine log terms", "log(n⁴) − log(n²) + log 8", "log(n^4) - log(n^2) + log(8)",
      ["4log(n) - 2log(n) + 3", "2log(n) + 3"], "2log(n) + 3", "log_simple", hints=["Power rule on the n terms; log₂ 8 = 3.", "4 log n − 2 log n."])
shown("mf_mix_squares", "math_mixed", 3, "Expand and cancel", "(n + 2)² − n(n + 4)", "(n + 2)^2 - n(n + 4)",
      ["n^2 + 4n + 4 - n^2 - 4n", "4"], "4", traps=[("8n + 4", "−n(n + 4) = −n² − 4n."), ("4n + 4", "(n + 2)² = n² + 4n + 4; the 4n terms cancel.")],
      hints=["Expand both parts.", "n² + 4n + 4 − n² − 4n."])
simp("mf_mix_monomial", "math_mixed", 3, "Several exponent rules", "(x³y²)² · x / (x²y)", "x^5y^3", "monomial",
     traps=[("x^7y^4", "Divide by x²y at the end: x⁷/x² and y⁴/y."), ("x^6y^4", "Don't forget the extra · x.")],
     hints=["(x³y²)² = x⁶y⁴.", "x⁶y⁴ · x = x⁷y⁴; then divide by x²y."], steps=["(x³y²)² = x⁶y⁴", "x⁶y⁴ · x = x⁷y⁴", "x⁷y⁴ / (x²y) = x⁵y³"])
shown("mf_mix_sums", "math_mixed", 4, "Two summations", "Σᵢ₌₁ⁿ i + Σᵢ₌₁ⁿ (n − i)", "n(n + 1)/2 + (n^2 - n(n + 1)/2)",
      ["n(n + 1)/2 + n^2 - n(n + 1)/2", "n^2"], "n^2", traps=[("n(n + 1)", "Σ(n − i) = n·n − Σ i.")],
      hints=["Σᵢ₌₁ⁿ (n − i) = Σ n − Σ i = n² − n(n + 1)/2. Start your work from that.", "The two n(n + 1)/2 terms cancel."])
mistake("mf_mix_mistake", "math_mixed", 3, "a mixed simplification", ["log(n² · n)", "= log(n²) · log(n)", "= 2 log n · log n"], 2,
        "log(n^2) + log(n)", hints=["What does the product rule give?", "log(xy) = log x + log y."],
        steps=["Line 2 should be log(n²) + log(n) = 2 log n + log n = 3 log n. (Or simplify n² · n = n³ first: log(n³) = 3 log n.)"])
shown("mf_mix_tn", "math_mixed", 4, "Simplify and classify a T(n)", "T(n) = n log(n²) + n(n − 1)/2", "n*log(n^2) + n(n - 1)/2",
      ["2n log(n) + (n^2 - n)/2", "2n log(n) + n^2/2 - n/2"], "n^2/2 + 2n log(n) - n/2", "log_simple", extra=[theta("Growth rate", "n^2")],
      hints=["Power rule, then expand the fraction.", "n² beats n log n."])
