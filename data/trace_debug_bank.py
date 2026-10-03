"""Tracing (Type F) and debugging (Type E) exercises."""
import textwrap

from data.builders_pc import T, _tags


def c(s):
    return textwrap.dedent(s).strip("\n")


def trace(id, topic, level, title, src, inputs, watch, snap, hints, explanation, prompt=None):
    """snap = ("loop", substring of a loop header) -> one row per iteration (values at the END of the iteration)
       snap = ("after", substring of a statement) -> one row each time that statement runs."""
    kind, where = snap
    return {
        "id": id, "track": "pseudocode", "type": "trace", "topic": topic, "level": level, "title": title,
        "prompt": prompt or ("Trace the code by hand. Fill in the value of each variable "
                             + ("at the END of each iteration of the highlighted loop." if kind == "loop"
                                else "right after the highlighted statement runs.")),
        "code": c(src), "inputs": inputs, "watch": watch, "snap": [kind, where],
        "hints": hints, "steps": explanation, "tags": _tags(topic),
    }


def debug(id, topic, level, title, buggy, solution, bug_lines, entry, params, tests, hints, explanation, prompt=None):
    return {
        "id": id, "track": "pseudocode", "type": "debug", "topic": topic, "level": level, "title": title,
        "prompt": prompt or "This pseudocode has a logical error. Click the line with the bug, then fix the code in the editor.",
        "buggy": c(buggy), "solution": c(solution), "bug_lines": bug_lines, "entry": entry, "params": params,
        "tests": tests, "hints": hints, "steps": explanation, "tags": _tags(topic),
    }


