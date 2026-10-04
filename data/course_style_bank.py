"""Exercises written in the course's pseudocode convention (Rosen-style slides).

    procedure name(x: integer, a1, a2, ..., an: integers)    - a1..an is one 1-indexed sequence, n is its length
    max := a_1                                                - ":=" assignment, subscripts a_i / a_{j+1}
    for i := 2 to n  /  for i in 2 to sqrt(n)                 - inclusive bounds
    if max < a_i then max := a_i                              - one-line if ... then / else
    {comments in braces}

Every exercise here carries the "course_style" tag so it can be filtered on the track pages.
"""
from data.builders import ident, cases_ex
from data.builders_pc import fill, order, complete, write, to_complexity, rubric, T
from data.trace_debug_bank import trace, debug
from engine.growth import ONE, LOG, N, NLOG, N2, N3, EXP

SQRT_OPTIONS = [ONE, LOG, "√n", N, NLOG, N2]
SEQ = "a1, a2, …, an is passed as a list; inside the procedure a_i is its i-th element (1-indexed) and n is its length."


def sub(base, idx):
    """Accepted spellings of a subscript in a fill-in blank: a_i, ai, a[i], a_{i}."""
    return [f"{base}_{idx}", f"{base}{idx}", f"{base}[{idx}]", f"{base}_{{{idx}}}"]


# ------------------------------------------------------------------------- reference solutions
SOL_MAX = """
procedure max(a1, a2, …, an: integers)
max := a_1
for i := 2 to n {each time i ≤ n is done to exit the loop}
    if max < a_i then max := a_i
return max
"""

SOL_LINEAR = """
procedure linear search(x: integer, a1, a2, …, an: distinct integers)
i := 1
while (i ≤ n and x ≠ a_i)
    i := i + 1
if i ≤ n then location := i
else location := 0
return location
"""

SOL_BINARY = """
procedure binary search(x: integer, a1, a2, …, an: increasing integers)
i := 1 {i is the left endpoint of the search interval}
j := n {j is the right endpoint of the search interval}
while i < j
    m := ⌊(i + j)/2⌋
    if x > a_m then i := m + 1
    else j := m
if x = a_i then location := i
else location := 0
return location
"""

SOL_PRIME = """
procedure isPrime(n)
    if n <= 1
        return false
    else if n <= 3
        return true
    else
        for i in 2 to sqrt(n)
            if n % i == 0
                return false
return true
"""

SOL_SELECTION = """
procedure SelectionSort(array A, length(A) = n)
    for i in 0 to n - 2
        maxIndex = i
        for j in (i + 1) to (n - 1)
            if A[j] > A[maxIndex]
                maxIndex = j
        swap(A[i], A[maxIndex])
"""

SOL_BUBBLE = """
procedure bubble sort(a1, …, an: real numbers with n ≥ 2)
for i := 1 to n − 1
    for j := 1 to n − i
        if a_j > a_{j+1} then interchange a_j and a_{j+1}
{a1, …, an is in increasing order}
"""

SOL_INSERTION = """
procedure insertion sort(a1, a2, …, an: real numbers with n ≥ 2)
for j := 2 to n
    i := 1
    while a_j > a_i
        i := i + 1
    m := a_j
    for k := 0 to j − i − 1
        a_{j−k} := a_{j−k−1}
    a_i := m
{a1, …, an is in increasing order}
"""

SOL_GCD = """
procedure gcd(a, b: positive integers)
x := a
y := b
while y ≠ 0
    r := x mod y
    x := y
    y := r
return x {gcd(a, b) is x}
"""

SOL_COUNT_EVEN = """
procedure count evens(a1, a2, …, an: integers)
count := 0
for i := 1 to n
    if a_i mod 2 = 0 then count := count + 1
return count
"""

SOL_MIN = """
procedure min(a1, a2, …, an: integers)
min := a_1
for i := 2 to n
    if a_i < min then min := a_i
return min
"""

SEARCH_TESTS = [T(7, [4, 7, 1], expect=2), T(9, [4, 7, 1], expect=0), T(4, [4], expect=1), T(1, [4, 7, 1], expect=3)]
SORTED_TESTS = [T(19, [1, 2, 3, 5, 6, 7, 8, 10, 12, 13, 15, 16, 18, 19, 20, 22], expect=14),
                T(1, [1, 3, 5, 7, 9], expect=1), T(9, [1, 3, 5, 7, 9], expect=5), T(4, [1, 3, 5, 7, 9], expect=0),
                T(5, [5], expect=1), T(6, [5], expect=0), T(8, [2, 4, 6, 8], expect=4)]
