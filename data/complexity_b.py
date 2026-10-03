"""Complexity-analysis exercises, part 2: levels 4-6 (logarithms, irregular loops, recursion)."""
import math

from data.builders import ident, analyze, count_ex
from engine.growth import ONE, LOGLOG, LOG, LOG2, SQRT, N, NLOG, N2, N3, EXP, FACT

LOGOPTS = [ONE, LOGLOG, LOG, LOG2, SQRT, N, NLOG, N2]


def _doubling(n):
    c, i = 0, 1
    while i < n:
        c += 1
        i *= 2
    return c


def _triangle(n):
    return sum(1 for i in range(1, n + 1) for j in range(1, i + 1))


def _calls_linear(n):
    return 1 if n <= 1 else 1 + _calls_linear(n - 1)


def _calls_double(n):
    return 1 if n <= 1 else 1 + 2 * _calls_double(n - 1)


def _geo_inner(n):
    c, i = 0, 1
    while i < n:
        c += i
        i *= 2
    return c


EXERCISES = [
    # ------------------------------------------------------------------ Level 4
    ident("c4-doubling", 4, "logarithmic", "Doubling up to n", """
        i = 1
        while i < n
            print(i)
            i = i * 2
        """, LOG,
        ["Write down the values i takes: 1, 2, 4, ... When does it reach n?",
         "After k iterations, i = 2ᵏ. The loop stops when 2ᵏ ≥ n.",
         "Solve 2ᵏ = n for k."],
        ["i doubles each iteration: after k iterations, i = 2ᵏ.",
         "The loop stops when 2ᵏ ≥ n, i.e. k ≥ log₂ n.",
         "Iterations ≈ log₂ n, each O(1).",
         "T(n) ∈ Θ(log n). Multiplying the loop variable shrinks the remaining distance geometrically."],
        [("i = i * 2", "multiplicative update → log n"), ("while i < n", "≈ log₂ n iterations")],
        options=LOGOPTS),

    ident("c4-tripling", 4, "logarithmic", "Tripling instead of doubling", """
        i = 1
        while i < n
            i = i * 3
        """, LOG,
        ["After k iterations, what is i?",
         "i = 3ᵏ. Stop when 3ᵏ ≥ n → k = log₃ n.",
         "How does log₃ n relate to log₂ n?"],
        ["After k iterations, i = 3ᵏ; the loop stops once 3ᵏ ≥ n.",
         "Iterations: log₃ n = log₂ n / log₂ 3 ≈ 0.63 · log₂ n",
         "Changing the base only multiplies by a constant.",
         "T(n) ∈ Θ(log n). The base of a logarithm doesn't matter asymptotically."],
        [("i = i * 3", "× 3 each time → log₃ n")], options=LOGOPTS),

    ident("c4-n-log-n", 4, "logarithmic", "A logarithmic loop inside a linear loop", """
        for i = 1 to n
            j = 1
            while j < n
                print(i, j)
                j = j * 2
        """, NLOG,
        ["Analyze the inner while loop by itself first.",
         "The inner loop doubles j, so it runs about log₂ n times - for every i.",
         "Multiply: n outer iterations × log n inner iterations."],
        ["Outer loop: n iterations",
         "Inner loop: j = 1, 2, 4, ... < n → ≈ log₂ n iterations (independent of i)",
         "Total: n × log n",
         "T(n) ∈ Θ(n log n)"],
        [("for i = 1 to n", "outer: n"), ("j = j * 2", "inner: log n")], options=LOGOPTS),

    ident("c4-log-outer", 4, "logarithmic", "A linear loop inside a logarithmic loop", """
        i = 1
        while i < n
            for j = 1 to n
                print(i + j)
            i = i * 2
        """, NLOG,
        ["How many times does the OUTER loop run?",
         "The outer loop doubles i: log n iterations. The inner loop always runs n times.",
         "log n × n."],
        ["Outer loop: i = 1, 2, 4, ... → ≈ log₂ n iterations",
         "Inner loop: n iterations each time (its bound doesn't depend on i)",
         "Total: log n × n = n log n → Θ(n log n)",
         "The order of nesting doesn't matter for the product."],
        [("i = i * 2", "outer: log n"), ("for j = 1 to n", "inner: n")], options=LOGOPTS),

    ident("c4-seq-log-linear", 4, "logarithmic", "A logarithmic loop followed by a linear loop", """
        i = n
        while i > 1
            i = i / 2
        for j = 1 to n
            print(j)
        """, N,
        ["These are two separate sections. Analyze each.",
         "First section: log n. Second section: n.",
         "Add, then keep the dominant term."],
        ["Section 1 (halving): ≈ log₂ n", "Section 2 (linear): n",
         "Sequential → T(n) = log n + n", "n dominates log n → Θ(n)"],
        [("i = i / 2", "section 1: log n"), ("for j = 1 to n", "section 2: n")], options=LOGOPTS),

    ident("c4-log-squared", 4, "logarithmic", "Two nested doubling loops", """
        i = 1
        while i < n
            j = 1
            while j < n
                print(i, j)
                j = j * 2
            i = i * 2
        """, LOG2,
        ["Each loop doubles its variable up to n.",
         "Outer: log n. Inner: log n for every outer iteration.",
         "log n × log n."],
        ["Outer loop: log₂ n iterations", "Inner loop: log₂ n iterations each",
         "Total: (log n)² = log² n",
         "Θ(log² n) grows faster than log n but much slower than n."],
        [("i = i * 2", "outer: log n"), ("j = j * 2", "inner: log n")], options=LOGOPTS),

    ident("c4-digits", 4, "logarithmic", "Counting the digits of a number", """
        procedure DigitCount(n)
            count = 0
            while n > 0
                n = n div 10
                count = count + 1
            return count
        """, LOG,
        ["What happens to n each iteration?",
         "Integer division by 10 removes one digit. How many digits does n have?",
         "A number n has about log₁₀ n digits."],
        ["Each iteration divides n by 10 (drops one digit).",
         "Iterations = number of digits ≈ log₁₀ n + 1",
         "log₁₀ n is a constant multiple of log₂ n",
         "T(n) ∈ Θ(log n). Here the input size is the VALUE n; the number of digits is logarithmic in it."],
        [("n = n div 10", "divide by 10 → log n")], options=LOGOPTS),

    ident("c4-binary-search", 4, "logarithmic", "Binary search loop", """
        procedure BinarySearch(A, target)
            low = 0
            high = length(A) - 1
            while low <= high
                mid = floor((low + high) / 2)
                if A[mid] == target
                    return mid
                else if A[mid] < target
                    low = mid + 1
                else
                    high = mid - 1
            return -1
        """, LOG,
        ["How big is the search range [low, high] at the start?",
         "Each iteration discards about half of the range.",
         "How many halvings until the range is empty?"],
        ["Initial range size: n.",
         "Each iteration keeps at most half of the remaining range.",
         "After k iterations the range is ≤ n / 2ᵏ; it becomes empty after ≈ log₂ n + 1 iterations.",
         "Worst case (target absent): Θ(log n). So the running time is O(log n)."],
        [("while low <= high", "≤ log₂ n + 1 iterations"),
         (["low = mid + 1", "high = mid - 1"], "halves the range")], options=LOGOPTS),

    count_ex("c4-count-doubling", 4, "logarithmic", "Counting a doubling loop", """
        count = 0
        i = 1
        while i < n
            count = count + 1
            i = i * 2
        """, "count = count + 1", {"n": 64},
        _doubling,
        ["n/2", "log₂ n", "√n", "n - 1"], "log₂ n", LOG,
        ["For n = 64, list the values of i that pass the test i < 64.",
         "i = 1, 2, 4, 8, 16, 32 - then 64 fails the test.",
         "2ᵏ = n ⇒ k = log₂ n."],
        ["For n = 64: i = 1, 2, 4, 8, 16, 32 → 6 executions (64 stops the loop).",
         "In general: log₂ n executions (when n is a power of 2).",
         "Θ(log n)"],
        [("i = i * 2", "doubling"), ("while i < n", "log₂ n tests pass")],
        expr_fn=lambda n: int(math.log2(n)), options=LOGOPTS),

    ident("c4-i-times-i", 4, "irregular_loops", "Loop until i² reaches n", """
        i = 1
        while i * i <= n
            print(i)
            i = i + 1
        """, SQRT,
        ["The loop variable grows by 1, but the condition compares i² to n.",
         "The loop stops once i > √n.",
         "How many integers are between 1 and √n?"],
        ["The loop continues while i² ≤ n, i.e. i ≤ √n.",
         "i increases by 1, so there are ⌊√n⌋ iterations.",
         "T(n) ∈ Θ(√n): faster than linear, slower than logarithmic.",
         "This is exactly the loop used by trial-division primality testing."],
        [("while i * i <= n", "≈ √n iterations")], options=LOGOPTS),

    # ------------------------------------------------------------------ Level 5
    ident("c5-halving", 5, "logarithmic", "Halving down to 1", """
        i = n
        while i > 1
            print(i)
            i = i / 2
        """, LOG,
        ["Track i: n, n/2, n/4, ... How many steps until it's ≤ 1?",
         "After k iterations i = n / 2ᵏ.",
         "Solve n / 2ᵏ = 1."],
        ["After k iterations, i = n / 2ᵏ.",
         "The loop ends when n / 2ᵏ ≤ 1, i.e. k ≥ log₂ n.",
         "T(n) ∈ Θ(log n). Dividing the problem size by a constant > 1 each step is logarithmic,",
         "just like multiplying the loop variable."],
        [("i = i / 2", "halving → log₂ n iterations")], options=LOGOPTS),

    ident("c5-triangle", 5, "irregular_loops", "Inner loop depends on the outer variable", """
        for i = 1 to n
            for j = 1 to i
                print(i, j)
        """, N2,
        ["The inner loop's bound changes. How many iterations when i = 1? i = 2? i = n?",
         "Total = 1 + 2 + 3 + ... + n.",
         "That sum equals n(n + 1)/2."],
        ["When i = 1 the inner loop runs 1 time, when i = 2 it runs 2 times, ..., when i = n it runs n times.",
         "Total = 1 + 2 + ... + n = n(n + 1)/2",
         "n(n + 1)/2 = ½n² + ½n",
         "Dominant term ½n² → Θ(n²). Half of n² is still quadratic.",
         "Pattern matching 'nested loops' happens to work here, but only because the sum is Θ(n²)."],
        [("for i = 1 to n", "i = 1..n"), ("for j = 1 to i", "i iterations → Σ i = n(n+1)/2")]),

    ident("c5-upper-triangle", 5, "irregular_loops", "Inner loop from i to n", """
        for i = 1 to n
            for j = i to n
                if A[i] == A[j]
                    matches = matches + 1
        """, N2,
        ["How many iterations does the inner loop do when i = 1? When i = n?",
         "It runs n - i + 1 times: n, n - 1, ..., 1.",
         "Sum that sequence."],
        ["Inner iterations for a given i: n - i + 1",
         "Total = n + (n - 1) + ... + 1 = n(n + 1)/2",
         "T(n) ∈ Θ(n²)"],
        [("for j = i to n", "n - i + 1 iterations")]),

    count_ex("c5-count-triangle", 5, "irregular_loops", "Counting a triangular loop", """
        count = 0
        for i = 1 to n
            for j = 1 to i
                count = count + 1
        """, "count = count + 1", {"n": 5},
        _triangle,
        ["n²", "n(n + 1)/2", "2n", "n log n"], "n(n + 1)/2", N2,
        ["For n = 5 add up the inner counts: i = 1 gives 1, i = 2 gives 2, ...",
         "1 + 2 + 3 + 4 + 5.",
         "Gauss: 1 + 2 + ... + n = n(n + 1)/2. What's its dominant term?"],
        ["For n = 5: 1 + 2 + 3 + 4 + 5 = 15.",
         "In general: n(n + 1)/2 = ½n² + ½n",
         "Drop the constant ½ and the lower-order ½n → Θ(n²)"],
        [("for j = 1 to i", "i iterations")],
        expr_fn=lambda n: n * (n + 1) // 2),

    ident("c5-geometric", 5, "irregular_loops", "Doubling outer loop, dependent inner loop", """
        i = 1
        while i < n
            for j = 1 to i
                print(j)
            i = i * 2
        """, N,
        ["Don't pattern-match 'log loop × linear loop'. The inner loop runs i times, and i changes.",
         "The inner counts are 1, 2, 4, 8, ... up to about n.",
         "A geometric series 1 + 2 + 4 + ... + 2ᵏ = 2ᵏ⁺¹ - 1 is at most about 2n."],
        ["Outer loop: i = 1, 2, 4, ..., < n (about log₂ n iterations).",
         "Inner loop: i iterations each time.",
         "Total = 1 + 2 + 4 + ... + 2ᵏ where 2ᵏ < n",
         "Geometric series: = 2ᵏ⁺¹ - 1 < 2n",
         "T(n) ∈ Θ(n) - NOT n log n. The big inner loops happen only at the end."],
        [("i = i * 2", "log n outer iterations"), ("for j = 1 to i", "1 + 2 + 4 + ... < 2n")],
        options=LOGOPTS),

    ident("c5-harmonic", 5, "irregular_loops", "Inner step size grows with i", """
        for i = 1 to n
            j = 1
            while j <= n
                print(i, j)
                j = j + i
        """, NLOG,
        ["For a fixed i, how many iterations does the inner loop do?",
         "j goes 1, 1 + i, 1 + 2i, ... ≤ n: about n / i iterations.",
         "Sum n/1 + n/2 + ... + n/n = n(1 + 1/2 + ... + 1/n). The harmonic sum is Θ(log n)."],
        ["Inner loop for a fixed i: ⌈n / i⌉ iterations.",
         "Total = n/1 + n/2 + n/3 + ... + n/n = n · Hₙ",
         "Hₙ = 1 + 1/2 + ... + 1/n ≈ ln n",
         "T(n) ∈ Θ(n log n). This harmonic pattern appears in the Sieve of Eratosthenes."],
        [("j = j + i", "step i → n / i iterations"), ("for i = 1 to n", "sum over i: harmonic")],
        options=LOGOPTS),

    ident("c5-early-break", 5, "irregular_loops", "An inner loop that breaks early", """
        for i = 1 to n
            for j = 1 to n
                if j == i
                    break
                print(i, j)
        """, N2,
        ["When does the inner loop stop for a given i?",
         "The inner loop breaks when j reaches i, so it does about i iterations.",
         "Sum i over i = 1..n."],
        ["For a given i, the inner loop runs j = 1, ..., i (it breaks at j = i).",
         "That's i iterations → total 1 + 2 + ... + n = n(n + 1)/2",
         "T(n) ∈ Θ(n²). An early exit only helps asymptotically if it cuts the work by more than a constant factor."],
        [("if j == i", "stops after i iterations"), ("for j = 1 to n", "i iterations, not n")]),

    ident("c5-log-i", 5, "irregular_loops", "A doubling loop bounded by i", """
        for i = 1 to n
            j = 1
            while j < i
                j = j * 2
        """, NLOG,
        ["The inner loop doubles j until it reaches i (not n).",
         "For a fixed i, it runs about log₂ i times.",
         "Σ log i for i = 1..n = log(n!). Is that closer to n or n log n?"],
        ["Inner loop for a fixed i: ≈ log₂ i iterations.",
         "Total = log 1 + log 2 + ... + log n = log(n!)",
         "Half of the terms (i ≥ n/2) are each ≥ log(n/2), so the total ≥ (n/2)·log(n/2).",
         "Every term is ≤ log n, so the total ≤ n log n.",
         "T(n) ∈ Θ(n log n)."],
        [("while j < i", "≈ log i iterations")], options=LOGOPTS),

    ident("c5-two-pointers", 5, "irregular_loops", "Two pointers moving toward each other", """
        procedure PairSum(A, target)      // A is sorted
            i = 0
            j = length(A) - 1
            while i < j
                s = A[i] + A[j]
                if s == target
                    return true
                else if s < target
                    i = i + 1
                else
                    j = j - 1
            return false
        """, N,
        ["Focus on the gap j - i. What happens to it each iteration?",
         "Every iteration either increases i or decreases j - the gap shrinks by 1.",
         "The gap starts at n - 1."],
        ["The gap j - i starts at n - 1.",
         "Each iteration moves exactly one pointer, shrinking the gap by 1.",
         "At most n - 1 iterations before i ≥ j.",
         "Worst case Θ(n) → O(n). Counting a quantity that shrinks every step is a powerful reasoning tool."],
        [("while i < j", "gap shrinks by 1 each iteration"), (["i = i + 1", "j = j - 1"], "one pointer moves")]),

    analyze("c5-shrinking-halves", 5, "irregular_loops", "Work that halves each round", """
        k = n
        while k >= 1
            for j = 1 to k
                print(j)
            k = k / 2
        """, N,
        ["The outer loop runs about log n times. Is the inner work the same each time?",
         "Inner work: n, n/2, n/4, ... - a geometric series.",
         "n + n/2 + n/4 + ... < 2n."],
        ["Outer loop: k = n, n/2, n/4, ..., 1 → log n + 1 rounds",
         "Inner loop: k iterations in each round",
         "Total = n + n/2 + n/4 + ... + 1 < 2n",
         "T(n) ∈ Θ(n). Multiplying 'log n rounds × n' would overestimate: most rounds are cheap."],
        [("k = k / 2", "log n rounds"), ("for j = 1 to k", "n + n/2 + ... < 2n")], options=LOGOPTS),

    ident("c5-sqrt-steps", 5, "irregular_loops", "Growing the step each time", """
        i = 0
        s = 0
        while s < n
            i = i + 1
            s = s + i
        """, SQRT,
        ["What is s after k iterations?",
         "s = 1 + 2 + ... + k = k(k + 1)/2.",
         "The loop stops when k²/2 ≈ n."],
        ["After k iterations, s = k(k + 1)/2 ≈ k²/2.",
         "The loop stops when k²/2 ≥ n, i.e. k ≈ √(2n).",
         "T(n) ∈ Θ(√n)"],
        [("s = s + i", "s grows like k²/2")], options=LOGOPTS),

    ident("c5-branch-on-n", 5, "conditionals", "A branch that depends on n itself", """
        if n > 1000
            for i = 1 to n
                print(i)
        else
            for i = 1 to n
                for j = 1 to n
                    print(i, j)
        """, N,
        ["Asymptotic analysis describes behavior for LARGE n.",
         "For every n > 1000, which branch runs?",
         "The quadratic branch only runs for n ≤ 1000: that's bounded by a constant."],
        ["For n ≤ 1000 the else-branch runs, costing at most 1000² = constant.",
         "For all n > 1000 the if-branch runs: n iterations.",
         "Big-O only needs T(n) ≤ c·g(n) for n ≥ n₀. Choose n₀ = 1001.",
         "T(n) ∈ Θ(n). Unlike a data-dependent branch, this condition is fixed by n."],
        [("if n > 1000", "large n always takes this branch"), ("for j = 1 to n", "only for small n")]),

    ident("c5-amortized-stack", 5, "irregular_loops", "Nested loops, amortized", """
        procedure NextGreater(A)
            S = empty stack
            for i = 0 to length(A) - 1
                while S is not empty and A[top(S)] < A[i]
                    pop(S)
                push(S, i)
        """, N,
        ["The inner while loop can run many times for one i. Can it run many times for EVERY i?",
         "Each index is pushed exactly once. How many times can it be popped?",
         "Total pops ≤ total pushes = n."],
        ["Each index is pushed onto S exactly once → n pushes.",
         "Each pop removes an index that was pushed earlier, so total pops ≤ n.",
         "Total inner-loop iterations over the whole run ≤ n (amortized).",
         "T(n) = n (outer) + ≤ n (all pops) ∈ Θ(n)",
         "Nested loops do NOT automatically mean n²."],
        [("pop(S)", "≤ n pops in total"), ("push(S, i)", "exactly n pushes")]),

    ident("c5-triple-dependent", 5, "irregular_loops", "Three dependent loops", """
        for i = 1 to n
            for j = 1 to i
                for k = 1 to j
                    count = count + 1
        """, N3,
        ["The innermost loop runs j times. The middle one runs i times.",
         "For a fixed i, the inner two loops do 1 + 2 + ... + i = i(i + 1)/2 steps.",
         "Sum i²/2 over i = 1..n."],
        ["Innermost: j iterations", "Middle + innermost for a fixed i: Σⱼ j = i(i + 1)/2",
         "Total: Σᵢ i(i + 1)/2 ≈ n³/6",
         "T(n) ∈ Θ(n³). The 1/6 is a constant; the cubic growth remains."],
        [("for k = 1 to j", "j iterations"), ("for j = 1 to i", "Σ j = i(i+1)/2")]),

    ident("c5-loglog", 5, "logarithmic", "Squaring the loop variable", """
        i = 2
        while i < n
            i = i * i
        """, LOGLOG,
        ["Track i: 2, 4, 16, 256, ... Write i as a power of 2.",
         "After k iterations, i = 2^(2ᵏ).",
         "Solve 2^(2ᵏ) = n: 2ᵏ = log n, k = log log n."],
        ["i = 2, 2², 2⁴, 2⁸, ... After k iterations, i = 2^(2ᵏ).",
         "Stop when 2^(2ᵏ) ≥ n ⇔ 2ᵏ ≥ log₂ n ⇔ k ≥ log₂ log₂ n",
         "T(n) ∈ Θ(log log n) - even slower-growing than log n."],
        [("i = i * i", "squaring → log log n")], options=LOGOPTS),

    ident("c5-squared-bound", 5, "irregular_loops", "Inner loop runs i² times", """
        for i = 1 to n
            for j = 1 to i * i
                print(j)
        """, N3,
        ["For a fixed i, how many inner iterations?",
         "i² iterations. Now sum 1² + 2² + ... + n².",
         "Σ i² = n(n + 1)(2n + 1)/6."],
        ["Inner loop: i² iterations",
         "Total = 1² + 2² + ... + n² = n(n + 1)(2n + 1)/6 ≈ n³/3",
         "T(n) ∈ Θ(n³)"],
        [("for j = 1 to i * i", "i² iterations")], options=[ONE, LOG, N, NLOG, N2, N3, EXP, FACT]),

    # ------------------------------------------------------------------ Level 6 - recursion
    ident("c6-rec-minus-one", 6, "recursion", "Recursion that shrinks by 1", """
        function mystery(n)
            if n <= 1
                return
            mystery(n - 1)
        """, N,
        ["Write a recurrence: T(n) = T(?) + (work outside the call).",
         "T(n) = T(n - 1) + c. Unroll it a few times.",
         "T(n) = T(n - k) + kc. When does n - k reach 1?"],
        ["Each call does O(1) work and makes ONE call on n - 1.",
         "Recurrence: T(n) = T(n - 1) + c,   T(1) = c",
         "Unroll: T(n) = T(n - 2) + 2c = ... = T(1) + (n - 1)c",
         "T(n) ∈ Θ(n): a chain of n calls, like a loop."],
        [("mystery(n - 1)", "one call, size n - 1"), ("if n <= 1", "base case")]),

    ident("c6-rec-half", 6, "recursion", "Recursion that halves", """
        function mystery(n)
            if n <= 1
                return
            mystery(n / 2)
        """, LOG,
        ["Write the recurrence: how big is the subproblem?",
         "T(n) = T(n/2) + c.",
         "How many halvings until you reach 1?"],
        ["Recurrence: T(n) = T(n/2) + c",
         "Unroll: T(n) = T(n/4) + 2c = ... = T(n/2ᵏ) + kc",
         "n/2ᵏ = 1 when k = log₂ n",
         "T(n) = c·log₂ n + c ∈ Θ(log n) - the recursive version of a halving loop."],
        [("mystery(n / 2)", "one call, half the size")], options=LOGOPTS),

    ident("c6-rec-two-calls", 6, "recursion", "Two recursive calls on n - 1", """
        function mystery(n)
            if n <= 1
                return
            mystery(n - 1)
            mystery(n - 1)
        """, EXP,
        ["How many calls does mystery(n) make directly? Draw the call tree for n = 3.",
         "Each level of the tree has twice as many calls as the level above.",
         "Levels: n. Calls: 1 + 2 + 4 + ... + 2ⁿ⁻¹."],
        ["Recurrence: T(n) = 2T(n - 1) + c",
         "Call tree: level 0 has 1 call, level 1 has 2, level 2 has 4, ...",
         "There are n levels, so total calls = 1 + 2 + ... + 2ⁿ⁻¹ = 2ⁿ - 1",
         "T(n) ∈ Θ(2ⁿ): each extra level doubles the work."],
        [("mystery(n - 1)\n", "call 1"), ("mystery(n - 1)@2", "call 2 → the tree doubles every level")]),

    count_ex("c6-count-calls-linear", 6, "recursion", "Counting recursive calls (one branch)", """
        function f(n)
            if n <= 1
                return 1
            return f(n - 1) + 1
        """, "calls to f", {"n": 5},
        _calls_linear,
        ["n", "2ⁿ - 1", "log₂ n", "n²"], "n", N,
        ["List the calls made when you call f(5).",
         "f(5) → f(4) → f(3) → f(2) → f(1).",
         "One call per value from n down to 1."],
        ["f(5) calls f(4), which calls f(3), f(2), f(1) → 5 calls in total.",
         "In general: n calls, each doing O(1) work.",
         "T(n) ∈ Θ(n)"],
        [("return f(n - 1) + 1", "one call per level")],
        expr_fn=lambda n: n),

    count_ex("c6-count-calls-tree", 6, "recursion", "Counting recursive calls (two branches)", """
        function g(n)
            if n <= 1
                return 1
            return g(n - 1) + g(n - 1)
        """, "calls to g", {"n": 4},
        _calls_double,
        ["2n", "n²", "2ⁿ - 1", "n!"], "2ⁿ - 1", EXP,
        ["Draw the call tree for g(4). How many g(3) calls? g(2)? g(1)?",
         "1 call of g(4), 2 of g(3), 4 of g(2), 8 of g(1).",
         "1 + 2 + 4 + ... + 2ⁿ⁻¹."],
        ["For n = 4: 1 + 2 + 4 + 8 = 15 calls.",
         "In general: 2⁰ + 2¹ + ... + 2ⁿ⁻¹ = 2ⁿ - 1",
         "T(n) ∈ Θ(2ⁿ)"],
        [("return g(n - 1) + g(n - 1)", "two calls → doubles each level")],
        expr_fn=lambda n: 2 ** n - 1),

    ident("c6-merge-sort", 6, "recursion", "Merge sort", """
        procedure MergeSort(A, lo, hi)
            if lo >= hi
                return
            mid = floor((lo + hi) / 2)
            MergeSort(A, lo, mid)
            MergeSort(A, mid + 1, hi)
            Merge(A, lo, mid, hi)        // linear in (hi - lo + 1)
        """, NLOG,
        ["Write the recurrence: two calls on halves plus the cost of Merge.",
         "T(n) = 2T(n/2) + cn. Draw the recursion tree: what is the total work per level?",
         "Each level does cn work in total. How many levels?"],
        ["Recurrence: T(n) = 2T(n/2) + cn",
         "Recursion tree: level k has 2ᵏ subproblems of size n/2ᵏ → total work 2ᵏ · c(n/2ᵏ) = cn per level",
         "Levels: log₂ n (halving until size 1)",
         "T(n) = cn · log₂ n ∈ Θ(n log n)"],
        [("MergeSort(A, lo, mid)", "T(n/2)"), ("MergeSort(A, mid + 1, hi)", "T(n/2)"), ("Merge(A, lo, mid, hi)", "+ cn")],
        options=LOGOPTS + [N3, EXP]),

    ident("c6-rec-loop-minus-one", 6, "recursion", "A loop plus a recursive call on n - 1", """
        function work(n)
            if n <= 0
                return
            for i = 1 to n
                print(i)
            work(n - 1)
        """, N2,
        ["Write the recurrence: loop cost plus one call on n - 1.",
         "T(n) = T(n - 1) + n. Unroll it.",
         "n + (n - 1) + ... + 1."],
        ["Recurrence: T(n) = T(n - 1) + cn",
         "Unroll: T(n) = cn + c(n - 1) + ... + c·1 = c · n(n + 1)/2",
         "T(n) ∈ Θ(n²) - the recursive version of the triangular nested loop."],
        [("for i = 1 to n", "cn at this level"), ("work(n - 1)", "T(n - 1)")]),

    ident("c6-rec-loop-half", 6, "recursion", "A loop plus a recursive call on n / 2", """
        function work(n)
            if n <= 1
                return
            for i = 1 to n
                print(i)
            work(n / 2)
        """, N,
        ["T(n) = T(n/2) + cn. Unroll it.",
         "Work per level: n, n/2, n/4, ...",
         "Geometric series with ratio ½: sum < 2n."],
        ["Recurrence: T(n) = T(n/2) + cn",
         "Unroll: cn + cn/2 + cn/4 + ... + c",
         "Geometric series: < 2cn",
         "T(n) ∈ Θ(n) - the top level dominates."],
        [("for i = 1 to n", "cn"), ("work(n / 2)", "T(n/2)")], options=LOGOPTS),

    ident("c6-rec-tree-const", 6, "recursion", "Two half-size calls with constant work", """
        function visit(n)
            if n <= 1
                return
            visit(n / 2)
            visit(n / 2)
        """, N,
        ["T(n) = 2T(n/2) + c. Draw the tree.",
         "Level k has 2ᵏ calls, each doing constant work.",
         "The last level has about n calls. Sum 1 + 2 + 4 + ... + n."],
        ["Recurrence: T(n) = 2T(n/2) + c",
         "Level k: 2ᵏ calls × c work",
         "Levels 0..log₂ n: total = c(1 + 2 + ... + n) < 2cn",
         "T(n) ∈ Θ(n) - like visiting every node of a balanced binary tree with n leaves."],
        [("visit(n / 2)\n", "T(n/2)"), ("visit(n / 2)@2", "T(n/2)")], options=LOGOPTS),

    ident("c6-fib", 6, "recursion", "Naive Fibonacci", """
        function Fib(n)
            if n <= 1
                return n
            return Fib(n - 1) + Fib(n - 2)
        """, EXP,
        ["How many recursive calls does each call make?",
         "T(n) = T(n - 1) + T(n - 2) + c. This is bigger than 2T(n - 2) and smaller than 2T(n - 1).",
         "Compare with the two-calls-on-(n - 1) tree."],
        ["Recurrence: T(n) = T(n - 1) + T(n - 2) + c",
         "Upper bound: T(n) ≤ 2T(n - 1) + c → O(2ⁿ)",
         "Lower bound: T(n) ≥ 2T(n - 2) + c → Ω(2^(n/2)) ≈ Ω(1.41ⁿ)",
         "The exact growth is Θ(φⁿ) with φ ≈ 1.618, the golden ratio.",
         "Among the choices, O(2ⁿ) is the tightest upper bound. Exponential either way!"],
        [("return Fib(n - 1) + Fib(n - 2)", "two calls, sizes n - 1 and n - 2")]),

    ident("c6-power-good", 6, "recursion", "Fast exponentiation", """
        function Power(x, n)
            if n == 0
                return 1
            half = Power(x, n div 2)
            if n mod 2 == 0
                return half * half
            else
                return half * half * x
        """, LOG,
        ["How many recursive calls does one call make? (The result is stored in half.)",
         "One call on n/2, then constant work.",
         "T(n) = T(n/2) + c."],
        ["Only ONE recursive call per invocation; its result is reused via 'half'.",
         "Recurrence: T(n) = T(n/2) + c",
         "T(n) ∈ Θ(log n)"],
        [("half = Power(x, n div 2)", "one call on n/2"), ("return half * half", "reuses the result: O(1)")],
        options=LOGOPTS),

    ident("c6-power-bad", 6, "recursion", "Exponentiation that recomputes", """
        function Power(x, n)
            if n == 0
                return 1
            if n mod 2 == 0
                return Power(x, n div 2) * Power(x, n div 2)
            else
                return Power(x, n div 2) * Power(x, n div 2) * x
        """, N,
        ["Compare with the version that stores 'half'. How many calls does this one make?",
         "T(n) = 2T(n/2) + c.",
         "Draw the tree: level k has 2ᵏ calls. How many levels?"],
        ["Two calls on n/2 per invocation → T(n) = 2T(n/2) + c",
         "Levels: log₂ n; level k has 2ᵏ calls",
         "Total calls ≈ 1 + 2 + ... + 2^(log n) ≈ 2n",
         "T(n) ∈ Θ(n) - calling the same subproblem twice undoes the benefit of halving."],
        [("return Power(x, n div 2) * Power(x, n div 2)\n", "two calls on n/2")], options=LOGOPTS),

    ident("c6-permutations", 6, "recursion", "Generating all permutations", """
        procedure Permute(A, k)            // call Permute(A, 0); n = length(A)
            if k == length(A)
                print(A)
                return
            for i = k to length(A) - 1
                swap(A[k], A[i])
                Permute(A, k + 1)
                swap(A[k], A[i])
        """, FACT,
        ["At depth k, how many recursive calls does the loop make?",
         "The top call makes n calls, each of those makes n - 1, ...",
         "n × (n - 1) × ... × 1."],
        ["Depth 0: the loop makes n recursive calls",
         "Depth 1: each makes n - 1 calls; depth 2: n - 2; ...",
         "Leaves (complete permutations): n × (n - 1) × ... × 1 = n!",
         "T(n) ∈ Ω(n!) and printing each permutation costs O(n), so the total is O(n · n!).",
         "Among the choices, the growth class is factorial."],
        [("for i = k to length(A) - 1", "n - k choices"), ("Permute(A, k + 1)", "recurse with one fewer choice")]),

    ident("c6-binary-search-rec", 6, "recursion", "Recursive binary search", """
        function Search(A, target, lo, hi)
            if lo > hi
                return -1
            mid = floor((lo + hi) / 2)
            if A[mid] == target
                return mid
            else if A[mid] < target
                return Search(A, target, mid + 1, hi)
            else
                return Search(A, target, lo, mid - 1)
        """, LOG,
        ["There are two recursive calls in the code. How many of them run in a single invocation?",
         "The if/else if/else chooses exactly one, on half of the range.",
         "T(n) = T(n/2) + c."],
        ["Only one branch executes → one recursive call on ≈ half the range.",
         "Recurrence: T(n) = T(n/2) + c",
         "T(n) ∈ Θ(log n) in the worst case.",
         "Two calls appearing in the code ≠ two calls executing!"],
        [("return Search(A, target, mid + 1, hi)", "either this..."), ("return Search(A, target, lo, mid - 1)", "...or this, never both")],
        options=LOGOPTS),

    ident("c6-rec-sum", 6, "recursion", "Recursive array sum", """
        function SumFrom(A, i)
            if i == length(A)
                return 0
            return A[i] + SumFrom(A, i + 1)
        """, N,
        ["What is the problem size, and how does it change per call?",
         "The remaining part of the array shrinks by 1 each call.",
         "T(n) = T(n - 1) + c."],
        ["Problem size: remaining elements n - i.",
         "Each call does O(1) work and recurses on one fewer element.",
         "T(n) = T(n - 1) + c ∈ Θ(n)"],
        [("return A[i] + SumFrom(A, i + 1)", "size n - 1")]),

    analyze("c6-three-way", 6, "recursion", "Three calls on a third of the input", """
        function Split(n)
            if n <= 1
                return
            for i = 1 to n
                print(i)
            Split(n / 3)
            Split(n / 3)
            Split(n / 3)
        """, NLOG,
        ["Write the recurrence: 3 calls on n/3 plus linear work.",
         "T(n) = 3T(n/3) + cn. What is the total work per level of the tree?",
         "Level k: 3ᵏ calls of size n/3ᵏ → cn per level. How many levels?"],
        ["Recurrence: T(n) = 3T(n/3) + cn",
         "Level k: 3ᵏ subproblems × c(n/3ᵏ) = cn",
         "Levels: log₃ n",
         "T(n) = cn · log₃ n ∈ Θ(n log n) - same shape as merge sort."],
        [("for i = 1 to n", "cn per call"), ("Split(n / 3)\n", "3 calls on n/3")],
        options=LOGOPTS + [N3]),

    ident("c6-quicksort-worst", 6, "recursion", "Quicksort with a bad pivot", """
        procedure QuickSort(A, lo, hi)
            if lo >= hi
                return
            p = Partition(A, lo, hi)     // linear time; uses A[hi] as pivot
            QuickSort(A, lo, p - 1)
            QuickSort(A, p + 1, hi)
        """, N2,
        ["Consider an already-sorted array. Where does the pivot end up?",
         "The pivot is the largest element, so one side is empty and the other has n - 1 elements.",
         "T(n) = T(n - 1) + cn."],
        ["Worst case (sorted input, last element as pivot): partition sizes n - 1 and 0.",
         "Recurrence: T(n) = T(n - 1) + cn",
         "Unroll: cn + c(n - 1) + ... = Θ(n²)",
         "The tightest upper bound that holds for EVERY input is O(n²).",
         "(Average case is Θ(n log n) - see the best/average/worst exercises.)"],
        [("p = Partition(A, lo, hi)", "cn"), ("QuickSort(A, lo, p - 1)", "size n - 1 in the worst case")]),
]