TRACES = [
    trace("pt-sum", "pc_loops", 1, "Running sum", """
        sum = 0
        for i = 0 to 3
            sum = sum + numbers[i]
        """, {"numbers": [5, 2, 8, 3]}, ["i", "sum"], ("loop", "for i = 0 to 3"),
        ["Start with sum = 0.", "Iteration i adds numbers[i].", "5, then 5 + 2, then ..."],
        ["i = 0: sum = 0 + 5 = 5", "i = 1: sum = 5 + 2 = 7", "i = 2: sum = 7 + 8 = 15", "i = 3: sum = 15 + 3 = 18"]),

    trace("pt-max", "pc_arrays", 1, "Tracking the maximum", """
        procedure FindMaximum(numbers)
            largest = numbers[0]
            for i = 1 to length(numbers) - 1
                if numbers[i] > largest
                    largest = numbers[i]
            return largest
        """, {"numbers": [3, 7, 2, 9, 4]}, ["i", "largest"], ("loop", "for i = 1"),
        ["largest starts at numbers[0] = 3.", "It only changes when a bigger value appears.", "2 and 4 don't change it."],
        ["Start: largest = 3", "i = 1: 7 > 3 → largest = 7", "i = 2: 2 > 7? no → 7",
         "i = 3: 9 > 7 → 9", "i = 4: 4 > 9? no → 9", "Return 9."]),

    trace("pt-count-even", "pc_counting", 1, "Counting evens", """
        count = 0
        for i = 0 to length(numbers) - 1
            if numbers[i] mod 2 == 0
                count = count + 1
        """, {"numbers": [4, 7, 10, 3, 8]}, ["i", "count"], ("loop", "for i = 0"),
        ["Check each value: is it divisible by 2?", "4 is even, 7 is odd, ...", "count only changes on even values."],
        ["i = 0: 4 even → 1", "i = 1: 7 odd → 1", "i = 2: 10 even → 2", "i = 3: 3 odd → 2", "i = 4: 8 even → 3"]),

    trace("pt-doubling", "pc_loops", 2, "A doubling loop", """
        i = 1
        count = 0
        while i < n
            i = i * 2
            count = count + 1
        """, {"n": 20}, ["i", "count"], ("loop", "while i < n"),
        ["i doubles each iteration.", "Check the condition i < 20 BEFORE each iteration.",
         "When i becomes 32 the loop ends."],
        ["i: 1 → 2 → 4 → 8 → 16 → 32 (then 32 < 20 fails).",
         "count ends at 5 = ⌈log₂ 20⌉ - this is why doubling loops are Θ(log n)."]),

    trace("pt-reverse", "pc_arrays", 2, "Reversing with two pointers", """
        left = 0
        right = length(A) - 1
        while left < right
            swap(A[left], A[right])
            left = left + 1
            right = right - 1
        """, {"A": [1, 2, 3, 4, 5]}, ["left", "right", "A"], ("loop", "while left < right"),
        ["The first swap exchanges A[0] and A[4].", "Both pointers move inward after each swap.",
         "The loop stops when left = right = 2."],
        ["Iteration 1: swap 1 and 5 → [5, 2, 3, 4, 1]; left = 1, right = 3",
         "Iteration 2: swap 2 and 4 → [5, 4, 3, 2, 1]; left = 2, right = 2",
         "2 < 2 is false → stop. The middle element 3 never moves."],
        prompt="Trace the code. Write arrays like 5, 2, 3, 4, 1. Give the values at the END of each iteration."),

    trace("pt-bubble", "pc_sorting", 3, "Bubble sort passes", """
        procedure BubbleSort(A)
            n = length(A)
            for i = 0 to n - 2
                for j = 0 to n - 2 - i
                    if A[j] > A[j + 1]
                        swap(A[j], A[j + 1])
            return A
        """, {"A": [5, 1, 4, 2]}, ["i", "A"], ("loop", "for i = 0 to n - 2"),
        ["In each pass, the largest remaining value bubbles to the end.",
         "Pass 0 compares (5,1), (5,4), (5,2).", "Write the array after each complete pass."],
        ["Pass 0: [1, 5, 4, 2] → [1, 4, 5, 2] → [1, 4, 2, 5]",
         "Pass 1: [1, 4, 2, 5] → [1, 2, 4, 5]",
         "Pass 2: compare (1, 2): no swap → [1, 2, 4, 5]"],
        prompt="Trace the code. Write arrays like 1, 4, 2, 5. Give the values at the END of each OUTER iteration."),

    trace("pt-insertion", "pc_sorting", 3, "Insertion sort", """
        procedure InsertionSort(A)
            for i = 1 to length(A) - 1
                key = A[i]
                j = i - 1
                while j >= 0 and A[j] > key
                    A[j + 1] = A[j]
                    j = j - 1
                A[j + 1] = key
            return A
        """, {"A": [4, 3, 1, 2]}, ["i", "key", "A"], ("loop", "for i = 1"),
        ["After iteration i, the first i + 1 elements are sorted.", "key = A[i] is inserted into the sorted prefix.",
         "Larger elements shift right to make room."],
        ["i = 1: key 3 → [3, 4, 1, 2]", "i = 2: key 1 → [1, 3, 4, 2]", "i = 3: key 2 → [1, 2, 3, 4]"],
        prompt="Trace the code. Write arrays like 3, 4, 1, 2. Give the values at the END of each outer iteration."),

    trace("pt-selection", "pc_sorting", 3, "Selection sort", """
        procedure SelectionSort(A)
            n = length(A)
            for i = 0 to n - 2
                minIndex = i
                for j = i + 1 to n - 1
                    if A[j] < A[minIndex]
                        minIndex = j
                swap(A[i], A[minIndex])
            return A
        """, {"A": [29, 10, 14, 37, 13]}, ["i", "minIndex", "A"], ("loop", "for i = 0 to n - 2"),
        ["minIndex is the index of the smallest element in A[i..n - 1] (before the swap).",
         "i = 0: the smallest is 10 at index 1.", "After the swap, A[i] holds that minimum."],
        ["i = 0: min 10 at index 1 → [10, 29, 14, 37, 13]",
         "i = 1: min 13 at index 4 → [10, 13, 14, 37, 29]",
         "i = 2: min 14 at index 2 (no change) → [10, 13, 14, 37, 29]",
         "i = 3: min 29 at index 4 → [10, 13, 14, 29, 37]"],
        prompt="Trace the code. Write arrays like 10, 29, 14. Give the values at the END of each outer iteration."),

    trace("pt-binary", "pc_searching", 4, "Binary search", """
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
        """, {"A": [2, 5, 8, 12, 16, 23, 38], "target": 23}, ["low", "high", "mid"], ("after", "mid = floor"),
        ["Start: low = 0, high = 6.", "mid = floor((0 + 6) / 2) = 3, and A[3] = 12 < 23.",
         "So low becomes 4. Compute the next mid."],
        ["Row 1: low 0, high 6, mid 3 (A[3] = 12 < 23 → low = 4)",
         "Row 2: low 4, high 6, mid 5 (A[5] = 23 → found!)",
         "Only 2 iterations for 7 elements."]),

    trace("pt-digits", "pc_numbers", 2, "Digit sum", """
        s = 0
        while n > 0
            s = s + n mod 10
            n = n div 10
        """, {"n": 4721}, ["n", "s"], ("loop", "while n > 0"),
        ["n mod 10 is the last digit.", "n div 10 removes the last digit.", "First iteration: s = 1, n = 472."],
        ["4721 → s = 1, n = 472", "472 → s = 3, n = 47", "47 → s = 10, n = 4", "4 → s = 14, n = 0"]),

    trace("pt-triangle", "pc_loops", 3, "A triangular nested loop", """
        count = 0
        for i = 1 to n
            for j = 1 to i
                count = count + 1
        """, {"n": 3}, ["i", "j", "count"], ("loop", "for j = 1 to i"),
        ["The inner loop runs i times.", "For i = 1: one row. For i = 2: two rows.",
         "Total rows: 1 + 2 + 3."],
        ["(1,1) → 1", "(2,1) → 2, (2,2) → 3", "(3,1) → 4, (3,2) → 5, (3,3) → 6",
         "6 = 3·4/2: the n(n + 1)/2 count from the complexity exercises."],
        prompt="Trace the INNER loop: give i, j and count at the end of every inner iteration."),

    trace("pt-coins", "pc_greedy", 3, "Greedy coin change", """
        procedure CoinCount(amount, coins)
            count = 0
            for i = 0 to length(coins) - 1
                while amount >= coins[i]
                    amount = amount - coins[i]
                    count = count + 1
            return count
        """, {"amount": 68, "coins": [25, 10, 5, 1]}, ["amount", "count"], ("loop", "while amount >= coins[i]"),
        ["Each row is one coin taken.", "25 fits twice into 68.", "Then 10, then 5, then 1s."],
        ["68 → 43 → 18 (two quarters)", "18 → 8 (a dime)", "8 → 3 (a nickel)", "3 → 2 → 1 → 0 (three pennies)", "7 coins."]),

    trace("pt-gcd", "pc_numbers", 3, "Euclid's algorithm", """
        procedure GCD(a, b)
            while b != 0
                t = b
                b = a mod b
                a = t
            return a
        """, {"a": 48, "b": 18}, ["a", "b"], ("loop", "while b != 0"),
        ["Each step replaces (a, b) with (b, a mod b).", "48 mod 18 = 12.", "Stop when b becomes 0."],
        ["(48, 18) → (18, 12) → (12, 6) → (6, 0)", "gcd = 6.",
         "Euclid's algorithm takes O(log min(a, b)) iterations."]),

    trace("pt-prefix", "pc_arrays", 2, "Prefix sums", """
        procedure PrefixSums(A)
            P = new array[length(A)]
            running = 0
            for i = 0 to length(A) - 1
                running = running + A[i]
                P[i] = running
            return P
        """, {"A": [3, 1, 4, 1, 5]}, ["i", "running", "P"], ("loop", "for i = 0"),
        ["P starts as all zeros.", "P[i] holds the sum of A[0..i].", "running accumulates as you go."],
        ["i = 0: running 3, P = [3, 0, 0, 0, 0]", "i = 1: 4", "i = 2: 8", "i = 3: 9", "i = 4: 14 → P = [3, 4, 8, 9, 14]"],
        prompt="Trace the code. Write arrays like 3, 0, 0. Give the values at the END of each iteration."),

    trace("pt-fib", "pc_loops", 3, "Iterative Fibonacci", """
        procedure Fib(n)
            a = 0
            b = 1
            for i = 2 to n
                c = a + b
                a = b
                b = c
            return b
        """, {"n": 7}, ["i", "a", "b"], ("loop", "for i = 2 to n"),
        ["a and b are two consecutive Fibonacci numbers.", "Each step: new b = a + b, and a takes the old b.",
         "Start: a = 0, b = 1."],
        ["i = 2: (1, 1)", "i = 3: (1, 2)", "i = 4: (2, 3)", "i = 5: (3, 5)", "i = 6: (5, 8)", "i = 7: (8, 13)",
         "Θ(n) - compare with the exponential recursive version!"]),

    trace("pt-second", "pc_arrays", 4, "Second-largest tracking", """
        procedure SecondLargest(A)
            first = -infinity
            second = -infinity
            for i = 0 to length(A) - 1
                if A[i] > first
                    second = first
                    first = A[i]
                else if A[i] > second and A[i] < first
                    second = A[i]
            return second
        """, {"A": [5, 9, 3, 9, 7]}, ["i", "first", "second"], ("loop", "for i = 0"),
        ["Write -infinity as -∞ (or -inf).", "A new maximum demotes the old first to second.",
         "The second 9 equals first, so nothing changes."],
        ["i = 0: first 5, second -∞", "i = 1: 9 > 5 → first 9, second 5", "i = 2: 3 → no change",
         "i = 3: 9 is not > 9 and not < 9 → no change", "i = 4: 7 > 5 → second 7"]),
]