SORT_UP = [T([3, 2, 4, 1, 5], expect=[1, 2, 3, 4, 5], check="either"), T([2, 1], expect=[1, 2], check="either"),
           T([5, 5, -1, 0], expect=[-1, 0, 5, 5], check="either"), T([1, 2, 3], expect=[1, 2, 3], check="either")]
MAX_TESTS = [T([3, 8, 2, 9, 4], expect=9), T([5], expect=5), T([-4, -9, -1], expect=-1), T([7, 7, 2], expect=7)]
PRIME_TESTS = [T(0, expect=False), T(1, expect=False), T(2, expect=True), T(3, expect=True), T(4, expect=False),
               T(9, expect=False), T(13, expect=True), T(25, expect=False), T(97, expect=True)]

EXERCISES = [
    # =================================================================== A. Fill in the blank
    fill("cs-f-max", "pc_arrays", 1, "Course style: max of a1, …, an",
         "Fill in the blanks of the slides' max procedure. " + SEQ,
         """
         procedure max(a1, a2, …, an: integers)
         max := [[0]]
         for i := [[1]] to n {each time i ≤ n is done to exit the loop}
             if max < a_i then max := [[2]]
         return max
         """,
         [sub("a", 1), ["2"], sub("a", "i")],
         SOL_MAX, "max", ["a"], MAX_TESTS,
         ["The sequence starts at a_1, not a_0.", "a_1 is already the best so far, so the loop can skip it.",
          "When a_i beats the current max, remember a_i."],
         ["Blank 1: max := a_1 - the first element is the best so far.",
          "Blank 2: start at i := 2, because a_1 is already accounted for.",
          "Blank 3: max := a_i whenever max < a_i.",
          "The loop body runs n − 1 times, so the procedure is Θ(n)."]),

    fill("cs-f-sum", "pc_loops", 1, "Course style: sum of a1, …, an",
         "Complete the accumulator. " + SEQ,
         """
         procedure sum(a1, a2, …, an: integers)
         total := [[0]]
         for i := 1 to [[1]]
             total := [[2]]
         return total
         """,
         [["0"], ["n"], ["total+a_i", "total+ai", "total+a[i]", "a_i+total", "ai+total", "a[i]+total"]],
         """
         procedure sum(a1, a2, …, an: integers)
         total := 0
         for i := 1 to n
             total := total + a_i
         return total
         """, "sum", ["a"],
         [T([1, 2, 3], expect=6), T([5], expect=5), T([-5, 5, 10], expect=10)],
         ["What is the sum of no elements?", "With 1-indexing, the last index is n itself.", "Add a_i to the running total."],
         ["total := 0 before the loop.", "for i := 1 to n visits a_1 through a_n (no − 1 with 1-indexing).",
          "total := total + a_i."]),

    fill("cs-f-linear", "pc_searching", 2, "Course style: linear search",
         "Fill in the blanks of the slides' linear search. It returns the position of x, or 0 if x is not in the list. " + SEQ,
         """
         procedure linear search(x: integer, a1, a2, …, an: distinct integers)
         i := 1
         while (i ≤ n and x [[0]] a_i)
             i := [[1]]
         if i ≤ n then location := [[2]]
         else location := [[3]]
         return location
         """,
         [["≠", "!=", "<>"], ["i+1", "1+i"], ["i"], ["0"]],
         SOL_LINEAR, "LinearSearch", ["x", "a"], SEARCH_TESTS,
         ["Keep walking while x has NOT been found yet.", "Move to the next position.",
          "If the loop stopped early (i ≤ n), x is at position i.", "The convention for 'not found' here is 0, not −1."],
         ["Blank 1: ≠ - keep going while x ≠ a_i.", "Blank 2: i := i + 1.", "Blank 3: location := i.",
          "Blank 4: location := 0 - positions start at 1, so 0 can mean 'not found'.",
          "Order matters in 'i ≤ n and x ≠ a_i': the bound check comes first so a_{n+1} is never read."]),

    fill("cs-f-prime", "pc_numbers", 3, "Course style: isPrime",
         "Fill in the blanks of the isPrime procedure from the slides.",
         """
         procedure isPrime(n)
             if n <= [[0]]
                 return false
             else if n <= 3
                 return true
             else
                 for i in 2 to [[1]]
                     if n % i == [[2]]
                         return false
         return true
         """,
         [["1"], ["sqrt(n)", "floor(sqrt(n))", "⌊sqrt(n)⌋"], ["0"]],
         SOL_PRIME, "isPrime", ["n"], PRIME_TESTS,
         ["0 and 1 are not prime.", "If n has a divisor other than 1 and n, one of them is at most √n.",
          "i divides n exactly when the remainder n % i is 0."],
         ["Blank 1: n <= 1 → false.", "Blank 2: trying i up to sqrt(n) is enough.",
          "Blank 3: n % i == 0 means i divides n, so n is not prime.",
          "The loop runs at most √n − 1 times: O(√n)."]),

    fill("cs-f-selection", "pc_sorting", 4, "Course style: SelectionSort (largest first)",
         "Fill in the blanks of the slides' SelectionSort. Each pass finds the largest remaining element and swaps it "
         "to position i, so the array ends up in decreasing order. This one uses 0-indexed A[0..n − 1].",
         """
         procedure SelectionSort(array A, length(A) = n)
             for i in 0 to n - 2
                 maxIndex = [[0]]
                 for j in [[1]] to (n - 1)
                     if A[j] > A[maxIndex]
                         maxIndex = [[2]]
                 swap(A[i], A[maxIndex])
         """,
         [["i"], ["i+1", "(i+1)"], ["j"]],
         SOL_SELECTION, "SelectionSort", ["A"],
         [T([3, 1, 2], expect=[3, 2, 1], check="either"), T([1, 2, 3, 4], expect=[4, 3, 2, 1], check="either"),
          T([5], expect=[5], check="either"), T([2, 9, 2, 7], expect=[9, 7, 2, 2], check="either")],
         ["Before scanning, the best candidate is the element at position i itself.",
          "Position i is already the candidate, so the scan starts just after it.",
          "When a bigger element shows up, remember its index."],
         ["maxIndex = i", "for j in (i + 1) to (n − 1)", "maxIndex = j",
          "length(A) = n in the header just names the length; only A is passed.",
          "(n − 1) + (n − 2) + … + 1 = n(n − 1)/2 comparisons → Θ(n²)."]),

    fill("cs-f-binary", "pc_searching", 4, "Course style: binary search",
         "Fill in the blanks of the slides' binary search on an increasing sequence. It returns the position of x, or 0. " + SEQ,
         """
         procedure binary search(x: integer, a1, a2, …, an: increasing integers)
         i := 1 {i is the left endpoint of the search interval}
         j := [[0]] {j is the right endpoint of the search interval}
         while i < j
             m := [[1]]
             if x > a_m then i := [[2]]
             else j := [[3]]
         if x = a_i then location := i
         else location := 0
         return location
         """,
         [["n"], ["⌊(i+j)/2⌋", "floor((i+j)/2)", "(i+j)div2", "⌊(i+j)/2⌋"], ["m+1", "1+m"], ["m"]],
         SOL_BINARY, "BinarySearch", ["x", "a"], SORTED_TESTS,
         ["The search interval starts as the whole list a_1..a_n.", "m is the midpoint, rounded down.",
          "If x > a_m, x can only be to the right of m.", "Otherwise x is at m or to its left - keep m in the interval."],
         ["j := n", "m := ⌊(i + j)/2⌋", "x > a_m → i := m + 1 (a_m is too small)",
          "else j := m (a_m might be x itself, so it stays)",
          "The loop stops when i = j; one final comparison decides the answer. The interval halves each time: Θ(log n)."]),

    # =================================================================== B. Put the steps in order
    order("cs-o-max", "pc_arrays", 1, "Course style: order the max procedure",
          "Put the lines of the slides' max procedure in order. " + SEQ,
          """
          procedure max(a1, a2, …, an: integers)
          max := a_1
          for i := 2 to n
              if max < a_i then max := a_i
          return max
          """, "max", ["a"], MAX_TESTS,
          ["The header comes first.", "max needs a value before the loop compares against it.", "return goes last, after the loop."],
          ["Header → initialize max := a_1 → loop over i = 2..n → update inside the loop → return max."]),

    order("cs-o-linear", "pc_searching", 2, "Course style: order linear search",
          "Put the lines of the slides' linear search in order. " + SEQ,
          SOL_LINEAR, "LinearSearch", ["x", "a"], SEARCH_TESTS,
          ["i starts at 1 before the while loop tests it.", "Only the increment belongs inside the loop.",
           "The if / else that sets location comes after the loop, then return."],
          ["i := 1 → while (i ≤ n and x ≠ a_i) → i := i + 1 → if i ≤ n then location := i → else location := 0 → return location."]),

    order("cs-o-count", "pc_counting", 2, "Course style: order count evens",
          "Put the lines in order so the procedure returns how many of a1, …, an are even. " + SEQ,
          SOL_COUNT_EVEN, "CountEvens", ["a"],
          [T([4, 7, 10, 3, 8], expect=3), T([1, 3], expect=0), T([2], expect=1)],
          ["Initialize the counter first.", "The test goes inside the loop.", "Return after the loop."],
          ["count := 0 → for i := 1 to n → if a_i mod 2 = 0 then count := count + 1 → return count."]),

    # =================================================================== C. Complete the algorithm
    complete("cs-c-min", "pc_arrays", 2, "Course style: complete min",
             "Write the missing loop so min ends up as the smallest of a1, …, an. Use the course convention "
             "(:=, a_i, if … then …). " + SEQ,
             """
             procedure min(a1, a2, …, an: integers)
             min := a_1
             // Complete this section
             return min
             """, SOL_MIN, "min", ["a"],
             [T([3, 8, 2, 9, 4], expect=2), T([5], expect=5), T([-4, -9, -1], expect=-9), T([1, 1, 1], expect=1)],
             rubric("loop", "if"),
             ["Mirror the max procedure.", "Loop i from 2 to n.", "if a_i < min then min := a_i"],
             ["for i := 2 to n", "    if a_i < min then min := a_i", "n − 1 comparisons: Θ(n)."]),

    complete("cs-c-gcd", "pc_numbers", 3, "Course style: complete Euclid's gcd",
             "Complete the loop of the Euclidean algorithm: repeatedly replace (x, y) by (y, x mod y) until y = 0.",
             """
             procedure gcd(a, b: positive integers)
             x := a
             y := b
             // Complete this section
             return x {gcd(a, b) is x}
             """, SOL_GCD, "gcd", ["a", "b"],
             [T(414, 662, expect=2), T(12, 18, expect=6), T(17, 5, expect=1), T(9, 9, expect=9), T(100, 10, expect=10)],
             rubric("loop", extra=[("Remainder", [r"\bmod\b|%"], "Use x mod y.")]),
             ["Loop while y ≠ 0.", "Save the remainder r := x mod y before overwriting anything.", "Then x := y and y := r."],
             ["while y ≠ 0", "    r := x mod y", "    x := y", "    y := r",
              "The remainder at least halves every two steps, so the loop runs O(log b) times."]),

    complete("cs-c-insertion", "pc_sorting", 4, "Course style: complete insertion sort",
             "The slides' insertion sort has found the position i where a_j belongs. Complete the step that shifts "
             "a_i, …, a_{j−1} one place to the right and puts a_j at position i. " + SEQ,
             """
             procedure insertion sort(a1, a2, …, an: real numbers with n ≥ 2)
             for j := 2 to n
                 i := 1
                 while a_j > a_i
                     i := i + 1
                 // Complete this section
             {a1, …, an is in increasing order}
             """, SOL_INSERTION, "InsertionSort", ["a"], SORT_UP,
             rubric("loop", extra=[("Save a_j", [r"\bm\s*=\s*a"], "Save a_j in a temporary (m := a_j) before shifting overwrites it.")]),
             ["Save a_j first (m := a_j) - shifting will overwrite it.",
              "Shift from the right end: a_{j−k} := a_{j−k−1} for k = 0 .. j − i − 1.",
              "Finally a_i := m."],
             ["m := a_j", "for k := 0 to j − i − 1", "    a_{j−k} := a_{j−k−1}", "a_i := m",
              "Shifting must go right-to-left so no value is overwritten before it is copied."]),

    # =================================================================== D. Write from a description
    write("cs-w-count-x", "pc_counting", 2, "Course style: count occurrences of x",
          "Write a procedure in the course convention that returns how many terms of a1, …, an equal x. " + SEQ,
          "procedure count(x: integer, a1, a2, …, an: integers)\n",
          """
          procedure count(x: integer, a1, a2, …, an: integers)
          c := 0
          for i := 1 to n
              if a_i = x then c := c + 1
          return c
          """, "count", ["x", "a"],
          [T(2, [2, 5, 2, 2], expect=3), T(9, [1, 2], expect=0), T(4, [4], expect=1)],
          rubric("loop", "if", "return"),
          ["Start a counter at 0.", "Look at every a_i for i := 1 to n.", "if a_i = x then add one."],
          ["c := 0; for i := 1 to n: if a_i = x then c := c + 1; return c.", "Θ(n): every term is checked once."]),

    write("cs-w-last", "pc_searching", 3, "Course style: last occurrence",
          "Write a procedure that returns the position of the LAST term of a1, …, an equal to x, or 0 if there is none. " + SEQ,
          "procedure last occurrence(x: integer, a1, a2, …, an: integers)\n",
          """
          procedure last occurrence(x: integer, a1, a2, …, an: integers)
          location := 0
          for i := 1 to n
              if a_i = x then location := i
          return location
          """, "LastOccurrence", ["x", "a"],
          [T(2, [2, 5, 2, 7], expect=3), T(9, [1, 2], expect=0), T(4, [4], expect=1), T(7, [7, 7, 7], expect=3)],
          rubric("loop", "if", "return"),
          ["Start with location := 0 (meaning 'not found').", "Every time a_i = x, overwrite location with i.",
           "Alternatively, loop from n down to 1 and stop at the first match."],
          ["Scanning left to right and overwriting leaves the last match in location.",
           "Or: for i := n downto 1 … return the first i with a_i = x."]),

    write("cs-w-sorted", "pc_arrays", 2, "Course style: is the list increasing?",
          "Write a procedure that returns true if a1 ≤ a2 ≤ … ≤ an and false otherwise. " + SEQ,
          "procedure is sorted(a1, a2, …, an: integers)\n",
          """
          procedure is sorted(a1, a2, …, an: integers)
          for i := 1 to n − 1
              if a_i > a_{i+1} then return false
          return true
          """, "IsSorted", ["a"],
          [T([1, 2, 2, 5], expect=True), T([3, 1], expect=False), T([4], expect=True), T([1, 3, 2, 4], expect=False)],
          rubric("loop", "if", "return"),
          ["Compare each neighbouring pair a_i and a_{i+1}.", "The last pair is a_{n−1}, a_n, so i stops at n − 1.",
           "One bad pair is enough to return false."],
          ["for i := 1 to n − 1: if a_i > a_{i+1} then return false.", "If no pair is out of order, return true. Θ(n) worst case."]),

    write("cs-w-factorial", "pc_recursion", 3, "Course style: recursive factorial",
          "Write the recursive procedure factorial(n) from the slides: n! = n · (n − 1)!, with 0! = 1.",
          "procedure factorial(n: nonnegative integer)\n",
          """
          procedure factorial(n: nonnegative integer)
          if n = 0 then return 1
          else return n · factorial(n − 1)
          {output is n!}
          """, "factorial", ["n"],
          [T(0, expect=1), T(1, expect=1), T(5, expect=120), T(7, expect=5040)],
          rubric("rec_call", "base"),
          ["Base case: n = 0.", "Otherwise the answer is n times factorial(n − 1).", "if n = 0 then return 1 / else return n · factorial(n − 1)"],
          ["if n = 0 then return 1", "else return n · factorial(n − 1)", "n recursive calls: Θ(n)."]),

    write("cs-w-power", "pc_recursion", 4, "Course style: recursive power",
          "Write a recursive procedure power(a, n) that computes aⁿ using aⁿ = a · aⁿ⁻¹ and a⁰ = 1.",
          "procedure power(a: nonzero real number, n: nonnegative integer)\n",
          """
          procedure power(a: nonzero real number, n: nonnegative integer)
          if n = 0 then return 1
          else return a · power(a, n − 1)
          {output is a^n}
          """, "power", ["a", "n"],
          [T(2, 0, expect=1), T(2, 10, expect=1024), T(3, 4, expect=81), T(-2, 3, expect=-8)],
          rubric("rec_call", "base"),
          ["Base case n = 0 returns 1.", "Recursive case: a · power(a, n − 1).", "Make sure n gets smaller in the call."],
          ["if n = 0 then return 1", "else return a · power(a, n − 1)", "n calls → Θ(n) multiplications."]),
]

