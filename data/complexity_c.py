"""Complexity-analysis exercises, part 3: O/Θ/Ω bounds (Mode B), cases (Mode F), comparisons (Mode E)."""
from data.builders import bounds_ex, statements_ex, cases_ex, compare_ex
from engine.growth import ONE, LOG, SQRT, N, NLOG, N2, N3, EXP, FACT

CLS7 = [ONE, LOG, N, NLOG, N2, N3, EXP]
CLS_SMALL = [ONE, LOG, SQRT, N, NLOG, N2]
CLS_BIG = [N, NLOG, N2, N3, EXP, FACT]

BOUND_HINTS = [
    "Find the dominant term: the one that grows fastest as n → ∞.",
    "Big O: any function growing AT LEAST as fast as the dominant term is a valid upper bound. "
    "Big Ω: any function growing AT MOST as fast is a valid lower bound.",
    "Θ requires BOTH: it must be an upper bound and a lower bound at the same time - only one class fits.",
]

EXERCISES = [
    bounds_ex("cb-quadratic", 3, "Bounds of a quadratic", "3n² + 7n + 4", N2,
        ["Dominant term: 3n² (7n and 4 grow more slowly).",
         "Upper bound: for n ≥ 1, 3n² + 7n + 4 ≤ 3n² + 7n² + 4n² = 14n² → f ∈ O(n²) with c = 14, n₀ = 1.",
         "Since n² ≤ n³ ≤ 2ⁿ (for n ≥ 10), f ∈ O(n³) and O(2ⁿ) too: valid but loose upper bounds.",
         "Lower bound: f(n) ≥ 3n² for all n ≥ 1 → f ∈ Ω(n²) with c = 3.",
         "Since n² ≥ n log n ≥ n ≥ log n ≥ 1, f ∈ Ω(n log n), Ω(n), Ω(log n), Ω(1) too: valid but loose.",
         "Only n² is both an upper and a lower bound → f ∈ Θ(n²).",
         "Big O is a CLAIM about an upper bound, not 'the runtime'. O(n³) is true but less informative."],
        BOUND_HINTS, classes=CLS7),

    bounds_ex("cb-linear", 2, "Bounds of a linear function", "5n + 100", N,
        ["The constant 100 matters for small n but not for growth.",
         "Upper: 5n + 100 ≤ 105n for n ≥ 1 → O(n); hence also O(n log n), O(n²), ...",
         "Lower: 5n + 100 ≥ 5n → Ω(n); hence also Ω(log n), Ω(1).",
         "Tight: Θ(n).",
         "O(1) is invalid: no constant c keeps 5n + 100 ≤ c forever."],
        BOUND_HINTS, classes=CLS7),

    bounds_ex("cb-cubic-mixed", 4, "A cubic with a log term", "2n³ + n² log n", N3,
        ["Compare n³ with n² log n: n³ / (n² log n) = n / log n → ∞, so n³ dominates.",
         "Upper: 2n³ + n² log n ≤ 3n³ for n ≥ 1 → O(n³), also O(2ⁿ).",
         "Lower: ≥ 2n³ → Ω(n³), and all slower classes.",
         "Θ(n³). O(n²) is invalid: the n³ term eventually exceeds any c·n²."],
        BOUND_HINTS, classes=CLS7),

    bounds_ex("cb-nlogn", 4, "Bounds with n log n", "n log n + 50n", NLOG,
        ["n log n / n = log n → ∞, so n log n eventually dominates 50n (once log n > 50 it is larger).",
         "Upper: n log n + 50n ≤ 51 n log n for n ≥ 2 → O(n log n), also O(n²), O(n³), O(2ⁿ).",
         "Lower: ≥ n log n → Ω(n log n), Ω(n), Ω(log n), Ω(1).",
         "Θ(n log n). O(n) is invalid even though 50n looks big: log n is unbounded."],
        BOUND_HINTS, classes=CLS7),

    bounds_ex("cb-constant", 1, "Bounds of a constant", "100", ONE,
        ["f(n) = 100 never changes with n.",
         "Upper: 100 ≤ 100·1 → O(1), and therefore O of every growing function too.",
         "Lower: 100 ≥ 1·1 → Ω(1). Ω(log n) is invalid: log n eventually exceeds any constant.",
         "Θ(1)."],
        BOUND_HINTS, classes=CLS7),

    bounds_ex("cb-exp", 5, "Exponential vs polynomial", "2ⁿ + n³", EXP,
        ["2ⁿ / n³ → ∞: any exponential with base > 1 beats any polynomial.",
         "Upper: 2ⁿ + n³ ≤ 2·2ⁿ for n ≥ 10 → O(2ⁿ).",
         "Lower: ≥ 2ⁿ → Ω(2ⁿ), and so Ω(n³), Ω(n²), ..., Ω(1).",
         "Θ(2ⁿ). O(n³) is invalid because 2ⁿ eventually passes c·n³ for any c."],
        BOUND_HINTS, classes=CLS7),

    bounds_ex("cb-log", 3, "Bounds of a logarithm", "log n + 20", LOG,
        ["The constant 20 dominates only while log n < 20.",
         "Upper: log n + 20 ≤ 21 log n for n ≥ 2 → O(log n), and O(√n), O(n), ...",
         "Lower: ≥ log n → Ω(log n), Ω(1).",
         "Θ(log n). O(1) is invalid: log n is unbounded."],
        BOUND_HINTS, classes=CLS_SMALL),

    bounds_ex("cb-small-coef", 4, "Tiny coefficients don't change the class", "n²/1000 − 50n", N2,
        ["For small n this is negative or small, but asymptotics looks at large n.",
         "Upper: n²/1000 − 50n ≤ n²/1000 → O(n²).",
         "Lower: for n ≥ 100000, 50n ≤ n²/2000, so f(n) ≥ n²/2000 → Ω(n²).",
         "Θ(n²): the coefficient 1/1000 is a constant factor, and constants are ignored.",
         "The n₀ in the definition lets us skip the range where the negative term wins."],
        BOUND_HINTS, classes=CLS7),

    bounds_ex("cb-sqrt", 4, "Square root vs logarithm", "√n + log n", SQRT,
        ["√n / log n → ∞, so √n dominates.",
         "Upper: √n + log n ≤ 2√n → O(√n), O(n), ...",
         "Lower: ≥ √n → Ω(√n), Ω(log n), Ω(1).",
         "Θ(√n)."],
        BOUND_HINTS, classes=CLS_SMALL),

    bounds_ex("cb-factorial", 5, "Factorial vs exponential", "n! + 2ⁿ", FACT,
        ["n! / 2ⁿ = (n/2)·((n-1)/2)·... → ∞, so n! dominates 2ⁿ.",
         "Upper: n! + 2ⁿ ≤ 2·n! for n ≥ 4 → O(n!).",
         "Lower: ≥ n! → Ω(n!), and everything slower.",
         "Θ(n!). O(2ⁿ) is invalid."],
        BOUND_HINTS, classes=CLS_BIG),

    bounds_ex("cb-gauss", 3, "A sum written in closed form", "n(n + 1)/2", N2,
        ["Expand: n(n + 1)/2 = ½n² + ½n.",
         "Upper: ≤ n² for n ≥ 1 → O(n²), O(n³), ...",
         "Lower: ≥ ½n² → Ω(n²), Ω(n), ...",
         "Θ(n²). This is the count of a triangular nested loop."],
        BOUND_HINTS, classes=CLS7),

    bounds_ex("cb-insertion-all-inputs", 6, "Insertion sort over ALL inputs", "the running time of insertion sort",
        None,
        ["Worst case (reverse-sorted): Θ(n²). Best case (already sorted): Θ(n).",
         "Upper bound for every input: every input takes ≤ c·n² → O(n²), and so O(n³), O(2ⁿ).",
         "Lower bound for every input: every input takes ≥ c·n (each element is examined) → Ω(n), Ω(log n), Ω(1).",
         "Ω(n²) is FALSE for the algorithm overall: sorted inputs finish in linear time.",
         "O(n) is FALSE: reverse-sorted inputs take quadratic time.",
         "So there's no single Θ for 'the running time of insertion sort'.",
         "But each CASE has a Θ: worst case Θ(n²), best case Θ(n).",
         "Note: O is not automatically 'worst case' and Ω is not automatically 'best case'. "
         "Here the upper bound happens to come from the worst case and the lower bound from the best case."],
        ["The statement must hold for EVERY input of size n.",
         "What does insertion sort cost on a sorted array? On a reverse-sorted array?",
         "An upper bound must cover the slowest input; a lower bound must hold even for the fastest input."],
        classes=[ONE, LOG, N, NLOG, N2, N3, EXP], o_valid=[N2, N3, EXP], om_valid=[ONE, LOG, N],
        subject="T(n)",
        prompt="Let T(n) be the running time of insertion sort on an arbitrary input of size n (any order). "
               "Which bounds hold for EVERY input?"),

    bounds_ex("cb-linear-search-worst", 4, "Bounds on a worst-case function", "the worst-case running time of linear search",
        N,
        ["W(n) = the maximum time over inputs of size n. For linear search, W(n) = cn (target absent).",
         "W(n) is a single function, so it has a Θ: Θ(n).",
         "Upper bounds: O(n), O(n log n), O(n²), ... Lower bounds: Ω(n), Ω(log n), Ω(1).",
         "The worst case can be described with O, Θ AND Ω - they are different claims about the same function."],
        ["First pin down the function: the worst-case time W(n).",
         "In the worst case the loop checks all n elements.",
         "Now apply O, Θ, Ω to W(n) exactly as you would to 3n + 2."],
        classes=CLS7, subject="W(n)",
        prompt="Let W(n) be the WORST-CASE running time of linear search on an array of size n. "
               "Answer each part about the function W(n)."),

    statements_ex("cb-statements-T", 3, "Valid bound or tight bound?",
        "Let T(n) = 4n² + 3n + 20. Which statements are true?",
        [("T(n) ∈ O(n³)", True, "True: n³ grows faster, so it's a valid (loose) upper bound."),
         ("T(n) ∈ O(n²)", True, "True: 4n² + 3n + 20 ≤ 27n² for n ≥ 1."),
         ("T(n) ∈ Θ(n²)", True, "True: it's both O(n²) and Ω(n²). This is the most informative statement."),
         ("T(n) ∈ Ω(n²)", True, "True: T(n) ≥ 4n²."),
         ("T(n) ∈ Ω(n)", True, "True but loose: T grows at least linearly (in fact quadratically)."),
         ("T(n) ∈ Θ(n³)", False, "False: T is not Ω(n³); n³ eventually outgrows c·T(n) for any c."),
         ("T(n) ∈ O(n)", False, "False: 4n² eventually exceeds c·n for any constant c."),
         ("T(n) ∈ Ω(n³)", False, "False: T cannot stay above c·n³.")],
        BOUND_HINTS,
        ["Dominant term: 4n² → T(n) ∈ Θ(n²).",
         "Every O(g) with g growing at least as fast as n² is true (n², n³).",
         "Every Ω(g) with g growing at most as fast as n² is true (n², n).",
         "Θ is only true for n².",
         "A mathematically valid bound (O(n³), Ω(n)) is not the same as the most informative tight bound (Θ(n²))."],
        formula="T(n) = 4n² + 3n + 20"),

    statements_ex("cb-misconceptions", 4, "Common misconceptions",
        "Which of these statements about asymptotic notation are true?",
        [("If an algorithm is O(n²), it can't also be O(n³).", False,
          "False: O is an upper bound. Anything that's O(n²) is automatically O(n³)."),
         ("An algorithm whose running time is Θ(n) is also O(n²).", True,
          "True: Θ(n) implies O(n), and O(n) ⊂ O(n²)."),
         ("Ω describes the best case and O describes the worst case.", False,
          "False: O, Ω and Θ describe functions. You can give an O, Ω, or Θ bound for the best case, the worst case, or the average case."),
         ("The worst-case running time of binary search is Θ(log n).", True,
          "True: the worst-case function W(n) is ≈ log₂ n, so W(n) ∈ Θ(log n)."),
         ("If f(n) ∈ Θ(g(n)), then f(n) ∈ O(g(n)) and f(n) ∈ Ω(g(n)).", True,
          "True: this is the definition of Θ."),
         ("3n + 5 ∈ O(1) because 3 and 5 are constants.", False,
          "False: the n term is unbounded; no constant c satisfies 3n + 5 ≤ c for all large n."),
         ("An O(n) algorithm is always faster than an O(n²) algorithm.", False,
          "False: O only bounds growth. Constants, lower-order terms, and small n can make the O(n²) algorithm faster in practice - and an O(n²) algorithm might even be Θ(n).")],
        BOUND_HINTS,
        ["O = upper bound, Ω = lower bound, Θ = both.",
         "Bounds are about functions; best/worst/average case tells you WHICH function.",
         "Bounds say nothing about constants or small inputs."]),

    statements_ex("cb-code-bounds", 3, "Bounds on code",
        "The code below runs in exactly 2n² + n steps for every input. Which statements are true?",
        [("Its running time is O(n²).", True, "True: 2n² + n ≤ 3n²."),
         ("Its running time is O(2ⁿ).", True, "True but uninformative: 2ⁿ outgrows n²."),
         ("Its running time is Ω(n).", True, "True but loose."),
         ("Its running time is Θ(n²).", True, "True: tight in both directions."),
         ("Its running time is Θ(n).", False, "False: not O(n)."),
         ("Its running time is Ω(n³).", False, "False: n³ outgrows the running time.")],
        BOUND_HINTS,
        ["Nested loops n × n plus a single loop n: T(n) = 2n² + n (as given).",
         "Because the code does the same work for every input, its running time is ONE function of n with a single Θ.",
         "Θ(n²); valid looser bounds include O(n³), O(2ⁿ), Ω(n), Ω(1)."],
        src="""
            for i = 1 to n
                for j = 1 to n
                    A[i][j] = A[i][j] * 2 + 1
            for i = 1 to n
                print(A[i][i])
            """),

    # ------------------------------------------------------------------ Mode F - cases
    cases_ex("cf-linear-search", 3, "Linear search", """
        procedure LinearSearch(A, target)
            for i = 0 to length(A) - 1
                if A[i] == target
                    return i
            return -1
        """, ONE, N, N,
        ["Best case: where could the target be so the loop stops immediately?",
         "Worst case: target in the last position or absent. Average: if the target is equally likely anywhere, how many checks on average?",
         "Average ≈ n/2 checks - a constant times n."],
        ["Best case: target at A[0] → 1 comparison → Θ(1).",
         "Worst case: target absent → n comparisons → Θ(n).",
         "Average case (target present, uniformly random position): (1 + 2 + ... + n)/n = (n + 1)/2 → Θ(n).",
         "Running time over ALL inputs: O(n) and Ω(1). No single Θ covers all inputs, but each case has one.",
         "Careful: 'Ω(1)' here comes from the best case, but Ω doesn't MEAN best case. The worst case is Θ(n), so it is also Ω(n)."],
        [("if A[i] == target", "may stop at the first check"), ("for i = 0 to length(A) - 1", "up to n iterations")],
        statement=("Which statement is correct?",
                   ["The worst-case running time is Ω(n).",
                    "Linear search is Ω(1), so its worst case is Θ(1).",
                    "O(n) means linear search always takes n steps."],
                   "The worst-case running time is Ω(n).",
                   {"The worst-case running time is Ω(n).": "Correct: W(n) = n, which is Ω(n) (and Θ(n)). Ω can describe the worst case.",
                    "Linear search is Ω(1), so its worst case is Θ(1).": "No: Ω(1) is a lower bound over all inputs; it says nothing tight about the worst case.",
                    "O(n) means linear search always takes n steps.": "No: O(n) is an upper bound. Many inputs finish sooner."})),

    cases_ex("cf-binary-search", 4, "Binary search", """
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
        """, ONE, LOG, LOG,
        ["Best case: what if the target is exactly at the first mid?",
         "Worst case: the range halves until it's empty.",
         "Average: most elements sit at the deepest levels of the 'search tree'."],
        ["Best case: target at the first midpoint → 1 iteration → Θ(1).",
         "Worst case: ≈ log₂ n + 1 iterations → Θ(log n).",
         "Average case: about half the elements need the full log₂ n steps, so the average is ≈ log₂ n - 1 → Θ(log n).",
         "Overall: O(log n) and Ω(1)."],
        [("if A[mid] == target", "best case: found immediately"), ("while low <= high", "≤ log₂ n + 1 iterations")],
        options=[ONE, LOG, SQRT, N, NLOG, N2]),

    cases_ex("cf-selection-sort", 4, "Selection sort", """
        procedure SelectionSort(A)
            n = length(A)
            for i = 0 to n - 2
                minIndex = i
                for j = i + 1 to n - 1
                    if A[j] < A[minIndex]
                        minIndex = j
                swap(A[i], A[minIndex])
        """, N2, N2, N2,
        ["Does anything in the loops stop early depending on the data?",
         "The inner loop always scans the entire unsorted suffix.",
         "(n - 1) + (n - 2) + ... + 1 comparisons for every input."],
        ["Comparisons: (n - 1) + (n - 2) + ... + 1 = n(n - 1)/2 for EVERY input.",
         "Best = average = worst = Θ(n²).",
         "Because every case is Θ(n²), we can say selection sort's running time is Θ(n²), full stop.",
         "Contrast: insertion sort's best case is Θ(n)."],
        [("for j = i + 1 to n - 1", "always scans the whole suffix")],
        statement=("Which statement is correct?",
                   ["Selection sort runs in Θ(n²) on every input.",
                    "On a sorted array, selection sort runs in Θ(n).",
                    "Selection sort is O(n²) but not Ω(n²)."],
                   "Selection sort runs in Θ(n²) on every input.",
                   {"Selection sort runs in Θ(n²) on every input.": "Correct: the comparisons don't depend on the data.",
                    "On a sorted array, selection sort runs in Θ(n).": "No: it still scans every suffix. It performs fewer writes, not fewer comparisons.",
                    "Selection sort is O(n²) but not Ω(n²).": "No: every input needs n(n - 1)/2 comparisons, so it's Ω(n²)."})),

    cases_ex("cf-insertion-sort", 5, "Insertion sort", """
        procedure InsertionSort(A)
            for i = 1 to length(A) - 1
                key = A[i]
                j = i - 1
                while j >= 0 and A[j] > key
                    A[j + 1] = A[j]
                    j = j - 1
                A[j + 1] = key
        """, N, N2, N2,
        ["How many times does the while loop run if the array is already sorted?",
         "If the array is reverse-sorted, the while loop shifts every earlier element.",
         "For random input, on average each key moves past about half of the earlier elements."],
        ["Best case (already sorted): the while test fails immediately → n - 1 checks → Θ(n).",
         "Worst case (reverse-sorted): i shifts for element i → 1 + 2 + ... + (n - 1) = Θ(n²).",
         "Average case (random order): about i/2 shifts for element i → ≈ n²/4 → Θ(n²).",
         "Overall: O(n²) and Ω(n). Upper bound from the worst case, lower bound from the best case - "
         "but that's a consequence of this algorithm, not what O and Ω mean."],
        [("while j >= 0 and A[j] > key", "0 to i shifts, depending on the data")],
        statement=("Which statement is correct?",
                   ["Insertion sort's best case is Θ(n), and its worst case is Θ(n²).",
                    "Insertion sort is Θ(n²) for every input.",
                    "Insertion sort's best case is O(n²), so it isn't linear."],
                   "Insertion sort's best case is Θ(n), and its worst case is Θ(n²).",
                   {"Insertion sort's best case is Θ(n), and its worst case is Θ(n²).": "Correct: each case is a separate function with its own tight bound.",
                    "Insertion sort is Θ(n²) for every input.": "No: sorted inputs finish in linear time.",
                    "Insertion sort's best case is O(n²), so it isn't linear.": "O(n²) is true of the best case, but it's loose; the best case is Θ(n). An O bound never rules out faster growth."})),

    cases_ex("cf-first-negative", 3, "Early-exit loop", """
        procedure FirstNegative(A)
            for i = 0 to length(A) - 1
                if A[i] < 0
                    return i
            return -1
        """, ONE, N, N,
        ["Best case: where is the first negative number?",
         "Worst case: there's no negative number at all.",
         "Average: assume the first negative is equally likely to be at any position or absent."],
        ["Best case: A[0] < 0 → Θ(1).",
         "Worst case: no negatives → n checks → Θ(n).",
         "Average (first negative uniformly likely at each of the n + 1 outcomes): ≈ n/2 → Θ(n).",
         "The early exit improves the best case only; the average stays linear."],
        [("return i", "early exit"), ("for i = 0 to length(A) - 1", "up to n iterations")]),

    cases_ex("cf-bubble-flag", 5, "Bubble sort with an early-exit flag", """
        procedure BubbleSort(A)
            n = length(A)
            for pass = 0 to n - 2
                swapped = false
                for j = 0 to n - 2 - pass
                    if A[j] > A[j + 1]
                        swap(A[j], A[j + 1])
                        swapped = true
                if swapped == false
                    return
        """, N, N2, N2,
        ["On a sorted array, how many passes happen before the flag stops the sort?",
         "On a reverse-sorted array, the flag never helps.",
         "For random input, many passes are still needed."],
        ["Best case (sorted): one pass with no swaps, then return → n - 1 comparisons → Θ(n).",
         "Worst case (reverse-sorted): every pass needed → n(n - 1)/2 comparisons → Θ(n²).",
         "Average case: Θ(n²) - a random element may need to travel far toward the front, one position per pass.",
         "Overall: O(n²), Ω(n)."],
        [("if swapped == false", "early exit after a clean pass"), ("for j = 0 to n - 2 - pass", "inner pass")]),

    cases_ex("cf-quicksort", 6, "Quicksort (last element as pivot)", """
        procedure QuickSort(A, lo, hi)
            if lo >= hi
                return
            p = Partition(A, lo, hi)    // Θ(hi - lo)
            QuickSort(A, lo, p - 1)
            QuickSort(A, p + 1, hi)
        """, NLOG, NLOG, N2,
        ["Best case: what split sizes make the recursion tree as shallow as possible?",
         "Worst case: the pivot is always the smallest or largest element.",
         "Average: random pivots give reasonably balanced splits most of the time."],
        ["Best case: pivot always splits evenly → T(n) = 2T(n/2) + cn → Θ(n log n).",
         "Worst case: pivot always extreme (e.g. sorted input) → T(n) = T(n - 1) + cn → Θ(n²).",
         "Average case (random input): expected Θ(n log n) (about 1.39 n log₂ n comparisons).",
         "So quicksort is O(n²) overall, and Ω(n log n) for comparison-based reasons."],
        [("p = Partition(A, lo, hi)", "cn per level"), ("QuickSort(A, lo, p - 1)", "split sizes depend on the pivot")],
        options=[ONE, LOG, N, NLOG, N2, N3, EXP]),

    cases_ex("cf-has-duplicate", 5, "Duplicate check with early exit", """
        procedure HasDuplicate(A)
            n = length(A)
            for i = 0 to n - 2
                for j = i + 1 to n - 1
                    if A[i] == A[j]
                        return true
            return false
        """, ONE, N2, N2,
        ["Best case: which pair is compared first?",
         "Worst case: no duplicates, so every pair is compared.",
         "Average: for random arrays without duplicates the loops run to completion; "
         "for this exercise assume inputs usually have no duplicates."],
        ["Best case: A[0] == A[1] → 1 comparison → Θ(1).",
         "Worst case: all distinct → n(n - 1)/2 comparisons → Θ(n²).",
         "Average case (assuming duplicates are rare): Θ(n²).",
         "Overall: O(n²), Ω(1)."],
        [("return true", "early exit on the first duplicate"), ("for j = i + 1 to n - 1", "all pairs in the worst case")]),

    # ------------------------------------------------------------------ Mode E - comparing
    compare_ex("ce-100n-vs-n2", 2, "Constants vs growth",
        "Algorithm A performs 100n operations. Algorithm B performs n² operations.",
        [{"id": "small", "kind": "choice", "label": "For n = 50, which algorithm performs fewer operations?",
          "options": ["A (100n)", "B (n²)", "They're equal"], "answer": "B (n²)"},
         {"id": "cross", "kind": "number", "label": "At what n do they perform the same number of operations?", "answer": 100},
         {"id": "large", "kind": "choice", "label": "For all n larger than that, which is faster?",
          "options": ["A (100n)", "B (n²)"], "answer": "A (100n)"}],
        ["Plug n = 50 into both formulas.",
         "Set 100n = n² and solve for n.",
         "After the crossover, which grows faster?"],
        ["n = 50: A = 5,000 operations, B = 2,500 operations → B is faster.",
         "Crossover: 100n = n² ⇒ n = 100.",
         "For n > 100, n² > 100n, so A (the O(n) algorithm) wins - and the gap widens forever.",
         "Asymptotic analysis is about what happens for large n; constants decide small cases."],
        algos=[{"label": "A", "formula": "100n", "cls": "n", "coef": 100},
               {"label": "B", "formula": "n²", "cls": "n²", "coef": 1}]),

    compare_ex("ce-nlogn-vs-n2", 3, "Sorting 1,024 items",
        "Algorithm A (merge sort) performs about n·log₂ n comparisons. Algorithm B (selection sort) performs about n² comparisons.",
        [{"id": "a", "kind": "number", "label": "For n = 1,024, how many comparisons does A perform? (log₂ 1024 = 10)", "answer": 10240},
         {"id": "b", "kind": "number", "label": "How many comparisons does B perform for n = 1,024?", "answer": 1048576},
         {"id": "ratio", "kind": "choice", "label": "B does roughly how many times more work?",
          "options": ["≈ 10×", "≈ 100×", "≈ 1,000×", "≈ 10,000×"], "answer": "≈ 100×"}],
        ["log₂ 1024 = 10.",
         "1024² = 1,048,576.",
         "Divide the two counts: n² / (n log n) = n / log n."],
        ["A: 1024 × 10 = 10,240 comparisons.",
         "B: 1024 × 1024 = 1,048,576 comparisons.",
         "Ratio: 1,048,576 / 10,240 ≈ 102 → about 100×.",
         "In general the ratio is n / log₂ n, which keeps growing with n."],
        algos=[{"label": "A", "formula": "n log₂ n", "cls": "n log n", "coef": 1},
               {"label": "B", "formula": "n²", "cls": "n²", "coef": 1}]),

    compare_ex("ce-exp-vs-cubic", 5, "Exponential vs cubic",
        "Algorithm A performs 2ⁿ operations. Algorithm B performs n³ operations.",
        [{"id": "n10", "kind": "choice", "label": "For n = 9, which performs fewer operations?",
          "options": ["A (2ⁿ)", "B (n³)"], "answer": "A (2ⁿ)"},
         {"id": "cross", "kind": "number",
          "label": "What is the smallest n ≥ 2 such that 2ⁿ > n³ for that n and every larger n?", "answer": 10},
         {"id": "n30", "kind": "choice", "label": "For n = 30, roughly how do they compare?",
          "options": ["About equal", "A is ~40× slower", "A is ~40,000× slower", "B is slower"],
          "answer": "A is ~40,000× slower"}],
        ["Compute 2⁹ and 9³.",
         "Try n = 9, 10, 11 and keep going.",
         "2³⁰ ≈ 1.07 billion; 30³ = 27,000."],
        ["n = 9: 2⁹ = 512 < 729 = 9³ → A is faster.",
         "n = 10: 2¹⁰ = 1024 > 1000 = 10³, and 2ⁿ stays ahead forever after (the ratio 2ⁿ/n³ keeps growing).",
         "n = 30: 1,073,741,824 / 27,000 ≈ 39,768 → A is about 40,000× slower.",
         "Exponential growth always overtakes polynomial growth eventually."],
        algos=[{"label": "A", "formula": "2ⁿ", "cls": "2ⁿ", "coef": 1},
               {"label": "B", "formula": "n³", "cls": "n³", "coef": 1}]),

    compare_ex("ce-doubling-time", 3, "What happens when the input doubles?",
        "An algorithm takes 3 seconds on an input of size n = 1,000. Estimate the time for n = 2,000.",
        [{"id": "lin", "kind": "number", "label": "If the algorithm is Θ(n): seconds for n = 2,000?", "answer": 6},
         {"id": "quad", "kind": "number", "label": "If it is Θ(n²): seconds for n = 2,000?", "answer": 12},
         {"id": "cub", "kind": "number", "label": "If it is Θ(n³): seconds for n = 2,000?", "answer": 24},
         {"id": "log", "kind": "choice", "label": "If it is Θ(log n), the time for n = 2,000 is...",
          "options": ["about 3.3 seconds", "6 seconds", "1.5 seconds", "9 seconds"], "answer": "about 3.3 seconds"}],
        ["Doubling n multiplies n by 2, n² by 4, n³ by 8.",
         "For log n: log(2000)/log(1000) = (log 1000 + 1)/log 1000 with base 2.",
         "log₂ 1000 ≈ 9.97, log₂ 2000 ≈ 10.97."],
        ["Θ(n): time × 2 = 6 s.",
         "Θ(n²): time × 4 = 12 s.",
         "Θ(n³): time × 8 = 24 s.",
         "Θ(log n): time × (10.97 / 9.97) ≈ × 1.1 → about 3.3 s.",
         "This 'doubling experiment' is a practical way to estimate growth rates from timings."]),

    compare_ex("ce-search-million", 3, "Linear vs binary search on a million items",
        "You search a sorted array of n = 1,048,576 (= 2²⁰) elements.",
        [{"id": "lin", "kind": "number", "label": "Worst-case comparisons for linear search?", "answer": 1048576},
         {"id": "bin", "kind": "number", "label": "Worst-case iterations for binary search (≈ log₂ n)?", "answer": 20},
         {"id": "why", "kind": "choice", "label": "What makes binary search possible here?",
          "options": ["The array is sorted", "The array is large", "n is a power of 2"], "answer": "The array is sorted"}],
        ["Linear search may look at every element.",
         "Binary search halves the range: 2²⁰ → 2¹⁹ → ... → 1.",
         "Binary search can discard half because of an ordering property."],
        ["Linear search worst case: n = 1,048,576 comparisons.",
         "Binary search worst case: ≈ log₂(2²⁰) = 20 halvings (21 with the final empty-range check).",
         "Sortedness lets one comparison rule out half of the remaining elements."],
        algos=[{"label": "Linear", "formula": "n", "cls": "n", "coef": 1},
               {"label": "Binary", "formula": "log₂ n", "cls": "log n", "coef": 1}]),

    compare_ex("ce-order-growth", 2, "Rank the growth rates",
        "Order these functions from SLOWEST-growing to FASTEST-growing (for large n).",
        [{"id": "order", "kind": "order", "label": "Drag or use the arrows to order them",
          "options": [N2, LOG, FACT, N, EXP, ONE, NLOG, SQRT, N3],
          "answer": [ONE, LOG, SQRT, N, NLOG, N2, N3, EXP, FACT]}],
        ["Constants and logarithms are the slowest.",
         "Polynomials: n^0.5 < n < n log n < n² < n³.",
         "Exponential beats every polynomial; factorial beats exponential."],
        ["1 < log n < √n < n < n log n < n² < n³ < 2ⁿ < n!",
         "Try the growth-rate visualizer to see these curves separate as n increases."]),

    compare_ex("ce-factorial", 4, "How big is n!?",
        "A brute-force algorithm tries every ordering of n cities (n! orderings). Another tries every subset (2ⁿ subsets).",
        [{"id": "fact", "kind": "number", "label": "How many orderings for n = 10?", "answer": 3628800},
         {"id": "exp", "kind": "number", "label": "How many subsets for n = 10?", "answer": 1024},
         {"id": "which", "kind": "choice", "label": "At 10⁹ operations per second, which is closest to the time for n = 20 orderings (20! ≈ 2.4 × 10¹⁸)?",
          "options": ["About 2 seconds", "About 40 minutes", "About 77 years", "About 1 day"], "answer": "About 77 years"}],
        ["10! = 10 × 9 × 8 × ... × 1.",
         "2¹⁰ = 1024.",
         "2.4 × 10¹⁸ / 10⁹ = 2.4 × 10⁹ seconds. A year is ≈ 3.15 × 10⁷ seconds."],
        ["10! = 3,628,800.", "2¹⁰ = 1,024.",
         "20! / 10⁹ ≈ 2.4 × 10⁹ s ≈ 77 years.",
         "Factorial algorithms become hopeless at modest n."]),

    compare_ex("ce-same-class", 4, "Same class, different constants",
        "Algorithm A performs 2n² + 10 operations; algorithm B performs n²/2 + 100n operations.",
        [{"id": "class", "kind": "choice", "label": "Asymptotically, how do they compare?",
          "options": ["Both are Θ(n²)", "A is Θ(n²), B is Θ(n)", "B grows faster"], "answer": "Both are Θ(n²)"},
         {"id": "ratio", "kind": "number", "label": "As n grows large, A / B approaches what number?", "answer": 4},
         {"id": "n100", "kind": "choice", "label": "For n = 100, which does fewer operations?",
          "options": ["A", "B", "Equal"], "answer": "B"}],
        ["Find each dominant term.",
         "Divide the dominant terms: 2n² / (n²/2).",
         "n = 100: A = 20,010; B = 5,000 + 10,000."],
        ["Dominant terms: 2n² and ½n² → both Θ(n²).",
         "A/B → 2 / ½ = 4. Same growth class, but B is about 4× faster for large n.",
         "n = 100: A = 20,010, B = 15,000 → B.",
         "Θ tells you the shape of growth; constants still matter when choosing between algorithms of the same class."]),
]
