"""Pseudocode Lab exercises: fill-in, ordering, completion, writing, and pseudocode → complexity."""
from data.builders_pc import fill, order, complete, write, to_complexity, rubric, T

NUMS = ["numbers"]

# ------------------------------------------------------------------------- solutions reused below
SOL_COUNT_EVEN = """
procedure CountEven(numbers)
    count = 0
    for i = 0 to length(numbers) - 1
        if numbers[i] mod 2 == 0
            count = count + 1
    return count
"""

SOL_PRIME = """
procedure IsPrime(n)
    if n < 2
        return false
    d = 2
    while d * d <= n
        if n mod d == 0
            return false
        d = d + 1
    return true
"""

SOL_DUPS = """
procedure HasDuplicate(A)
    n = length(A)
    for i = 0 to n - 2
        for j = i + 1 to n - 1
            if A[i] == A[j]
                return true
    return false
"""

SOL_BINARY = """
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
"""

SOL_SELECTION = """
procedure SelectionSort(A)
    n = length(A)
    for i = 0 to n - 2
        minIndex = i
        for j = i + 1 to n - 1
            if A[j] < A[minIndex]
                minIndex = j
        swap(A[i], A[minIndex])
    return A
"""

SOL_INTERVALS = """
procedure MaxMeetings(intervals)
    // intervals are [start, end] pairs sorted by end time
    count = 0
    lastEnd = -infinity
    for i = 0 to length(intervals) - 1
        if intervals[i][0] >= lastEnd
            count = count + 1
            lastEnd = intervals[i][1]
    return count
"""

SOL_POWER = """
procedure Power(x, n)
    if n == 0
        return 1
    half = Power(x, n div 2)
    if n mod 2 == 0
        return half * half
    else
        return half * half * x
"""

SORT_TESTS = [T([5, 2, 9, 1, 5, 6], expect=[1, 2, 5, 5, 6, 9], check="either"),
              T([], expect=[], check="either"), T([1], expect=[1], check="either"),
              T([3, 2, 1], expect=[1, 2, 3], check="either"), T([-4, 10, 0, -4], expect=[-4, -4, 0, 10], check="either")]