TRACES = [
    trace("cs-t-max", "pc_arrays", 1, "Course style: trace max", SOL_MAX,
          {"a": [3, 8, 2, 9, 4]}, ["i", "max"], ("loop", "for i := 2 to n"),
          ["max starts at a_1 = 3.", "It changes only when a_i is bigger.", "a_3 = 2 and a_5 = 4 don't change it."],
          ["Start: max = 3", "i = 2: 3 < 8 → max = 8", "i = 3: 8 < 2? no", "i = 4: 8 < 9 → max = 9", "i = 5: 9 < 4? no → return 9"],
          prompt="Trace max with a1, …, a5 = 3, 8, 2, 9, 4. Fill in i and max at the END of each iteration of the for loop."),

    trace("cs-t-linear", "pc_searching", 1, "Course style: trace linear search", SOL_LINEAR,
          {"x": 6, "a": [4, 2, 6, 9]}, ["i"], ("loop", "while (i ≤ n"),
          ["i starts at 1 and a_1 = 4 ≠ 6.", "Each iteration only increments i.", "The loop stops as soon as a_i = 6."],
          ["a_1 = 4 ≠ 6 → i = 2", "a_2 = 2 ≠ 6 → i = 3", "a_3 = 6: the condition fails, loop ends → location = 3"],
          prompt="Trace linear search for x = 6 in 4, 2, 6, 9. Fill in i at the END of each iteration of the while loop."),

    trace("cs-t-binary", "pc_searching", 3, "Course style: trace binary search", SOL_BINARY,
          {"x": 19, "a": [1, 2, 3, 5, 6, 7, 8, 10, 12, 13, 15, 16, 18, 19, 20, 22]}, ["i", "j", "m"], ("loop", "while i < j"),
          ["Start: i = 1, j = 16.", "m = ⌊(i + j)/2⌋; compare x with a_m.", "x > a_m moves i to m + 1; otherwise j becomes m."],
          ["i=1, j=16: m=8, a_8=10 < 19 → i=9", "i=9, j=16: m=12, a_12=16 < 19 → i=13",
           "i=13, j=16: m=14, a_14=19, not < 19 → j=14", "i=13, j=14: m=13, a_13=18 < 19 → i=14",
           "i = j = 14 and a_14 = 19 → location = 14 (the example from the slides)"],
          prompt="Trace binary search for x = 19 in 1, 2, 3, 5, 6, 7, 8, 10, 12, 13, 15, 16, 18, 19, 20, 22. "
                 "Fill in i, j and m at the END of each iteration of the while loop."),

    trace("cs-t-bubble", "pc_sorting", 3, "Course style: trace bubble sort", SOL_BUBBLE,
          {"a": [3, 2, 4, 1, 5]}, ["i", "j", "a"], ("after", "interchange"),
          ["Only adjacent pairs that are out of order are interchanged.", "Pass i = 1 compares j = 1..4.",
           "After pass 1 the largest value, 5, is at the end."],
          ["Pass 1: (3,2) swap → 2 3 4 1 5; (4,1) swap → 2 3 1 4 5", "Pass 2: (3,1) swap → 2 1 3 4 5",
           "Pass 3: (2,1) swap → 1 2 3 4 5", "Pass 4: no swaps."],
          prompt="Trace bubble sort on 3, 2, 4, 1, 5. Add a row each time an interchange happens: i, j, and the list right after the swap."),

    trace("cs-t-gcd", "pc_numbers", 2, "Course style: trace gcd(414, 662)", SOL_GCD,
          {"a": 414, "b": 662}, ["r", "x", "y"], ("loop", "while y ≠ 0"),
          ["r := x mod y first, then shift: x := y, y := r.", "414 mod 662 = 414, so the first pass just swaps.",
           "Stop when y becomes 0; the answer is x."],
          ["r=414, x=662, y=414", "r=248, x=414, y=248", "r=166, x=248, y=166", "r=82, x=166, y=82", "r=2, x=82, y=2",
           "r=0, x=2, y=0 → gcd = 2"],
          prompt="Trace gcd(414, 662). Fill in r, x and y at the END of each iteration of the while loop."),
]

