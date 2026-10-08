"""Topic / type catalog shared by the backend and templates."""

COMPLEXITY_TOPICS = {
    "fundamentals": "Constant & linear work",
    "sequential": "Sequential operations",
    "conditionals": "Conditional branches",
    "nested_loops": "Nested loops",
    "multi_variable": "Multiple input sizes (n, m, k)",
    "logarithmic": "Logarithmic loops",
    "irregular_loops": "Irregular / dependent loops",
    "recursion": "Recursion",
    "bounds": "O / Θ / Ω bounds",
    "cases": "Best / average / worst case",
    "growth_rates": "Growth rates & comparing algorithms",
}

PSEUDO_TOPICS = {
    "pc_loops": "Loops & accumulation",
    "pc_conditionals": "Conditionals",
    "pc_arrays": "Array manipulation",
    "pc_counting": "Counting",
    "pc_searching": "Searching",
    "pc_sorting": "Sorting",
    "pc_numbers": "Number algorithms",
    "pc_greedy": "Greedy algorithms",
    "pc_recursion": "Recursion",
}

TN_TOPICS = {
    "tn_constant": "Constant-time statements",
    "tn_single": "Single loops",
    "tn_sequential": "Sequential loops",
    "tn_nested": "Nested loops",
    "tn_dependent": "Dependent loops & summations",
    "tn_log": "Logarithmic loops",
    "tn_multi": "Multiple input sizes",
    "tn_conditional": "Conditionals (best / worst)",
    "tn_algorithms": "Common algorithms",
}

TN_LEVELS = {
    1: "Level 1 · Constant-time statements",
    2: "Level 2 · Single loops",
    3: "Level 3 · Sequential loops",
    4: "Level 4 · Nested loops",
    5: "Level 5 · Dependent loops",
    6: "Level 6 · Logarithmic loops",
    7: "Level 7 · Multiple input variables",
    8: "Level 8 · Conditionals",
    9: "Level 9 · Common algorithms",
}

PROOF_TOPICS = {
    "pf_poly": "Polynomial bounds",
    "pf_growth": "Growth comparisons",
    "pf_false": "Disproving bounds",
    "pf_construct": "Proof construction",
    "pf_debug": "Proof debugging",
    "pf_limits": "Ratio & limit method",
    "pf_tn": "Proving T(n) bounds",
}

PROOF_LEVELS = {
    1: "Level 1 · Simple polynomial bounds",
    2: "Level 2 · Polynomial expressions",
    3: "Level 3 · Comparing growth classes",
    4: "Level 4 · False statements",
    5: "Level 5 · Limits & advanced",
}

MATH_TOPICS = {
    "math_algebra": "Algebra fundamentals",
    "math_exp": "Exponent rules",
    "math_log": "Logarithm rules",
    "math_poly": "Polynomial simplification",
    "math_factor": "Factoring",
    "math_frac": "Fractions & rational expressions",
    "math_aseq": "Arithmetic sequences",
    "math_aseries": "Arithmetic series & summations",
    "math_gseq": "Geometric sequences",
    "math_growth": "Growth-rate comparisons",
    "math_ineq": "Mathematical inequalities",
    "math_tn": "Math used in T(n)",
    "math_mixed": "Mixed simplification",
}

MATH_LEVELS = {
    1: "Level 1 · One rule",
    2: "Level 2 · Two rules",
    3: "Level 3 · Multi-step",
    4: "Level 4 · Algorithm analysis",
}

TRACK_LABELS = {"complexity": "Complexity", "pseudocode": "Pseudocode", "tn": "T(n) Analysis", "proofs": "Proofs",
                "math": "Discrete Math Foundations"}

TOPICS = {**COMPLEXITY_TOPICS, **PSEUDO_TOPICS, **TN_TOPICS, **PROOF_TOPICS, **MATH_TOPICS}

COMPLEXITY_TYPES = {
    "identify": "A · Identify the complexity",
    "bounds": "B · Big O vs Θ vs Ω",
    "analyze": "C · Analyze the code",
    "count": "D · Count operations",
    "compare": "E · Compare algorithms",
    "cases": "F · Best / average / worst case",
    "generated": "Generated challenge",
}

PSEUDO_TYPES = {
    "fill": "A · Fill in the blank",
    "order": "B · Put the steps in order",
    "complete": "C · Complete the algorithm",
    "write": "D · Write from a description",
    "debug": "E · Find the bug",
    "trace": "F · Trace the pseudocode",
    "to_complexity": "G · Pseudocode → complexity",
}

TN_TYPES = {"tn": "T(n) derivation"}

PROOF_TYPES = {
    "proof": "A · Prove or disprove",
    "proof_fill": "B · Complete the proof",
    "proof_debug": "C · Find the flaw",
    "proof_limit": "D · Ratio & limit method",
}

MATH_TYPES = {
    "math_rule": "A · What rule do I use?",
    "math_simplify": "B · Simplify",
    "math_steps": "C · Step-by-step",
    "math_work": "D · Show your work",
    "math_valid": "E · Valid or invalid?",
    "math_mistake": "F · Find the mistake",
    "math_bound": "G · Inequalities & constants",
    "math_apply": "H · Algorithm application",
}

TYPES = {**COMPLEXITY_TYPES, **PSEUDO_TYPES, **TN_TYPES, **PROOF_TYPES, **MATH_TYPES}

LEVELS = {
    1: "Level 1 · Fundamentals",
    2: "Level 2 · Nested & sequential",
    3: "Level 3 · Different bounds",
    4: "Level 4 · Logarithmic behavior",
    5: "Level 5 · Irregular loops",
    6: "Level 6 · Recursion & advanced",
}


def difficulty_of(level):
    return "beginner" if level <= 2 else ("intermediate" if level <= 4 else "advanced")


# Session "topic" filter -> predicate over an exercise row
SESSION_TOPICS = {
    "big_o": "Big O",
    "big_theta": "Big Theta",
    "big_omega": "Big Omega",
    "loops": "Loops",
    "nested": "Nested loops",
    "logarithms": "Logarithms",
    "recursion": "Recursion",
    "mixed_complexity": "Mixed complexity",
    "pseudocode": "Pseudocode",
    "tn": "T(n) derivation",
    "proofs": "Complexity proofs",
    "math": "Discrete math foundations",
    "mixed": "Mixed (everything)",
}

TOPIC_TAGS = {
    "fundamentals": ["loops"], "sequential": ["loops"], "conditionals": ["loops"],
    "nested_loops": ["nested"], "multi_variable": ["nested"], "irregular_loops": ["nested"],
    "logarithmic": ["logarithms"], "recursion": ["recursion"], "pc_recursion": ["recursion"],
    "bounds": ["big_o", "big_theta", "big_omega"], "cases": ["big_theta", "big_omega", "big_o"],
    "growth_rates": ["big_o"],
}