DEBUGS = [
    debug("pd-max", "pc_arrays", 1, "FindMaximum returns the wrong value", """
        procedure FindMaximum(numbers)
            largest = 0
            for i = 0 to length(numbers) - 1
                if numbers[i] < largest
                    largest = numbers[i]
            return largest
        """, """
        procedure FindMaximum(numbers)
            largest = numbers[0]
            for i = 0 to length(numbers) - 1
                if numbers[i] > largest
                    largest = numbers[i]
            return largest
        """, ["if numbers[i] < largest", "largest = 0"], "FindMaximum", ["numbers"],
        [T([3, 8, 1], expect=8), T([-5, -2, -9], expect=-2), T([4], expect=4)],
        ["What does the comparison actually look for?", "'<' replaces largest with SMALLER values.",
         "Also: what if every number is negative?"],
        ["Bug 1: 'numbers[i] < largest' updates on smaller values - the comparison is reversed. It must be '>'.",
         "Bug 2: starting at 0 fails when all values are negative (it would return 0, which isn't in the array).",
         "Fix: largest = numbers[0] and compare with '>'.",
         "Reasoning: 'largest' must always be a value from the array that is ≥ everything seen so far."]),

    debug("pd-sum-bounds", "pc_loops", 1, "Sum runs off the end", """
        procedure Sum(A)
            total = 0
            for i = 0 to length(A)
                total = total + A[i]
            return total
        """, """
        procedure Sum(A)
            total = 0
            for i = 0 to length(A) - 1
                total = total + A[i]
            return total
        """, ["for i = 0 to length(A)"], "Sum", ["A"],
        [T([1, 2, 3], expect=6), T([5], expect=5)],
        ["What are the valid indices of an array of length n?", "The last valid index is n - 1.",
         "The loop bound is inclusive."],
        ["Off-by-one: 'for i = 0 to length(A)' visits index n, which doesn't exist.",
         "Valid indices are 0..n - 1, so the bound must be length(A) - 1."]),

    debug("pd-count-even-indent", "pc_counting", 2, "CountEven counts everything", """
        procedure CountEven(numbers)
            count = 0
            for i = 0 to length(numbers) - 1
                if numbers[i] mod 2 == 0
                    print(numbers[i])
                count = count + 1
            return count
        """, """
        procedure CountEven(numbers)
            count = 0
            for i = 0 to length(numbers) - 1
                if numbers[i] mod 2 == 0
                    print(numbers[i])
                    count = count + 1
            return count
        """, ["count = count + 1"], "CountEven", ["numbers"],
        [T([1, 2, 3, 4], expect=2), T([1, 3], expect=0)],
        ["Look at the indentation of the increment.", "Which statements belong to the if?",
         "The increment runs on every iteration right now."],
        ["The increment is indented at the loop level, not inside the if, so it runs for every element.",
         "Fix: indent count = count + 1 under the if.",
         "In indentation-based pseudocode, indentation IS structure."]),

    debug("pd-search-else", "pc_searching", 2, "Linear search gives up too early", """
        procedure LinearSearch(A, target)
            for i = 0 to length(A) - 1
                if A[i] == target
                    return i
                else
                    return -1
        """, """
        procedure LinearSearch(A, target)
            for i = 0 to length(A) - 1
                if A[i] == target
                    return i
            return -1
        """, ["return -1", "else"], "LinearSearch", ["A", "target"],
        [T([4, 7, 1], 7, expect=1), T([4, 7, 1], 4, expect=0), T([4, 7], 9, expect=-1), T([], 9, expect=-1)],
        ["Trace it with target in position 1. What happens at i = 0?",
         "The else returns during the first iteration.",
         "When can you be sure the target is absent?"],
        ["The else branch returns -1 as soon as the FIRST element doesn't match.",
         "'Not found' is only known after checking every element - so return -1 after the loop.",
         "Also note: with the bug, an empty array returns nothing at all."]),

    debug("pd-average-div", "pc_loops", 2, "Average rounds down", """
        procedure Average(numbers)
            total = 0
            for i = 0 to length(numbers) - 1
                total = total + numbers[i]
            return total div length(numbers)
        """, """
        procedure Average(numbers)
            total = 0
            for i = 0 to length(numbers) - 1
                total = total + numbers[i]
            return total / length(numbers)
        """, ["return total div length(numbers)"], "Average", ["numbers"],
        [T([1, 2], expect=1.5), T([2, 4], expect=3)],
        ["Compute the result for [1, 2] by hand.", "What does div do?", "Which operator keeps the fraction?"],
        ["div is integer division: 3 div 2 = 1, so the average 1.5 becomes 1.",
         "Use real division '/'."]),

    debug("pd-binary-infinite", "pc_searching", 4, "Binary search never finishes", """
        procedure BinarySearch(A, target)
            low = 0
            high = length(A) - 1
            while low <= high
                mid = floor((low + high) / 2)
                if A[mid] == target
                    return mid
                else if A[mid] < target
                    low = mid
                else
                    high = mid - 1
            return -1
        """, """
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
        """, ["low = mid\n", "low = mid"], "BinarySearch", ["A", "target"],
        [T([1, 3, 5, 7], 7, expect=3), T([1, 3], 3, expect=1), T([1, 3, 5], 4, expect=-1)],
        ["Trace A = [1, 3], target = 3.", "low = 0, high = 1 → mid = 0 → A[0] < 3 → low = 0 again!",
         "mid has already been ruled out - exclude it."],
        ["When A[mid] < target, mid itself is too small, but 'low = mid' keeps it in the range.",
         "With low + 1 == high, mid = low forever → infinite loop.",
         "Fix: low = mid + 1. Every iteration must shrink the range."]),

    debug("pd-prime-start", "pc_numbers", 2, "IsPrime says nothing is prime", """
        procedure IsPrime(n)
            if n < 2
                return false
            for d = 1 to n - 1
                if n mod d == 0
                    return false
            return true
        """, """
        procedure IsPrime(n)
            if n < 2
                return false
            for d = 2 to n - 1
                if n mod d == 0
                    return false
            return true
        """, ["for d = 1 to n - 1"], "IsPrime", ["n"],
        [T(7, expect=True), T(8, expect=False), T(2, expect=True), T(1, expect=False)],
        ["What is n mod 1?", "Every integer is divisible by 1.", "Which divisors actually matter?"],
        ["n mod 1 = 0 for every n, so the loop returns false immediately.",
         "Divisors to test start at 2.", "(Stopping at √n instead of n - 1 would also speed it up.)"]),

    debug("pd-reverse-twice", "pc_arrays", 3, "Reverse does nothing", """
        procedure Reverse(A)
            n = length(A)
            for i = 0 to n - 1
                swap(A[i], A[n - 1 - i])
            return A
        """, """
        procedure Reverse(A)
            n = length(A)
            for i = 0 to n div 2 - 1
                swap(A[i], A[n - 1 - i])
            return A
        """, ["for i = 0 to n - 1"], "Reverse", ["A"],
        [T([1, 2, 3, 4], expect=[4, 3, 2, 1], check="either"), T([1, 2, 3], expect=[3, 2, 1], check="either")],
        ["Trace [1, 2, 3, 4] to the end.", "After i passes the middle, which pairs are swapped?",
         "Each pair should be swapped exactly once."],
        ["The loop swaps every pair twice: once on the way to the middle, again on the way back.",
         "Two swaps cancel out → the array is unchanged.",
         "Fix: loop only over the first half, i = 0 to n div 2 - 1."]),

    debug("pd-bubble-bounds", "pc_sorting", 3, "Bubble sort reads past the end", """
        procedure BubbleSort(A)
            n = length(A)
            for i = 0 to n - 2
                for j = 0 to n - 1
                    if A[j] > A[j + 1]
                        swap(A[j], A[j + 1])
            return A
        """, """
        procedure BubbleSort(A)
            n = length(A)
            for i = 0 to n - 2
                for j = 0 to n - 2 - i
                    if A[j] > A[j + 1]
                        swap(A[j], A[j + 1])
            return A
        """, ["for j = 0 to n - 1"], "BubbleSort", ["A"],
        [T([3, 1, 2], expect=[1, 2, 3], check="either"), T([2, 1], expect=[1, 2], check="either")],
        ["The body reads A[j + 1].", "What is j + 1 when j = n - 1?", "Index n doesn't exist."],
        ["When j = n - 1, A[j + 1] = A[n] is out of bounds.",
         "The inner bound must keep j + 1 ≤ n - 1: use n - 2 (or n - 2 - i to skip the sorted tail)."]),

    debug("pd-insertion-zero", "pc_sorting", 4, "Insertion sort ignores the first element", """
        procedure InsertionSort(A)
            for i = 1 to length(A) - 1
                key = A[i]
                j = i - 1
                while j > 0 and A[j] > key
                    A[j + 1] = A[j]
                    j = j - 1
                A[j + 1] = key
            return A
        """, """
        procedure InsertionSort(A)
            for i = 1 to length(A) - 1
                key = A[i]
                j = i - 1
                while j >= 0 and A[j] > key
                    A[j + 1] = A[j]
                    j = j - 1
                A[j + 1] = key
            return A
        """, ["while j > 0 and A[j] > key"], "InsertionSort", ["A"],
        [T([3, 1, 2], expect=[1, 2, 3], check="either"), T([2, 1], expect=[1, 2], check="either")],
        ["Trace [2, 1].", "With j = 0, is the loop body ever executed?", "Index 0 is a valid position."],
        ["'j > 0' stops before comparing with A[0], so a key smaller than A[0] is never moved to the front.",
         "Fix: 'j >= 0'."]),

    debug("pd-factorial-base", "pc_recursion", 2, "Factorial always returns 0", """
        procedure Factorial(n)
            if n == 0
                return 0
            return n * Factorial(n - 1)
        """, """
        procedure Factorial(n)
            if n == 0
                return 1
            return n * Factorial(n - 1)
        """, ["return 0"], "Factorial", ["n"],
        [T(3, expect=6), T(0, expect=1), T(5, expect=120)],
        ["What does every chain of multiplications end with?", "Anything × 0 = 0.", "What is 0! by definition?"],
        ["The base case returns 0, and every result is a product that includes the base case → always 0.",
         "0! = 1 (the empty product). Fix: return 1."]),

    debug("pd-count-reset", "pc_counting", 2, "Counter keeps resetting", """
        procedure CountOccurrences(A, target)
            for i = 0 to length(A) - 1
                count = 0
                if A[i] == target
                    count = count + 1
            return count
        """, """
        procedure CountOccurrences(A, target)
            count = 0
            for i = 0 to length(A) - 1
                if A[i] == target
                    count = count + 1
            return count
        """, ["count = 0"], "CountOccurrences", ["A", "target"],
        [T([1, 1, 2], 1, expect=2), T([3, 1], 1, expect=1), T([5, 1], 5, expect=0 + 1)],
        ["Where does count get its starting value?", "That statement runs on every iteration.",
         "Initialization belongs before the loop."],
        ["count = 0 is inside the loop, so the count restarts on every iteration.",
         "The result is at most 1 (only the last element matters).",
         "Fix: initialize once, before the loop."]),

    debug("pd-second-demote", "pc_arrays", 4, "Second largest is wrong", """
        procedure SecondLargest(A)
            first = -infinity
            second = -infinity
            for i = 0 to length(A) - 1
                if A[i] > first
                    first = A[i]
                else if A[i] > second and A[i] < first
                    second = A[i]
            return second
        """, """
        procedure SecondLargest(A)
            first = -infinity
            second = -infinity
            for i = 0 to length(A) - 1
                if A[i] > first
                    second = first
                    first = A[i]
                else if A[i] > second and A[i] < first
                    second = A[i]
            return second
        """, ["first = A[i]", "if A[i] > first"], "SecondLargest", ["A"],
        [T([1, 2, 3], expect=2), T([3, 1, 2], expect=2)],
        ["Trace [1, 2, 3].", "When 2 replaces 1 as the maximum, what should happen to 1?",
         "The old maximum is the new second-largest candidate."],
        ["When a new maximum arrives, the old maximum is lost instead of becoming second.",
         "For increasing input, second is never updated.",
         "Fix: second = first before first = A[i]."]),

    debug("pd-selection-min", "pc_sorting", 4, "Selection sort misplaces elements", """
        procedure SelectionSort(A)
            n = length(A)
            for i = 0 to n - 2
                minIndex = 0
                for j = i + 1 to n - 1
                    if A[j] < A[minIndex]
                        minIndex = j
                swap(A[i], A[minIndex])
            return A
        """, """
        procedure SelectionSort(A)
            n = length(A)
            for i = 0 to n - 2
                minIndex = i
                for j = i + 1 to n - 1
                    if A[j] < A[minIndex]
                        minIndex = j
                swap(A[i], A[minIndex])
            return A
        """, ["minIndex = 0"], "SelectionSort", ["A"],
        [T([3, 1, 2], expect=[1, 2, 3], check="either"), T([2, 3, 1], expect=[1, 2, 3], check="either")],
        ["Trace [3, 1, 2] for i = 1.", "The minimum should come from the UNSORTED part, A[i..n - 1].",
         "Index 0 is already in the sorted part."],
        ["minIndex = 0 lets the search pick an element from the already-sorted prefix and swap it back out.",
         "Fix: minIndex = i."]),

    debug("pd-coins-if", "pc_greedy", 3, "Greedy change uses too few coins", """
        procedure CoinCount(amount, coins)
            count = 0
            for i = 0 to length(coins) - 1
                if amount >= coins[i]
                    amount = amount - coins[i]
                    count = count + 1
            return count
        """, """
        procedure CoinCount(amount, coins)
            count = 0
            for i = 0 to length(coins) - 1
                while amount >= coins[i]
                    amount = amount - coins[i]
                    count = count + 1
            return count
        """, ["if amount >= coins[i]"], "CoinCount", ["amount", "coins"],
        [T(68, [25, 10, 5, 1], expect=7), T(50, [25, 10, 5, 1], expect=2)],
        ["How many quarters go into 50?", "'if' takes each coin at most once.", "Which loop repeats while a condition holds?"],
        ["'if' uses each denomination at most once: 68 → 25 + 10 + 5 + 1 = 41, leaving 27 unpaid.",
         "Fix: 'while' keeps taking the same coin while it still fits."]),

    debug("pd-fib-base", "pc_recursion", 3, "Fibonacci recursion never ends", """
        function Fib(n)
            if n == 0
                return 0
            return Fib(n - 1) + Fib(n - 2)
        """, """
        function Fib(n)
            if n <= 1
                return n
            return Fib(n - 1) + Fib(n - 2)
        """, ["if n == 0"], "Fib", ["n"],
        [T(1, expect=1), T(6, expect=8), T(0, expect=0)],
        ["Trace Fib(1).", "Fib(1) calls Fib(0) and Fib(-1).", "Does any base case catch n = -1?"],
        ["With only n == 0 as a base case, Fib(1) calls Fib(-1), which never reaches 0 → infinite recursion.",
         "Fix: 'if n <= 1 return n' handles both 0 and 1."]),

    debug("pd-min-zero", "pc_arrays", 1, "FindMinimum fails for positive numbers", """
        procedure FindMinimum(numbers)
            smallest = 0
            for i = 0 to length(numbers) - 1
                if numbers[i] < smallest
                    smallest = numbers[i]
            return smallest
        """, """
        procedure FindMinimum(numbers)
            smallest = numbers[0]
            for i = 0 to length(numbers) - 1
                if numbers[i] < smallest
                    smallest = numbers[i]
            return smallest
        """, ["smallest = 0"], "FindMinimum", ["numbers"],
        [T([4, 2, 9], expect=2), T([-1, 5], expect=-1)],
        ["Try [4, 2, 9]. What gets returned?", "No element is smaller than 0.", "Start with a value FROM the array."],
        ["Starting at 0 returns 0 for any all-positive array.", "Fix: smallest = numbers[0]."]),
]