DEBUGS = [
    debug("cs-d-max", "pc_arrays", 1, "Course style: max returns the minimum", """
        procedure max(a1, a2, …, an: integers)
        max := a_1
        for i := 2 to n
            if max > a_i then max := a_i
        return max
        """, SOL_MAX, ["if max > a_i"], "max", ["a"], MAX_TESTS,
        ["Try it on 3, 8, 2: what does it return?", "When should max be replaced?", "The comparison is backwards."],
        ["The bug: 'max > a_i' replaces max with smaller values, so it computes the minimum.",
         "Fix: if max < a_i then max := a_i."]),

    debug("cs-d-linear", "pc_searching", 2, "Course style: linear search runs off the end", """
        procedure linear search(x: integer, a1, a2, …, an: distinct integers)
        i := 1
        while (i ≤ n or x ≠ a_i)
            i := i + 1
        if i ≤ n then location := i
        else location := 0
        return location
        """, SOL_LINEAR, ["while (i ≤ n or"], "LinearSearch", ["x", "a"], SEARCH_TESTS,
        ["What happens when x is not in the list?", "When i = n + 1, is the loop condition false?",
         "Both conditions must hold to keep going."],
        ["With 'or', the loop keeps going while x ≠ a_i even after i passes n, reading a_{n+1}.",
         "Fix: while (i ≤ n and x ≠ a_i)."]),

    debug("cs-d-prime", "pc_numbers", 2, "Course style: isPrime says no number is prime", """
        procedure isPrime(n)
            if n <= 1
                return false
            else if n <= 3
                return true
            else
                for i in 2 to n
                    if n % i == 0
                        return false
        return true
        """, SOL_PRIME, ["for i in 2 to n"], "isPrime", ["n"], PRIME_TESTS,
        ["Try n = 5. Which values does i take?", "What is n % n?", "The loop must stop before reaching n itself."],
        ["i eventually equals n, and n % n == 0, so every n > 3 is reported as not prime.",
         "Fix: for i in 2 to sqrt(n) (or n − 1, which is correct but Θ(n) instead of Θ(√n))."]),

    debug("cs-d-binary", "pc_searching", 4, "Course style: binary search misses elements", """
        procedure binary search(x: integer, a1, a2, …, an: increasing integers)
        i := 1
        j := n
        while i < j
            m := ⌊(i + j)/2⌋
            if x > a_m then i := m + 1
            else j := m − 1
        if x = a_i then location := i
        else location := 0
        return location
        """, SOL_BINARY, ["else j := m − 1"], "BinarySearch", ["x", "a"], SORTED_TESTS,
        ["Search for 9 in 1, 3, 5, 7, 9. Then for 3.", "In the else branch, x ≤ a_m - could x BE a_m?",
         "Discarding m can throw away the answer."],
        ["When x ≤ a_m, x may equal a_m, so m must stay in the interval: j := m.",
         "(This version tests x = a_i only once at the end, unlike the version that checks a_m = x inside the loop.)"]),
]