EXERCISES = [
    # =================================================================== A. Fill in the blank
    fill("pf-count-gt10", "pc_counting", 1, "Count values greater than 10",
         "Fill in the blanks so the procedure returns how many values in numbers are greater than 10.",
         """
         procedure CountGreaterThan10(numbers)
             count = 0
             for i = 0 to [[0]]
                 if numbers[i] > 10
                     count = [[1]]
             return [[2]]
         """,
         [["length(numbers)-1", "len(numbers)-1", "numbers.length-1", "size(numbers)-1"],
          ["count+1", "1+count"], ["count"]],
         """
         procedure CountGreaterThan10(numbers)
             count = 0
             for i = 0 to length(numbers) - 1
                 if numbers[i] > 10
                     count = count + 1
             return count
         """, "CountGreaterThan10", NUMS,
         [T([5, 12, 30, 10], expect=2), T([], expect=0), T([11], expect=1), T([1, 2, 3], expect=0)],
         ["Arrays are 0-indexed. What is the index of the last element?",
          "When the condition holds, the counter should grow by one.",
          "What value does the procedure need to hand back?"],
         ["Blank 1: the last valid index is length(numbers) - 1 (indices run 0..n - 1).",
          "Blank 2: count = count + 1 adds one for every value > 10.",
          "Blank 3: return count.",
          "Pattern: initialize → iterate → test → update → return."]),

    fill("pf-sum", "pc_loops", 1, "Sum an array",
         "Complete the accumulator pattern.",
         """
         procedure Sum(numbers)
             total = [[0]]
             for i = 0 to length(numbers) - 1
                 total = [[1]]
             return total
         """,
         [["0"], ["total+numbers[i]", "numbers[i]+total"]],
         """
         procedure Sum(numbers)
             total = 0
             for i = 0 to length(numbers) - 1
                 total = total + numbers[i]
             return total
         """, "Sum", NUMS,
         [T([1, 2, 3], expect=6), T([], expect=0), T([-5, 5, 10], expect=10)],
         ["What should the total be before you've added anything?",
          "Each iteration adds the current element to the running total.",
          "total = total + numbers[i]"],
         ["Blank 1: start at 0 - the sum of no elements.",
          "Blank 2: total = total + numbers[i] updates the running total.",
          "This accumulator pattern is the basis for averages, counts, and many more algorithms."]),

    fill("pf-min", "pc_arrays", 1, "Find the minimum",
         "Fill in the comparison and the update.",
         """
         procedure FindMinimum(numbers)
             smallest = numbers[0]
             for i = 1 to length(numbers) - 1
                 if numbers[i] [[0]] smallest
                     smallest = [[1]]
             return smallest
         """,
         [["<", "<="], ["numbers[i]"]],
         """
         procedure FindMinimum(numbers)
             smallest = numbers[0]
             for i = 1 to length(numbers) - 1
                 if numbers[i] < smallest
                     smallest = numbers[i]
             return smallest
         """, "FindMinimum", NUMS,
         [T([4, 2, 8], expect=2), T([7], expect=7), T([-1, -9, 3], expect=-9), T([5, 5, 6], expect=5)],
         ["When should smallest change?",
          "Only when the current element is smaller than the best so far.",
          "Replace smallest with the current element."],
         ["Blank 1: '<' - a new minimum is smaller than the current smallest.",
          "Blank 2: numbers[i] - remember the new minimum.",
          "Starting from numbers[0] (not 0) makes it work for all-positive arrays too."]),

    fill("pf-average", "pc_loops", 2, "Average of an array",
         "Fill in the blanks. An empty array should return 0.",
         """
         procedure Average(numbers)
             if length(numbers) == [[0]]
                 return 0
             total = 0
             for i = 0 to length(numbers) - 1
                 total = total + numbers[i]
             return [[1]]
         """,
         [["0"], ["total/length(numbers)", "total/len(numbers)", "total/numbers.length"]],
         """
         procedure Average(numbers)
             if length(numbers) == 0
                 return 0
             total = 0
             for i = 0 to length(numbers) - 1
                 total = total + numbers[i]
             return total / length(numbers)
         """, "Average", NUMS,
         [T([2, 4, 6], expect=4), T([], expect=0), T([1, 2], expect=1.5)],
         ["When would dividing be a problem?",
          "The average is the total divided by how many values there are.",
          "total / length(numbers)"],
         ["Blank 1: guard against length 0 to avoid dividing by zero.",
          "Blank 2: total / length(numbers)."]),

    fill("pf-linear-search", "pc_searching", 2, "Linear search",
         "Return the index of target, or -1 if it is not present.",
         """
         procedure LinearSearch(A, target)
             for i = 0 to length(A) - 1
                 if A[i] == [[0]]
                     return [[1]]
             return [[2]]
         """,
         [["target"], ["i"], ["-1"]],
         """
         procedure LinearSearch(A, target)
             for i = 0 to length(A) - 1
                 if A[i] == target
                     return i
             return -1
         """, "LinearSearch", ["A", "target"],
         [T([4, 7, 1], 7, expect=1), T([4, 7, 1], 9, expect=-1), T([], 3, expect=-1), T([2, 2], 2, expect=0)],
         ["What are we comparing each element against?",
          "When found, we return WHERE it was found.",
          "The loop only finishes if nothing matched."],
         ["Blank 1: compare with target.", "Blank 2: return the index i (not the value).",
          "Blank 3: reaching the end of the loop means 'not found' → -1.",
          "Note the -1 return sits AFTER the loop, not in an else branch inside it."]),

    fill("pf-reverse", "pc_arrays", 3, "Reverse an array in place",
         "Two indices walk toward each other, swapping as they go.",
         """
         procedure Reverse(A)
             left = 0
             right = [[0]]
             while [[1]]
                 swap(A[left], A[right])
                 left = [[2]]
                 right = [[3]]
             return A
         """,
         [["length(A)-1", "len(A)-1", "A.length-1"], ["left<right"], ["left+1"], ["right-1"]],
         """
         procedure Reverse(A)
             left = 0
             right = length(A) - 1
             while left < right
                 swap(A[left], A[right])
                 left = left + 1
                 right = right - 1
             return A
         """, "Reverse", ["A"],
         [T([1, 2, 3, 4], expect=[4, 3, 2, 1], check="either"), T([1, 2, 3], expect=[3, 2, 1], check="either"),
          T([], expect=[], check="either"), T([9], expect=[9], check="either")],
         ["Where does the right index start?",
          "Keep going while the indices haven't met or crossed.",
          "After a swap, move both indices inward."],
         ["right starts at the last index, length(A) - 1.",
          "Loop while left < right; when they meet, the middle element stays put.",
          "left moves right (+1), right moves left (-1).",
          "Each swap handles two elements → about n/2 swaps → Θ(n)."]),

    fill("pf-prime", "pc_numbers", 3, "Primality test",
         "Complete the trial-division primality test.",
         """
         procedure IsPrime(n)
             if n < [[0]]
                 return false
             for d = 2 to [[1]]
                 if n mod d == [[2]]
                     return false
             return true
         """,
         [["2"], ["floor(sqrt(n))", "sqrt(n)", "n-1", "ndiv2", "n/2"], ["0"]],
         """
         procedure IsPrime(n)
             if n < 2
                 return false
             for d = 2 to floor(sqrt(n))
                 if n mod d == 0
                     return false
             return true
         """, "IsPrime", ["n"],
         [T(1, expect=False), T(2, expect=True), T(9, expect=False), T(13, expect=True), T(25, expect=False), T(0, expect=False)],
         ["What is the smallest prime?",
          "If n has a divisor, one of its divisors is at most √n.",
          "d divides n exactly when the remainder is 0."],
         ["Blank 1: numbers below 2 are not prime.",
          "Blank 2: checking d up to ⌊√n⌋ is enough (n - 1 also works but is slower: Θ(n) vs Θ(√n)).",
          "Blank 3: n mod d == 0 means d divides n."]),

    fill("pf-binary-search", "pc_searching", 4, "Binary search updates",
         "Fill in the midpoint and how the range shrinks.",
         """
         procedure BinarySearch(A, target)
             low = 0
             high = length(A) - 1
             while low <= high
                 mid = [[0]]
                 if A[mid] == target
                     return mid
                 else if A[mid] < target
                     low = [[1]]
                 else
                     high = [[2]]
             return -1
         """,
         [["floor((low+high)/2)", "(low+high)div2", "(low+high)/2", "low+(high-low)div2", "floor(low+(high-low)/2)"],
          ["mid+1"], ["mid-1"]],
         SOL_BINARY, "BinarySearch", ["A", "target"],
         [T([1, 3, 5, 7, 9], 7, expect=3), T([1, 3, 5, 7, 9], 4, expect=-1), T([], 1, expect=-1),
          T([2], 2, expect=0), T([1, 3, 5, 7, 9, 11], 1, expect=0), T([1, 3, 5, 7, 9, 11], 11, expect=5)],
         ["The midpoint is halfway between low and high (rounded down).",
          "If A[mid] < target, the target is to the RIGHT of mid - and mid itself is ruled out.",
          "Likewise for the left side."],
         ["mid = floor((low + high) / 2)",
          "low = mid + 1: everything up to mid is too small.",
          "high = mid - 1: everything from mid on is too big.",
          "Using low = mid (without + 1) can loop forever when low + 1 == high."]),

    fill("pf-bubble", "pc_sorting", 4, "Bubble sort",
         "Fill in the inner-loop bound and the comparison.",
         """
         procedure BubbleSort(A)
             n = length(A)
             for i = 0 to n - 2
                 for j = 0 to [[0]]
                     if A[j] > [[1]]
                         swap(A[j], A[j + 1])
             return A
         """,
         [["n-2-i", "n-i-2"], ["A[j+1]"]],
         """
         procedure BubbleSort(A)
             n = length(A)
             for i = 0 to n - 2
                 for j = 0 to n - 2 - i
                     if A[j] > A[j + 1]
                         swap(A[j], A[j + 1])
             return A
         """, "BubbleSort", ["A"], SORT_TESTS,
         ["The inner loop compares A[j] with A[j + 1] - so j + 1 must be a valid index.",
          "After pass i, the last i elements are already in their final places.",
          "Compare each element with its right-hand neighbor."],
         ["Blank 1: n - 2 - i. j + 1 ≤ n - 1 - i keeps us inside the unsorted part.",
          "(n - 2 also works but repeats useless comparisons.)",
          "Blank 2: A[j + 1] - swap adjacent elements that are out of order."]),

    fill("pf-factorial", "pc_recursion", 3, "Recursive factorial",
         "Fill in the base case and the recursive call.",
         """
         procedure Factorial(n)
             if n [[0]]
                 return 1
             return n * [[1]]
         """,
         [["<=1", "==0", "=0", "<=0", "<2", "==1"], ["Factorial(n-1)"]],
         """
         procedure Factorial(n)
             if n <= 1
                 return 1
             return n * Factorial(n - 1)
         """, "Factorial", ["n"],
         [T(0, expect=1), T(1, expect=1), T(5, expect=120), T(6, expect=720)],
         ["When can you answer without recursing?",
          "0! = 1! = 1.",
          "n! = n × (n - 1)!"],
         ["Base case: n <= 1 → return 1.",
          "Recursive case: n × Factorial(n - 1) - a smaller instance of the same problem.",
          "Each call reduces n by 1: T(n) = T(n - 1) + c → Θ(n)."]),

    fill("pf-coins", "pc_greedy", 4, "Greedy coin change",
         "coins is sorted from largest to smallest. Count how many coins the greedy strategy uses.",
         """
         procedure CoinCount(amount, coins)
             count = 0
             for i = 0 to length(coins) - 1
                 while amount >= [[0]]
                     amount = [[1]]
                     count = count + 1
             return count
         """,
         [["coins[i]"], ["amount-coins[i]"]],
         """
         procedure CoinCount(amount, coins)
             count = 0
             for i = 0 to length(coins) - 1
                 while amount >= coins[i]
                     amount = amount - coins[i]
                     count = count + 1
             return count
         """, "CoinCount", ["amount", "coins"],
         [T(68, [25, 10, 5, 1], expect=7), T(0, [25, 10, 5, 1], expect=0), T(30, [25, 10, 5, 1], expect=2), T(99, [25, 10, 5, 1], expect=9)],
         ["Greedy: take the largest coin that still fits, as many times as it fits.",
          "Keep using coins[i] while it's not bigger than what remains.",
          "Taking a coin reduces the remaining amount."],
         ["Blank 1: coins[i] - use this coin while it fits.",
          "Blank 2: amount - coins[i].",
          "68 = 25 + 25 + 10 + 5 + 1 + 1 + 1 → 7 coins.",
          "Greedy is optimal for US coins but not for every coin system (e.g. coins 4, 3, 1 for amount 6)."]),

    # =================================================================== B. Put the steps in order
    order("po-max", "pc_arrays", 1, "Find the maximum",
          "Rearrange the statements into a correct algorithm that returns the largest value.",
          """
          procedure FindMaximum(numbers)
              largest = numbers[0]
              for i = 1 to length(numbers) - 1
                  if numbers[i] > largest
                      largest = numbers[i]
              return largest
          """, "FindMaximum", NUMS,
          [T([3, 9, 2], expect=9), T([-4, -2, -8], expect=-2), T([5], expect=5)],
          ["The procedure header always comes first.",
           "You need a best-so-far value before the loop starts.",
           "Return only after the loop has seen every element."],
          ["1. Header.", "2. Initialize largest with the first element.",
           "3. Loop over the remaining elements.", "4. Compare, 5. update.", "6. Return after the loop."]),

    order("po-count-neg", "pc_counting", 1, "Count negative values",
          "Order the statements to count the negative numbers.",
          """
          procedure CountNegative(numbers)
              count = 0
              for i = 0 to length(numbers) - 1
                  if numbers[i] < 0
                      count = count + 1
              return count
          """, "CountNegative", NUMS,
          [T([-1, 2, -3], expect=2), T([], expect=0), T([0, 5], expect=0)],
          ["Initialize first.", "Loop, then test inside the loop.", "Return last."],
          ["Initialize → iterate → test → update → return."]),

    order("po-linear-search", "pc_searching", 2, "Linear search",
          "Order the statements. Return the index of target or -1.",
          """
          procedure LinearSearch(A, target)
              for i = 0 to length(A) - 1
                  if A[i] == target
                      return i
              return -1
          """, "LinearSearch", ["A", "target"],
          [T([5, 8, 2], 2, expect=2), T([5, 8, 2], 7, expect=-1), T([], 1, expect=-1)],
          ["The -1 case can only be decided after the loop.",
           "Inside the loop: test, then return the index.",
           "The indentation shows which statement belongs inside which."],
          ["The loop checks each element; the first match returns immediately.",
           "return -1 is reached only if no element matched."]),

    order("po-average", "pc_loops", 2, "Average with a guard",
          "Order the statements. Empty arrays return 0.",
          """
          procedure Average(numbers)
              n = length(numbers)
              if n == 0
                  return 0
              total = 0
              for i = 0 to n - 1
                  total = total + numbers[i]
              return total / n
          """, "Average", NUMS,
          [T([1, 2, 3], expect=2), T([], expect=0), T([5, 6], expect=5.5)],
          ["n must exist before anything uses it.", "Guard against empty input before dividing.",
           "Accumulate, then divide once at the end."],
          ["Compute n → guard → accumulate → divide."]),

    order("po-selection", "pc_sorting", 4, "Selection sort",
          "Order the statements of selection sort.",
          """
          procedure SelectionSort(A)
              n = length(A)
              for i = 0 to n - 2
                  minIndex = i
                  for j = i + 1 to n - 1
                      if A[j] < A[minIndex]
                          minIndex = j
                  swap(A[i], A[minIndex])
              return A
          """, "SelectionSort", ["A"], SORT_TESTS,
          ["For each position i, find the smallest element in the rest of the array.",
           "minIndex must be reset at the start of every outer iteration.",
           "The swap happens once per outer iteration, after the inner loop."],
          ["Outer loop picks position i; the inner loop finds the index of the minimum of A[i..n - 1];",
           "the swap places it at position i."]),

    order("po-insertion", "pc_sorting", 4, "Insertion sort",
          "Order the statements of insertion sort.",
          """
          procedure InsertionSort(A)
              for i = 1 to length(A) - 1
                  key = A[i]
                  j = i - 1
                  while j >= 0 and A[j] > key
                      A[j + 1] = A[j]
                      j = j - 1
                  A[j + 1] = key
              return A
          """, "InsertionSort", ["A"], SORT_TESTS,
          ["Save the element being inserted before shifting overwrites it.",
           "Shift larger elements one step right.",
           "Drop the key into the gap after the shifting stops."],
          ["key = A[i] must come before any shifting.",
           "The while loop shifts bigger elements right.",
           "A[j + 1] = key places the key in the gap."]),

    order("po-binary", "pc_searching", 4, "Binary search",
          "Order the statements of binary search.",
          SOL_BINARY, "BinarySearch", ["A", "target"],
          [T([1, 4, 6, 9], 6, expect=2), T([1, 4, 6, 9], 5, expect=-1), T([], 5, expect=-1)],
          ["Set up low and high first.",
           "Compute mid at the start of every iteration.",
           "Three outcomes: found, go right, go left."],
          ["low/high → loop → mid → compare → shrink range → return -1 when the range is empty."]),

    order("po-rec-sum", "pc_recursion", 3, "Recursive sum of 1..n",
          "Order the statements so SumTo(n) returns 1 + 2 + ... + n recursively.",
          """
          procedure SumTo(n)
              if n == 0
                  return 0
              rest = SumTo(n - 1)
              return n + rest
          """, "SumTo", ["n"],
          [T(0, expect=0), T(1, expect=1), T(4, expect=10)],
          ["The base case must be checked before the recursive call.",
           "Compute the smaller problem's answer, then use it.",
           "SumTo(n) = n + SumTo(n - 1)."],
          ["Base case first - otherwise the recursion never stops.",
           "Then solve the smaller problem and combine."]),

    order("po-intervals", "pc_greedy", 5, "Interval scheduling (greedy)",
          "Intervals are [start, end] pairs sorted by end time. Order the statements to count the maximum number of non-overlapping intervals.",
          """
          procedure MaxMeetings(intervals)
              count = 0
              lastEnd = -infinity
              for i = 0 to length(intervals) - 1
                  if intervals[i][0] >= lastEnd
                      count = count + 1
                      lastEnd = intervals[i][1]
              return count
          """, "MaxMeetings", ["intervals"],
          [T([[1, 3], [2, 4], [3, 5], [6, 7]], expect=3), T([], expect=0), T([[2, 3], [4, 5], [1, 10]], expect=2)],
          ["Track the end time of the last interval you accepted.",
           "Accept an interval when it starts at or after that end time.",
           "When you accept one, update both the count and lastEnd."],
          ["Greedy rule: always pick the compatible interval that finishes first.",
           "Because the input is sorted by end time, a single pass suffices: Θ(n) (Θ(n log n) including sorting)."]),

    # =================================================================== C. Complete the algorithm
    complete("pc-count-positive", "pc_counting", 1, "Count positive values",
             "Write ONLY the missing logic.",
             """
             procedure CountPositive(numbers)
                 count = 0
                 // Complete this section
                 return count
             """,
             """
             procedure CountPositive(numbers)
                 count = 0
                 for i = 0 to length(numbers) - 1
                     if numbers[i] > 0
                         count = count + 1
                 return count
             """, "CountPositive", NUMS,
             [T([1, -2, 3, 0], expect=2), T([], expect=0), T([-1, -2], expect=0)],
             rubric("loop", "if", "pos", "inc"),
             ["What must you do with every element?", "Test whether it is > 0.", "Increment count when it is."],
             ["Loop over every index, test numbers[i] > 0, increment count.",
              "0 is neither positive nor negative - use > 0, not >= 0."]),

    complete("pc-count-range", "pc_conditionals", 2, "Count values in a range",
             "Count how many values x satisfy low ≤ x ≤ high. Write only the loop.",
             """
             procedure CountInRange(numbers, low, high)
                 count = 0
                 // Complete this section
                 return count
             """,
             """
             procedure CountInRange(numbers, low, high)
                 count = 0
                 for i = 0 to length(numbers) - 1
                     if numbers[i] >= low and numbers[i] <= high
                         count = count + 1
                 return count
             """, "CountInRange", ["numbers", "low", "high"],
             [T([1, 5, 10, 15], 5, 10, expect=2), T([], 0, 1, expect=0), T([3, 3, 3], 3, 3, expect=3)],
             rubric("loop", "if", "inc", extra=[("Two-sided condition", [r"\band\b", r"&&"], "Combine both comparisons with 'and'.")]),
             ["Each value needs two comparisons.", "Use 'and' to require both.", "Include the endpoints (≥ and ≤)."],
             ["The condition numbers[i] >= low and numbers[i] <= high checks both ends.",
              "Using > instead of >= would miss values equal to low."]),

    complete("pc-reverse-copy", "pc_arrays", 2, "Reverse into a new array",
             "Fill B so that B is A reversed. Write only the loop.",
             """
             procedure ReversedCopy(A)
                 n = length(A)
                 B = new array[n]
                 // Complete this section
                 return B
             """,
             """
             procedure ReversedCopy(A)
                 n = length(A)
                 B = new array[n]
                 for i = 0 to n - 1
                     B[i] = A[n - 1 - i]
                 return B
             """, "ReversedCopy", ["A"],
             [T([1, 2, 3], expect=[3, 2, 1]), T([], expect=[]), T([7, 8], expect=[8, 7])],
             rubric("loop", "index", extra=[("Mirror index", [r"n\s*-\s*1\s*-\s*\w+", r"n\s*-\s*\w+\s*-\s*1", r"length\(a\)\s*-\s*1\s*-\s*\w+"],
                                            "Position i in B gets the element at position n - 1 - i in A.")]),
             ["Which element of A belongs at B[0]?", "B[i] ↔ A[n - 1 - i].", "Loop i from 0 to n - 1."],
             ["B[i] = A[n - 1 - i]: the first of B is the last of A.", "One pass → Θ(n) time, Θ(n) extra space."]),

    complete("pc-bubble-inner", "pc_sorting", 4, "Bubble sort: the inner pass",
             "The outer loop is given. Write the inner loop that bubbles the largest remaining element to the end.",
             """
             procedure BubbleSort(A)
                 n = length(A)
                 for i = 0 to n - 2
                     // Complete this section
                 return A
             """,
             """
             procedure BubbleSort(A)
                 n = length(A)
                 for i = 0 to n - 2
                     for j = 0 to n - 2 - i
                         if A[j] > A[j + 1]
                             swap(A[j], A[j + 1])
                 return A
             """, "BubbleSort", ["A"], SORT_TESTS,
             rubric("loop", "if", "swap", extra=[("Adjacent comparison", [r"\[\s*\w+\s*\+\s*1\s*\]"], "Compare A[j] with A[j + 1].")]),
             ["Compare neighbors A[j] and A[j + 1].", "Swap them if they're out of order.",
              "Stop j so that j + 1 is still a valid index."],
             ["for j = 0 to n - 2 - i, swapping out-of-order neighbors.",
              "After pass i, the i + 1 largest elements are in place."]),

    complete("pc-insertion-shift", "pc_sorting", 4, "Insertion sort: shifting",
             "Write the loop that shifts larger elements to the right, then place the key.",
             """
             procedure InsertionSort(A)
                 for i = 1 to length(A) - 1
                     key = A[i]
                     j = i - 1
                     // Complete this section
                 return A
             """,
             """
             procedure InsertionSort(A)
                 for i = 1 to length(A) - 1
                     key = A[i]
                     j = i - 1
                     while j >= 0 and A[j] > key
                         A[j + 1] = A[j]
                         j = j - 1
                     A[j + 1] = key
                 return A
             """, "InsertionSort", ["A"], SORT_TESTS,
             rubric(extra=[("While loop with bound check", [r"while[^\n]*j\s*>=\s*0", r"while[^\n]*j\s*>\s*-\s*1"], "Stop at the start of the array: j >= 0."),
                           ("Shift right", [r"\[\s*j\s*\+\s*1\s*\]\s*=\s*a\[\s*j\s*\]"], "Move A[j] one position to the right."),
                           ("Place key", [r"=\s*key\b"], "Put key into the gap at A[j + 1].")]),
             ["Keep shifting while there's an element to the left that's bigger than key.",
              "Check j >= 0 BEFORE reading A[j].", "After the loop, the gap is at j + 1."],
             ["while j >= 0 and A[j] > key: A[j + 1] = A[j]; j = j - 1",
              "then A[j + 1] = key.",
              "Order in the condition matters: j >= 0 must be tested first so A[-1] is never read."]),

    complete("pc-has-dup", "pc_counting", 3, "Check for duplicates",
             "Write the nested loops that compare every pair.",
             """
             procedure HasDuplicate(A)
                 n = length(A)
                 // Complete this section
                 return false
             """,
             SOL_DUPS, "HasDuplicate", ["A"],
             [T([1, 2, 3, 2], expect=True), T([1, 2, 3], expect=False), T([], expect=False), T([4, 4], expect=True)],
             rubric("nested", "if", extra=[("Early return", [r"return\s+true"], "Return true as soon as a pair matches.")]),
             ["Compare every pair (i, j) with i < j.", "Start j at i + 1 so you never compare an element with itself.",
              "Return true immediately on a match."],
             ["for i = 0 to n - 2, for j = i + 1 to n - 1, if A[i] == A[j] return true.",
              "Comparisons: n(n - 1)/2 in the worst case → Θ(n²)."]),

    complete("pc-second-largest", "pc_arrays", 5, "Second-largest element",
             "Assume at least two DISTINCT values. Track the two largest distinct values in one pass.",
             """
             procedure SecondLargest(A)
                 first = -infinity
                 second = -infinity
                 // Complete this section
                 return second
             """,
             """
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
             """, "SecondLargest", ["A"],
             [T([3, 9, 5, 9, 7], expect=7), T([1, 2], expect=1), T([2, 1], expect=1), T([5, 5, 4], expect=4), T([-3, -1, -2], expect=-2)],
             rubric("loop", "if", extra=[("Demote the old maximum", [r"second\s*=\s*first"], "When a new maximum appears, the old maximum becomes second.")]),
             ["There are two cases: a new maximum, or a value between second and first.",
              "When a new maximum appears, what happens to the old one?",
              "Ignore values equal to first (distinct values)."],
             ["New maximum: second = first, then first = A[i].",
              "Between them: second = A[i] (use A[i] < first to skip duplicates of the max).",
              "One pass → Θ(n)."]),

    complete("pc-intervals", "pc_greedy", 5, "Interval scheduling: selection loop",
             "Intervals are [start, end] pairs sorted by end time. Complete the greedy selection.",
             """
             procedure MaxMeetings(intervals)
                 count = 0
                 lastEnd = -infinity
                 // Complete this section
                 return count
             """,
             SOL_INTERVALS, "MaxMeetings", ["intervals"],
             [T([[1, 3], [2, 4], [3, 5], [6, 7]], expect=3), T([], expect=0), T([[1, 2], [2, 3], [3, 4]], expect=3)],
             rubric("loop", "if", "inc", extra=[("Update last end", [r"lastend\s*=\s*\w+\[[^\]]+\]\s*\[\s*1\s*\]"], "Remember the end time of the interval you accepted.")]),
             ["Visit intervals in order (they're sorted by end time).",
              "Accept an interval when its start ≥ lastEnd.",
              "On accept, update count and lastEnd."],
             ["Greedy choice: the earliest-finishing compatible interval leaves the most room for the rest.",
              "intervals[i][0] is the start, intervals[i][1] is the end."]),

    complete("pc-rec-binary", "pc_recursion", 5, "Recursive binary search",
             "Write the recursive cases.",
             """
             procedure Search(A, target, lo, hi)
                 if lo > hi
                     return -1
                 mid = floor((lo + hi) / 2)
                 if A[mid] == target
                     return mid
                 // Complete this section
             """,
             """
             procedure Search(A, target, lo, hi)
                 if lo > hi
                     return -1
                 mid = floor((lo + hi) / 2)
                 if A[mid] == target
                     return mid
                 if A[mid] < target
                     return Search(A, target, mid + 1, hi)
                 else
                     return Search(A, target, lo, mid - 1)
             """, "Search", ["A", "target", "lo", "hi"],
             [T([1, 3, 5, 7, 9], 9, 0, 4, expect=4), T([1, 3, 5, 7, 9], 1, 0, 4, expect=0), T([1, 3, 5, 7, 9], 4, 0, 4, expect=-1)],
             rubric("if", "rec_call", extra=[("Return the recursive result", [r"return\s+search\s*\("], "Return the result of the recursive call.")]),
             ["Which half can still contain the target?",
              "Recurse on [mid + 1, hi] or [lo, mid - 1].",
              "Don't forget to RETURN the recursive call's result."],
             ["If A[mid] < target, search the right half; otherwise the left half.",
              "Forgetting 'return' is a classic bug: the result is computed and then thrown away."]),

    # =================================================================== D. Write from a description
    write("pw-count-even", "pc_counting", 1, "Count even values",
          "Write pseudocode that receives an array of integers and returns the number of even values.",
          "procedure CountEven(numbers)\n    ", SOL_COUNT_EVEN, "CountEven", NUMS,
          [T([1, 2, 4, 5], expect=2), T([], expect=0), T([-2, 3, 0], expect=2), T([7, 9], expect=0)],
          rubric("init0", "loop", "even", "inc", "return"),
          ["Inputs: an array. Output: a number. What must you track?",
           "A counter starting at 0, and a loop over every element.",
           "Even means x mod 2 == 0."],
          ["count = 0 → loop over all indices → if numbers[i] mod 2 == 0 → count = count + 1 → return count.",
           "Negative even numbers and 0 are even too."]),

    write("pw-sum", "pc_loops", 1, "Sum of an array",
          "Write pseudocode that returns the sum of all values in numbers (0 for an empty array).",
          "procedure Sum(numbers)\n    ",
          """
          procedure Sum(numbers)
              total = 0
              for i = 0 to length(numbers) - 1
                  total = total + numbers[i]
              return total
          """, "Sum", NUMS,
          [T([1, 2, 3], expect=6), T([], expect=0), T([-1, 1], expect=0)],
          rubric("init0", "loop", "accum", "return"),
          ["What should the answer be for an empty array?", "Keep a running total.", "Add each element to it."],
          ["total = 0; for each index add numbers[i]; return total."]),

    write("pw-count-neg", "pc_counting", 1, "Count negative values",
          "Write pseudocode that returns how many values in numbers are negative.",
          "procedure CountNegative(numbers)\n    ",
          """
          procedure CountNegative(numbers)
              count = 0
              for i = 0 to length(numbers) - 1
                  if numbers[i] < 0
                      count = count + 1
              return count
          """, "CountNegative", NUMS,
          [T([-1, 2, -3, 0], expect=2), T([], expect=0), T([4], expect=0)],
          rubric("init0", "loop", "neg", "inc", "return"),
          ["Same shape as counting evens.", "Negative means < 0.", "0 is not negative."],
          ["Initialize, iterate, test numbers[i] < 0, increment, return."]),

    write("pw-max", "pc_arrays", 2, "Find the maximum",
          "Write pseudocode that returns the largest value in a non-empty array. It must work for all-negative arrays.",
          "procedure FindMaximum(numbers)\n    ",
          """
          procedure FindMaximum(numbers)
              largest = numbers[0]
              for i = 1 to length(numbers) - 1
                  if numbers[i] > largest
                      largest = numbers[i]
              return largest
          """, "FindMaximum", NUMS,
          [T([3, 8, 1], expect=8), T([-5, -2, -9], expect=-2), T([4], expect=4)],
          rubric("first", "loop", "if", "return"),
          ["What should the best-so-far start as? (0 fails for all-negative arrays.)",
           "Start from numbers[0].", "Replace it whenever you see something bigger."],
          ["largest = numbers[0], then compare with every other element.",
           "Starting at 0 is the most common bug in this algorithm."]),

    write("pw-linear-search", "pc_searching", 2, "Linear search",
          "Return the index of the first occurrence of target in A, or -1 if it isn't there.",
          "procedure LinearSearch(A, target)\n    ",
          """
          procedure LinearSearch(A, target)
              for i = 0 to length(A) - 1
                  if A[i] == target
                      return i
              return -1
          """, "LinearSearch", ["A", "target"],
          [T([4, 2, 7, 2], 2, expect=1), T([4, 2, 7], 5, expect=-1), T([], 1, expect=-1)],
          rubric("loop", "if", "neg1"),
          ["Check each index in order.", "Return as soon as you find it.", "Only return -1 after checking everything."],
          ["Return i on the first match; return -1 after the loop.",
           "Best case Θ(1), worst case Θ(n)."]),

    write("pw-average", "pc_loops", 2, "Average",
          "Return the average of the values in numbers. Return 0 for an empty array.",
          "procedure Average(numbers)\n    ",
          """
          procedure Average(numbers)
              if length(numbers) == 0
                  return 0
              total = 0
              for i = 0 to length(numbers) - 1
                  total = total + numbers[i]
              return total / length(numbers)
          """, "Average", NUMS,
          [T([2, 4, 9], expect=5), T([], expect=0), T([1, 2], expect=1.5)],
          rubric("empty", "loop", "accum", "divide", "return"),
          ["Handle the empty array first.", "Sum the values.", "Divide by the count."],
          ["Guard → accumulate → divide.", "Without the guard, an empty array divides by zero."]),

    write("pw-count-occ", "pc_counting", 2, "Count occurrences",
          "Return how many times target appears in A.",
          "procedure CountOccurrences(A, target)\n    ",
          """
          procedure CountOccurrences(A, target)
              count = 0
              for i = 0 to length(A) - 1
                  if A[i] == target
                      count = count + 1
              return count
          """, "CountOccurrences", ["A", "target"],
          [T([1, 3, 1, 1], 1, expect=3), T([], 5, expect=0), T([2, 4], 3, expect=0)],
          rubric("init0", "loop", "if", "inc", "return"),
          ["Don't stop at the first match.", "Compare each element with target.", "Increment a counter."],
          ["Unlike linear search, we must keep going after a match: always Θ(n)."]),

    write("pw-prime", "pc_numbers", 3, "Is it prime?",
          "Return true if n is prime and false otherwise. (Numbers below 2 are not prime.)",
          "procedure IsPrime(n)\n    ", SOL_PRIME, "IsPrime", ["n"],
          [T(0, expect=False), T(1, expect=False), T(2, expect=True), T(3, expect=True), T(4, expect=False),
           T(17, expect=True), T(21, expect=False), T(49, expect=False), T(97, expect=True)],
          rubric("if", "loop", "sqrt", "return"),
          ["Handle n < 2 first.", "Try every divisor d from 2 upward.",
           "You can stop once d * d > n."],
          ["If n < 2 → false. For d = 2, 3, ... while d * d ≤ n: if n mod d == 0 → false. Otherwise → true.",
           "Stopping at √n makes this Θ(√n) instead of Θ(n)."]),

    write("pw-reverse", "pc_arrays", 3, "Reverse an array",
          "Reverse A. You may reverse it in place (and return A) or return a new reversed array.",
          "procedure Reverse(A)\n    ",
          """
          procedure Reverse(A)
              left = 0
              right = length(A) - 1
              while left < right
                  swap(A[left], A[right])
                  left = left + 1
                  right = right - 1
              return A
          """, "Reverse", ["A"],
          [T([1, 2, 3, 4], expect=[4, 3, 2, 1], check="either"), T([1, 2, 3], expect=[3, 2, 1], check="either"),
           T([], expect=[], check="either"), T([5], expect=[5], check="either")],
          rubric("loop", "index"),
          ["Two indices: one at each end.", "Swap, then move them toward the middle.",
           "Stop when they meet - going further un-reverses it."],
          ["In place: swap A[left] and A[right] while left < right.",
           "Looping over the WHOLE array with swaps reverses it twice (a classic bug)."]),

    write("pw-duplicates", "pc_counting", 3, "Find duplicates",
          "Return true if any value appears more than once in A, false otherwise.",
          "procedure HasDuplicate(A)\n    ", SOL_DUPS, "HasDuplicate", ["A"],
          [T([1, 2, 3, 1], expect=True), T([1, 2, 3], expect=False), T([], expect=False), T([7, 7], expect=True)],
          rubric("nested", "if", "return"),
          ["Compare every pair of positions.", "Make sure you never compare an element with itself.",
           "Return false only after all pairs are checked."],
          ["Nested loops over pairs i < j; return true on a match; false after the loops.",
           "Θ(n²) worst case. (Sorting first gives Θ(n log n).)"]),

    write("pw-selection-sort", "pc_sorting", 4, "Selection sort",
          "Sort A in ascending order using selection sort. Sort in place (you may also return A).",
          "procedure SelectionSort(A)\n    ", SOL_SELECTION, "SelectionSort", ["A"], SORT_TESTS,
          rubric("nested", "swap", extra=[("Track the minimum's index", [r"\bmin\w*\s*=\s*\w+"], "Remember WHERE the minimum is, so you can swap it.")]),
          ["For position i, find the smallest element among A[i..n - 1].",
           "Remember its index, not just its value.",
           "Swap it into position i."],
          ["Outer loop i = 0..n - 2; inner loop finds minIndex; swap A[i], A[minIndex].",
           "Always n(n - 1)/2 comparisons → Θ(n²)."]),

    write("pw-binary-search", "pc_searching", 4, "Binary search",
          "A is sorted ascending. Return an index of target, or -1. Use binary search (not a linear scan).",
          "procedure BinarySearch(A, target)\n    ", SOL_BINARY, "BinarySearch", ["A", "target"],
          [T([1, 3, 5, 7, 9, 11], 9, expect=4), T([1, 3, 5, 7, 9, 11], 1, expect=0), T([1, 3, 5, 7, 9, 11], 11, expect=5),
           T([1, 3, 5, 7, 9, 11], 6, expect=-1), T([], 1, expect=-1), T([4], 4, expect=0)],
          rubric("loop", "mid", "halve", "neg1"),
          ["Keep a range [low, high] that could still contain the target.",
           "Look at the middle; discard the half that can't contain the target.",
           "Stop when low > high."],
          ["low = 0, high = n - 1; while low ≤ high: mid; compare; move low or high past mid.",
           "Θ(log n) worst case."]),

    write("pw-rec-power", "pc_recursion", 4, "Recursive power",
          "Write a RECURSIVE procedure Power(x, n) that returns xⁿ for n ≥ 0 (no loops, no ^ operator).",
          "procedure Power(x, n)\n    ", SOL_POWER, "Power", ["x", "n"],
          [T(2, 0, expect=1), T(2, 10, expect=1024), T(3, 3, expect=27), T(5, 1, expect=5)],
          rubric("base", "rec_call", "return",
                 extra=[("No loops", [r"^(?![\s\S]*\b(for|while)\b)"], "Solve it with recursion instead of a loop.")]),
          ["What is x⁰?", "xⁿ = x · xⁿ⁻¹ works (Θ(n) calls).",
           "Faster: xⁿ = (x^(n/2))² - compute x^(n/2) ONCE and square it."],
          ["Base case n == 0 → 1.",
           "Simple version: return x * Power(x, n - 1) → Θ(n).",
           "Fast version: half = Power(x, n div 2); return half*half (× x if n is odd) → Θ(log n)."]),

    write("pw-coins", "pc_greedy", 5, "Greedy coin change",
          "coins is sorted from largest to smallest. Return the number of coins the greedy strategy uses to make amount.",
          "procedure CoinCount(amount, coins)\n    ",
          """
          procedure CoinCount(amount, coins)
              count = 0
              for i = 0 to length(coins) - 1
                  while amount >= coins[i]
                      amount = amount - coins[i]
                      count = count + 1
              return count
          """, "CoinCount", ["amount", "coins"],
          [T(68, [25, 10, 5, 1], expect=7), T(0, [25, 10, 5, 1], expect=0), T(41, [25, 10, 5, 1], expect=4), T(12, [10, 6, 1], expect=3)],
          rubric("init0", "loop", "inc", "return"),
          ["Greedy: always take the largest coin that fits.", "A coin may be used many times: while, not if.",
           "Subtract and count each coin you take."],
          ["for each coin (largest first): while it fits, take it.",
           "Note: for coins [10, 6, 1] and amount 12, greedy uses 10 + 1 + 1 = 3 coins but 6 + 6 = 2 is optimal. Greedy isn't always optimal."]),

    write("pw-second-largest", "pc_arrays", 5, "Second-largest value",
          "Return the second-largest DISTINCT value in A (A contains at least two distinct values). One pass, no sorting.",
          "procedure SecondLargest(A)\n    ",
          """
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
          """, "SecondLargest", ["A"],
          [T([4, 9, 2, 9, 7], expect=7), T([1, 2], expect=1), T([2, 1], expect=1), T([-5, -1, -3], expect=-3), T([8, 8, 3], expect=3)],
          rubric("loop", "if", "return", extra=[("Demote the old maximum", [r"=\s*first\b", r"=\s*max\w*\b", r"=\s*largest\b"],
                                                  "When a new maximum is found, the old maximum becomes the second largest.")]),
          ["Track two values: the largest and second largest so far.",
           "A new maximum pushes the old maximum down to second.",
           "Values equal to the maximum shouldn't become second."],
          ["Two cases per element: new max (demote old max), or strictly between second and first.",
           "Θ(n), one pass."]),

    write("pw-intervals", "pc_greedy", 6, "Interval scheduling",
          "intervals is a list of [start, end] pairs sorted by end time. Return the maximum number of non-overlapping intervals "
          "(an interval may start exactly when the previous one ends).",
          "procedure MaxMeetings(intervals)\n    ", SOL_INTERVALS, "MaxMeetings", ["intervals"],
          [T([[1, 3], [2, 4], [3, 5], [6, 7]], expect=3), T([], expect=0), T([[2, 3], [3, 4], [4, 9], [1, 10]], expect=3),
           T([[0, 1]], expect=1)],
          rubric("init0", "loop", "if", "return"),
          ["Greedy: pick the interval that finishes first, then the next one compatible with it...",
           "Keep the end time of the last chosen interval.",
           "An interval is compatible when its start ≥ that end time."],
          ["count = 0, lastEnd = -∞; for each interval in order: if start ≥ lastEnd, take it.",
           "Proof idea (exchange argument): replacing any optimal first choice with the earliest-finishing interval never hurts.",
           "Θ(n) after sorting; Θ(n log n) including the sort."]),

    # =================================================================== G. Pseudocode → complexity
    to_complexity("tc-count-even", "pw-count-even", 2, "Complexity of CountEven", "n",
                  ["1", "log n", "n", "n log n", "n²"],
                  ["How many times does the loop run?", "What does one iteration cost?", "n × O(1)."],
                  ["The loop runs n = length(numbers) times.", "Each iteration: one mod, one comparison, maybe an increment → O(1).",
                   "T(n) = Θ(n) - for every input, not just the worst case."], "pc_counting"),

    to_complexity("tc-prime", "pw-prime", 4, "Complexity of IsPrime", "√n",
                  ["1", "log n", "√n", "n", "n log n"],
                  ["When does the loop stop in the worst case (n prime)?", "d goes up to √n.", "Count the values of d."],
                  ["Worst case: n is prime, so the loop runs until d * d > n.",
                   "d = 2, 3, ..., ⌊√n⌋ → about √n iterations.",
                   "Θ(√n) worst case. (Measured in the value n; in terms of the number of digits it's exponential!)"],
                  "pc_numbers"),

    to_complexity("tc-duplicates", "pw-duplicates", 3, "Complexity of HasDuplicate", "n²",
                  ["n", "n log n", "n²", "n³", "2ⁿ"],
                  ["What happens when there are no duplicates?", "Every pair (i, j) with i < j is compared.",
                   "How many pairs?"],
                  ["Worst case (all distinct): pairs = n(n - 1)/2.", "Θ(n²) worst case; best case Θ(1) (A[0] == A[1])."],
                  "pc_counting"),

    to_complexity("tc-binary", "pw-binary-search", 4, "Complexity of BinarySearch", "log n",
                  ["1", "log n", "√n", "n", "n log n"],
                  ["How big is the range after each iteration?", "It halves.", "How many halvings until it's empty?"],
                  ["Each iteration discards at least half of [low, high].", "≈ log₂ n + 1 iterations in the worst case → Θ(log n)."],
                  "pc_searching"),

    to_complexity("tc-selection", "pw-selection-sort", 4, "Complexity of SelectionSort", "n²",
                  ["n", "n log n", "n²", "n³"],
                  ["Count comparisons in the inner loop for each i.", "(n - 1) + (n - 2) + ... + 1.", "That sum is n(n - 1)/2."],
                  ["Inner loop for position i: n - 1 - i comparisons.", "Total: n(n - 1)/2 → Θ(n²) on every input."],
                  "pc_sorting"),

    to_complexity("tc-intervals", "pw-intervals", 5, "Complexity of MaxMeetings", "n",
                  ["1", "log n", "n", "n log n", "n²"],
                  ["The input is already sorted - is there any nested loop?", "One pass over the intervals.",
                   "O(1) work per interval."],
                  ["One pass, constant work per interval → Θ(n).",
                   "If the input weren't sorted, sorting first would cost Θ(n log n), which would dominate."],
                  "pc_greedy"),

    to_complexity("tc-power", "pw-rec-power", 5, "Complexity of fast Power", "log n",
                  ["1", "log n", "n", "n log n", "n²"],
                  ["How many recursive calls does each invocation make?", "One call on n div 2.",
                   "T(n) = T(n/2) + c."],
                  ["The reference solution calls Power(x, n div 2) ONCE and reuses the result.",
                   "T(n) = T(n/2) + c → Θ(log n).",
                   "If you wrote x * Power(x, n - 1), your version is Θ(n) - compare the two!"],
                  "pc_recursion"),
]