COMPLEXITY = [
    ident("cs-i-max", 1, "fundamentals", "Course style: complexity of max", SOL_MAX, N,
          ["How many times does the for loop body run?", "i goes from 2 to n.", "Each iteration does one comparison."],
          ["The loop runs n − 1 times, each doing one comparison (and maybe an assignment).",
           "T(n) = c(n − 1) + c' ∈ Θ(n), so the tightest upper bound is O(n)."],
          [("for i := 2 to n", "n − 1 iterations"), ("if max < a_i", "1 comparison each")]),

    ident("cs-i-bubble", 2, "nested_loops", "Course style: complexity of bubble sort", SOL_BUBBLE, N2,
          ["The inner loop's length depends on i.", "Pass i makes n − i comparisons.", "Add up (n − 1) + (n − 2) + … + 1."],
          ["Comparisons: Σ_{i=1}^{n−1} (n − i) = n(n − 1)/2.", "That is Θ(n²), so O(n²) is the tightest upper bound."],
          [("for i := 1 to n − 1", "n − 1 passes"), ("for j := 1 to n − i", "n − i comparisons in pass i")]),

    ident("cs-i-binary", 4, "logarithmic", "Course style: complexity of binary search", SOL_BINARY, LOG,
          ["How does the interval i..j change each iteration?", "It is cut roughly in half.",
           "How many halvings until one element is left?"],
          ["Each iteration halves the interval size j − i + 1.", "After about log₂ n iterations i = j.",
           "Plus one final comparison: Θ(log n)."],
          [("while i < j", "≈ log₂ n iterations"), ("m := ⌊(i + j)/2⌋", "halves the interval")]),

    ident("cs-i-prime", 5, "irregular_loops", "Course style: complexity of isPrime", SOL_PRIME, "√n",
          ["In the worst case (n prime) the loop never returns early.", "i runs from 2 to √n.",
           "So how many iterations is that, as a function of n?"],
          ["Worst case: n is prime, so all values i = 2, …, ⌊√n⌋ are tried.",
           "That is about √n iterations of constant work: O(√n)."],
          [("for i in 2 to sqrt(n)", "≈ √n iterations")], options=SQRT_OPTIONS),

    ident("cs-i-selection", 3, "nested_loops", "Course style: complexity of SelectionSort", SOL_SELECTION, N2,
          ["Count the comparisons A[j] > A[maxIndex].", "Pass i compares n − 1 − i elements.",
           "The sum of 1 through n − 1 is…"],
          ["(n − 1) + (n − 2) + … + 1 = n(n − 1)/2 comparisons, for every input.", "Θ(n²) → O(n²)."],
          [("for i in 0 to n - 2", "n − 1 passes"), ("for j in (i + 1) to (n - 1)", "n − 1 − i comparisons")], wrap="Θ"),

    cases_ex("cs-k-linear", 2, "Course style: linear search cases", SOL_LINEAR, ONE, N, N,
             ["Best case: where is x?", "Worst case: x is last, or not there at all.",
              "On average (x present, every position equally likely) about n/2 comparisons."],
             ["Best: x = a_1, one comparison → Θ(1).", "Worst: x absent → n + 1 bound checks → Θ(n).",
              "Average: about (n + 1)/2 comparisons → Θ(n)."],
             [("while (i ≤ n and x ≠ a_i)", "up to n + 1 checks")]),
]

EXERCISES += TRACES + DEBUGS + COMPLEXITY + [
    # =================================================================== G. Pseudocode → complexity
    to_complexity("cs-g-linear", "cs-o-linear", 2, "Course style: linear search → complexity", N, [ONE, LOG, N, NLOG, N2],
                  ["What is the worst case for linear search?", "x is not in the list.", "Every term is compared."],
                  ["Worst case: the while loop runs n times and the bound check runs n + 1 times → Θ(n)."], "pc_searching"),
    to_complexity("cs-g-binary", "cs-f-binary", 4, "Course style: binary search → complexity", LOG, [ONE, LOG, N, NLOG, N2],
                  ["How much of the list survives each iteration?", "About half.", "Halving n down to 1 takes log₂ n steps."],
                  ["The interval halves each iteration, so the loop runs ⌈log₂ n⌉ times → Θ(log n)."], "pc_searching"),
    to_complexity("cs-g-insertion", "cs-c-insertion", 4, "Course style: insertion sort → complexity", N2, [N, NLOG, N2, N3, EXP],
                  ["For each j, how far can the while loop and the shifting go?", "Up to j − 1 steps in total.",
                   "Σ_{j=2}^{n} j is quadratic."],
                  ["For each j, finding i plus shifting costs about j steps, so the total is about n²/2 → Θ(n²)."], "pc_sorting"),
    to_complexity("cs-g-prime", "cs-f-prime", 3, "Course style: isPrime → complexity", "√n", SQRT_OPTIONS,
                  ["Worst case: n is prime.", "The loop tries i = 2 … √n.", "No other loop."],
                  ["About √n iterations in the worst case → Θ(√n) (measured in the value n, not its number of digits)."], "pc_numbers"),
]

for _ex in EXERCISES:
    _ex["tags"] = list(_ex.get("tags", [])) + ["course_style"]
