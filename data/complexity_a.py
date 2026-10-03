"""Complexity-analysis exercises, part 1: levels 1-3 (fundamentals, sequential/nested, multiple variables)."""
from data.builders import ident, analyze, count_ex
from engine.growth import ONE, LOG, SQRT, N, NLOG, N2, N3, EXP, FACT

MULTI = ["n + m", "nm", "n²", "n", "m", "nm + n"]

EXERCISES = [
    # ------------------------------------------------------------------ Level 1
    ident("c1-const-assign", 1, "fundamentals", "Straight-line code", """
        x = 5
        y = x * 2
        z = y + 7
        print(z)
        """, ONE,
        ["Is there any loop or recursive call? Count how many statements run.",
         "Each statement runs exactly once, no matter how large n is.",
         "A fixed number of constant-time steps is still constant: 4 × O(1)."],
        ["There are 4 statements and no loops.",
         "Each executes exactly once, independent of n.",
         "T(n) = 4 · c = constant",
         "Therefore T(n) ∈ Θ(1), and the tightest upper bound is O(1)."],
        [("x = 5", "runs once"), ("print(z)", "runs once")]),

    ident("c1-linear-print", 1, "fundamentals", "A single counting loop", """
        for i = 1 to n
            print(i)
        """, N,
        ["Count how many times the loop header lets the body run.",
         "i takes the values 1, 2, ..., n. How many values is that?",
         "Multiply the number of iterations by the cost of the body (constant)."],
        ["The loop executes n times (i = 1, 2, ..., n).",
         "The body performs constant work each iteration.",
         "T(n) = n × O(1) = O(n)",
         "The count is exactly n, so the bound is tight: Θ(n)."],
        [("for i = 1 to n", "n iterations"), ("print(i)", "O(1) per iteration")]),

    ident("c1-fixed-bound", 1, "fundamentals", "A loop with a fixed bound", """
        for i = 1 to 100
            total = total + i
        print(total)
        """, ONE,
        ["Look carefully at the loop bound. Does it depend on n at all?",
         "The loop always runs 100 times, even if n is a billion.",
         "100 × O(1) is a constant."],
        ["The loop runs exactly 100 times regardless of the input size.",
         "T(n) = 100 · c + c = constant",
         "Constants are ignored in asymptotic analysis, so T(n) ∈ Θ(1).",
         "Lesson: a loop is only O(n) when its iteration count grows with n."],
        [("for i = 1 to 100", "100 iterations (constant)")]),

    ident("c1-array-sum", 1, "fundamentals", "Summing an array", """
        procedure Sum(A)
            total = 0
            for i = 0 to length(A) - 1
                total = total + A[i]
            return total
        """, N,
        ["Let n = length(A). How many times does the loop body run?",
         "Indices 0 through n - 1: that's n iterations, each doing one addition.",
         "Add the constant work outside the loop: c₁ + c₂·n."],
        ["Let n = length(A).",
         "total = 0 and return total run once each: constant.",
         "The loop runs for i = 0, 1, ..., n - 1 → n iterations of O(1) work.",
         "T(n) = c₁ + c₂·n ∈ Θ(n)"],
        [("for i = 0 to length(A) - 1", "n iterations"), ("total = total + A[i]", "O(1) body")]),

    ident("c1-step-two", 1, "fundamentals", "Skipping every other element", """
        i = 1
        while i <= n
            print(i)
            i = i + 2
        """, N,
        ["How much does i increase each iteration?",
         "i goes 1, 3, 5, ... up to n. Roughly how many values is that?",
         "n/2 iterations. What does a constant factor of 1/2 do asymptotically?"],
        ["i increases by 2 each iteration: 1, 3, 5, ...",
         "The loop runs about n/2 times (exactly ⌈n/2⌉).",
         "T(n) ≈ (1/2)·n",
         "Constant factors are dropped: T(n) ∈ Θ(n).",
         "Adding a constant step (+2, +3, +100) still gives linear time."],
        [("while i <= n", "≈ n/2 iterations"), ("i = i + 2", "additive step: linear")]),

    ident("c1-first-last", 1, "fundamentals", "Accessing array elements", """
        procedure Ends(A)
            n = length(A)
            first = A[0]
            last = A[n - 1]
            return first + last
        """, ONE,
        ["Does array indexing depend on the position you access?",
         "Accessing A[n - 1] is a single address calculation - not a walk through the array.",
         "Count the statements: all constant."],
        ["Array access A[k] is O(1) for any index k (random access).",
         "length(A) is O(1) for an array.",
         "There are 5 constant-time statements and no loops.",
         "T(n) ∈ Θ(1)"],
        [("last = A[n - 1]", "O(1) random access")]),

    ident("c1-countdown", 1, "fundamentals", "Counting down", """
        for i = n downto 1
            if i mod 2 == 0
                print(i)
        """, N,
        ["Direction doesn't matter; count the iterations.",
         "The if statement is constant work per iteration, whether or not it prints.",
         "n iterations × O(1)."],
        ["The loop runs n times (i = n, n - 1, ..., 1).",
         "Each iteration does a constant-time test and maybe a print: O(1).",
         "T(n) = n · O(1) = Θ(n)"],
        [("for i = n downto 1", "n iterations"), ("if i mod 2 == 0", "O(1) test")], wrap="Θ"),

    analyze("c1-several-statements", 1, "fundamentals", "Several statements per iteration", """
        for i = 1 to n
            x = x + 1
            y = y * 2
            z = x + y
            print(z)
        """, N,
        ["Write the cost of ONE iteration first.",
         "The body is 4 constant statements: 4c per iteration.",
         "Total = n × 4c. Drop the constant."],
        ["Body cost: 4 statements × O(1) = 4c",
         "Iterations: n",
         "T(n) = 4c · n",
         "Drop the constant 4c → T(n) ∈ Θ(n)",
         "More statements inside a loop change the constant, not the growth rate."],
        [("for i = 1 to n", "n iterations"), (["x = x + 1", "print(z)"], "4 constant statements")]),

    count_ex("c1-count-linear", 1, "fundamentals", "Counting a single loop", """
        count = 0
        for i = 1 to n
            count = count + 1
        """, "count = count + 1", {"n": 10},
        lambda n: sum(1 for i in range(1, n + 1)),
        ["n", "n + 1", "n/2", "n²"], "n", N,
        ["Try it by hand: how many values does i take when n = 10?",
         "For general n, i takes n values.",
         "A count of exactly n is linear."],
        ["For n = 10: i = 1, 2, ..., 10 → 10 executions.",
         "In general: n executions.",
         "T(n) = n → Θ(n)"],
        [("for i = 1 to n", "n iterations"), ("count = count + 1", "counted operation")],
        expr_fn=lambda n: n),

    ident("c1-half-loop", 1, "fundamentals", "Looping over half the input", """
        for i = 1 to n / 2
            print(A[i])
        """, N,
        ["How many iterations when n = 100? When n = 1000?",
         "Doubling n doubles the number of iterations.",
         "n/2 = (1/2)·n; drop the constant factor."],
        ["The loop runs n/2 times.",
         "T(n) = (1/2)·n·c",
         "Halving the work is a constant factor: T(n) ∈ Θ(n), not Θ(log n).",
         "Only repeatedly halving (i = i / 2) leads to logarithms."],
        [("for i = 1 to n / 2", "n/2 iterations → still linear")]),

    # ------------------------------------------------------------------ Level 2
    ident("c2-seq-two", 2, "sequential", "Two loops, one after the other", """
        for i = 1 to n
            print(i)
        for j = 1 to n
            print(j)
        """, N,
        ["Are these loops nested or sequential?",
         "Sequential sections ADD: first loop cost + second loop cost.",
         "n + n = 2n. Drop the constant."],
        ["First loop: n iterations of O(1).",
         "Second loop: n iterations of O(1), starting after the first finishes.",
         "Sequential → add: T(n) = n + n = 2n",
         "O(n) + O(n) = O(n) → Θ(n)"],
        [("for i = 1 to n", "section 1: n"), ("for j = 1 to n", "section 2: n (added, not multiplied)")]),

    ident("c2-nested-two", 2, "nested_loops", "A loop inside a loop", """
        for i = 1 to n
            for j = 1 to n
                print(i, j)
        """, N2,
        ["Count how many times the outer loop executes.",
         "Now determine how many times the inner loop executes for EACH outer iteration.",
         "Multiply the two iteration counts."],
        ["Outer loop: n iterations",
         "Inner loop: n iterations for every outer iteration",
         "Total:",
         "n × n = n²",
         "Therefore: Θ(n²)"],
        [("for i = 1 to n", "outer: n"), ("for j = 1 to n", "inner: n per outer iteration"),
         ("print(i, j)", "runs n × n times")]),

    ident("c2-seq-then-nested", 2, "sequential", "A single loop followed by a nested loop", """
        for i = 1 to n
            A[i] = 0
        for i = 1 to n
            for j = 1 to n
                A[i] = A[i] + B[j]
        """, N2,
        ["Split the code into two sections and analyze each one separately.",
         "Section 1 is n. Section 2 is n × n.",
         "Add the sections and keep only the dominant term."],
        ["Section 1 (single loop): n",
         "Section 2 (nested loops): n × n = n²",
         "Sequential → T(n) = n + n²",
         "The dominant term is n² (the n term becomes negligible).",
         "T(n) ∈ Θ(n²)"],
        [("A[i] = 0", "section 1: n"), ("for j = 1 to n", "section 2: n × n")]),

    ident("c2-triple", 2, "nested_loops", "Three nested loops", """
        for i = 1 to n
            for j = 1 to n
                for k = 1 to n
                    C[i][j] = C[i][j] + A[i][k] * B[k][j]
        """, N3,
        ["Three loops, each with n iterations - are they nested or sequential?",
         "Each level multiplies the work of the level below.",
         "n × n × n."],
        ["Outer i-loop: n iterations",
         "Middle j-loop: n per i",
         "Inner k-loop: n per (i, j) pair",
         "Total = n × n × n = n³",
         "This is standard matrix multiplication: Θ(n³)."],
        [("for i = 1 to n", "n"), ("for j = 1 to n", "× n"), ("for k = 1 to n", "× n")]),

    ident("c2-inner-constant", 2, "nested_loops", "Nested, but the inner bound is fixed", """
        for i = 1 to n
            for j = 1 to 5
                print(i * j)
        """, N,
        ["Does the inner loop's iteration count grow with n?",
         "The inner loop always runs 5 times.",
         "n × 5 = 5n."],
        ["Outer loop: n iterations",
         "Inner loop: exactly 5 iterations (constant)",
         "T(n) = 5n",
         "T(n) ∈ Θ(n) - nesting only multiplies growth when BOTH loops grow with n."],
        [("for j = 1 to 5", "constant 5"), ("for i = 1 to n", "n")]),

    ident("c2-three-seq", 2, "sequential", "Three passes over the data", """
        procedure Stats(A)
            n = length(A)
            total = 0
            for i = 0 to n - 1
                total = total + A[i]
            mean = total / n
            biggest = A[0]
            for i = 1 to n - 1
                if A[i] > biggest
                    biggest = A[i]
            above = 0
            for i = 0 to n - 1
                if A[i] > mean
                    above = above + 1
            return above
        """, N,
        ["How many separate loops are there, and are any of them nested?",
         "Each loop is a separate pass over the array.",
         "n + (n - 1) + n = 3n - 1."],
        ["Pass 1 (sum): n", "Pass 2 (max): n - 1", "Pass 3 (count above mean): n",
         "Sequential → T(n) = 3n - 1 + constant",
         "T(n) ∈ Θ(n): three passes is still linear."],
        [("total = total + A[i]", "pass 1"), ("if A[i] > biggest", "pass 2"), ("if A[i] > mean", "pass 3")],
        wrap="Θ"),

    count_ex("c2-count-nested", 2, "nested_loops", "Counting a nested loop", """
        count = 0
        for i = 1 to n
            for j = 1 to n
                count = count + 1
        """, "count = count + 1", {"n": 4},
        lambda n: sum(1 for i in range(1, n + 1) for j in range(1, n + 1)),
        ["n", "2n", "n²", "n(n+1)/2"], "n²", N2,
        ["For n = 4, write out the pairs (i, j). How many are there?",
         "Every value of i is paired with every value of j.",
         "n choices × n choices."],
        ["For n = 4: 4 outer iterations × 4 inner iterations = 16.",
         "In general: n × n = n²",
         "T(n) = n² → Θ(n²)"],
        [("for i = 1 to n", "n"), ("for j = 1 to n", "n per i")],
        expr_fn=lambda n: n * n),

    count_ex("c2-count-seq", 2, "sequential", "Counting sequential loops", """
        count = 0
        for i = 1 to n
            count = count + 1
        for j = 1 to n
            count = count + 1
        """, "count = count + 1", {"n": 5},
        lambda n: 2 * n,
        ["n", "2n", "n²", "n + 1"], "2n", N,
        ["For n = 5, how many times does each loop increment count?",
         "The loops run one after the other, so their counts add.",
         "2n. What happens to the constant 2?"],
        ["For n = 5: 5 + 5 = 10.",
         "In general: n + n = 2n",
         "T(n) = 2n → Θ(n). Compare with the nested version, which gives n²."],
        [("for i = 1 to n", "n"), ("for j = 1 to n", "+ n")],
        expr_fn=lambda n: 2 * n),

    ident("c2-seq-nested-pair", 2, "sequential", "Two nested blocks in sequence", """
        for i = 1 to n
            for j = 1 to n
                A[i][j] = 0
        for i = 1 to n
            for j = 1 to n
                A[i][j] = A[i][j] + 1
        """, N2,
        ["Identify the two top-level sections.",
         "Each section on its own is n × n.",
         "n² + n² = 2n²."],
        ["Block 1: n × n = n²", "Block 2: n × n = n²",
         "Sequential → T(n) = 2n²", "T(n) ∈ Θ(n²) - two quadratic passes are still quadratic."],
        [("A[i][j] = 0", "block 1: n²"), ("A[i][j] = A[i][j] + 1", "block 2: n²")]),

    ident("c2-if-heavy", 2, "conditionals", "A branch with an expensive side", """
        for i = 1 to n
            if A[i] > 0
                for j = 1 to n
                    print(A[i] * j)
            else
                print(0)
        """, N2,
        ["For big-O of the worst case, which branch should you assume is taken?",
         "In the worst case every A[i] > 0, so the inner loop runs every time.",
         "n outer iterations × n inner iterations."],
        ["Outer loop: n iterations",
         "Branch cost: the 'if' side costs n, the 'else' side costs 1.",
         "Worst case (every A[i] > 0): n × n = n²",
         "Best case (every A[i] ≤ 0): n × 1 = n",
         "The tightest upper bound on the running time for all inputs is O(n²)."],
        [("for i = 1 to n", "n"), ("for j = 1 to n", "n when the condition is true"), ("print(0)", "O(1) branch")]),

    ident("c2-if-const-cond", 2, "conditionals", "Branches with different costs", """
        if flag == true
            for i = 1 to n
                print(i)
        else
            for i = 1 to n
                for j = 1 to n
                    print(i + j)
        """, N2,
        ["Analyze each branch separately.",
         "The 'if' branch is n; the 'else' branch is n².",
         "An upper bound must cover whichever branch the input selects."],
        ["Branch 1: n", "Branch 2: n × n = n²",
         "Worst case: T(n) = max(n, n²) = n²",
         "Only one branch runs, so we take the MAX, not the sum.",
         "Tightest upper bound: O(n²)."],
        [("for i = 1 to n", "if-branch: n"), ("for j = 1 to n", "else-branch: n²")]),

    analyze("c2-nested-plus-log", 2, "nested_loops", "Nested loops with extra constant work", """
        for i = 1 to n
            x = 0
            for j = 1 to n
                x = x + A[j]
            B[i] = x
        """, N2,
        ["Analyze the inner loop first: what does one run of it cost?",
         "Each outer iteration does n + 2 constant steps.",
         "n × (n + 2) = n² + 2n."],
        ["Inner loop: n iterations of O(1) → n",
         "One outer iteration: 1 (x = 0) + n + 1 (B[i] = x) = n + 2",
         "Outer loop runs n times: T(n) = n(n + 2) = n² + 2n",
         "Dominant term: n² → Θ(n²)"],
        [("for i = 1 to n", "outer: n"), ("for j = 1 to n", "inner: n"), (["x = 0", "B[i] = x"], "constant extras")]),

    # ------------------------------------------------------------------ Level 3
    ident("c3-nm", 3, "multi_variable", "Two different input sizes", """
        for i = 1 to n
            for j = 1 to m
                print(A[i], B[j])
        """, "nm",
        ["The loops have different bounds. Don't assume m = n.",
         "Outer: n. Inner: m per outer iteration.",
         "Multiply, keeping both variables."],
        ["Outer loop: n iterations",
         "Inner loop: m iterations per outer iteration",
         "Total: n × m = nm",
         "Θ(nm). Writing O(n²) would be wrong unless we know m ≤ n."],
        [("for i = 1 to n", "n"), ("for j = 1 to m", "m per i")], options=MULTI),

    ident("c3-n-plus-m", 3, "multi_variable", "Two independent inputs, sequential", """
        for i = 1 to n
            print(A[i])
        for j = 1 to m
            print(B[j])
        """, "n + m",
        ["Nested or sequential?",
         "Sequential sections add.",
         "Can you drop either term? Only if you know which input is larger."],
        ["Loop over A: n", "Loop over B: m",
         "Sequential → T(n, m) = n + m",
         "Θ(n + m). We cannot simplify further: either n or m might dominate."],
        [("for i = 1 to n", "n"), ("for j = 1 to m", "+ m")], options=MULTI),

    ident("c3-nmk", 3, "multi_variable", "Three different bounds", """
        for i = 1 to n
            for j = 1 to m
                for t = 1 to k
                    total = total + A[i][j] * W[t]
        """, "nmk",
        ["Three nested loops with three different bounds.",
         "Each level multiplies by its own bound.",
         "n × m × k."],
        ["i-loop: n", "j-loop: m per i", "t-loop: k per (i, j)",
         "Total: n × m × k = nmk → Θ(nmk)"],
        [("for i = 1 to n", "n"), ("for j = 1 to m", "× m"), ("for t = 1 to k", "× k")],
        options=["nmk", "n + m + k", "n³", "nm + k", "nm"]),

    ident("c3-nk", 3, "multi_variable", "Comparing each word against k patterns", """
        procedure CountMatches(words, patterns)
            n = length(words)
            k = length(patterns)
            matches = 0
            for i = 0 to n - 1
                for p = 0 to k - 1
                    if words[i] == patterns[p]
                        matches = matches + 1
            return matches
        """, "nk",
        ["Name the sizes: n words and k patterns.",
         "Every word is compared with every pattern.",
         "Assume one comparison is O(1). Multiply."],
        ["Outer loop over words: n", "Inner loop over patterns: k per word",
         "Comparisons: n × k", "T(n, k) ∈ Θ(nk)"],
        [("for i = 0 to n - 1", "n"), ("for p = 0 to k - 1", "k per word")],
        options=["nk", "n + k", "n²", "k", "n"]),

    ident("c3-n-times-m-plus-k", 3, "multi_variable", "One outer loop, two inner loops", """
        for i = 1 to n
            for j = 1 to m
                print(i, j)
            for t = 1 to k
                print(i, t)
        """, "n(m + k)",
        ["Inside the outer loop there are TWO loops. Are they nested in each other?",
         "One outer iteration costs m + k.",
         "Multiply by the outer count n."],
        ["Inner loops run one after another: cost m + k per outer iteration.",
         "Outer loop: n iterations",
         "T = n(m + k) = nm + nk",
         "Θ(n(m + k)). Not nmk: the j and t loops are siblings, not nested."],
        [("for i = 1 to n", "n"), ("for j = 1 to m", "m"), ("for t = 1 to k", "+ k (sibling, not nested)")],
        options=["n(m + k)", "nmk", "n + m + k", "nm", "n²"]),

    ident("c3-nm-plus-n", 3, "multi_variable", "Dropping a dominated term", """
        for i = 1 to n
            for j = 1 to m
                grid[i][j] = 0
        for i = 1 to n
            rowTotal[i] = 0
        """, "nm",
        ["Write the cost of each section.",
         "You get nm + n. Assume m ≥ 1.",
         "Since m ≥ 1, nm ≥ n, so the n term is dominated."],
        ["Section 1: n × m = nm", "Section 2: n",
         "T = nm + n = n(m + 1)",
         "Because m ≥ 1, n ≤ nm, so nm + n ≤ 2nm.",
         "T ∈ Θ(nm): the lone n term is dominated even though m is a separate variable."],
        [("grid[i][j] = 0", "nm"), ("rowTotal[i] = 0", "+ n")],
        options=["nm", "n + m", "n²", "nm²", "m"]),

    count_ex("c3-count-nm", 3, "multi_variable", "Counting with two bounds", """
        count = 0
        for i = 1 to n
            for j = 1 to m
                count = count + 1
        """, "count = count + 1", {"n": 3, "m": 4},
        lambda n, m: n * m,
        ["n + m", "nm", "n²", "m²"], "nm", "nm",
        ["For n = 3 and m = 4, how many (i, j) pairs are there?",
         "Every i is paired with every j.",
         "n × m."],
        ["For n = 3, m = 4: 3 × 4 = 12.", "In general: n × m = nm", "Θ(nm)"],
        [("for i = 1 to n", "n"), ("for j = 1 to m", "m per i")],
        options=["n + m", "nm", "n²", "m", "n"]),

    ident("c3-graph", 3, "multi_variable", "Visiting a graph's adjacency lists", """
        procedure CountEdges(G)
            total = 0
            for each vertex v in G.vertices          // V vertices
                for each neighbor w of v             // deg(v) neighbors
                    total = total + 1
            return total
        """, "V + E",
        ["How many times does the outer loop run? Call it V.",
         "The inner loop's count differs per vertex: deg(v). Sum those over all vertices.",
         "The sum of all degrees is proportional to E, and the outer loop still costs V."],
        ["Outer loop: V iterations (constant work each, even if deg(v) = 0)",
         "Inner loop: deg(v) iterations for vertex v",
         "Total inner work: Σ deg(v) = 2E (undirected) → Θ(E)",
         "T = Θ(V) + Θ(E) = Θ(V + E)",
         "Not V × E: the inner loop does NOT run E times for every vertex."],
        [("for each vertex v", "V"), ("for each neighbor w of v", "deg(v): sums to O(E) total")],
        options=["V + E", "VE", "V²", "E", "E log V"]),

    ident("c3-min-nm", 3, "multi_variable", "Comparing two strings", """
        procedure CommonPrefix(S, T)          // |S| = n, |T| = m
            i = 0
            while i < length(S) and i < length(T) and S[i] == T[i]
                i = i + 1
            return i
        """, "min(n, m)",
        ["What stops the loop? There are three conditions.",
         "In the worst case the characters keep matching. Then which condition stops it first?",
         "The loop can never go past the shorter string."],
        ["The loop stops as soon as i reaches the end of EITHER string (or a mismatch).",
         "Worst case (strings agree as far as possible): min(n, m) iterations.",
         "Best case: first characters differ → 1 iteration.",
         "Worst-case bound: O(min(n, m)), which is also O(n) and O(m) - but min(n, m) is tighter."],
        [("while i < length(S) and i < length(T)", "stops at the shorter length")],
        options=["min(n, m)", "n + m", "nm", "max(n, m)", "1"]),

    analyze("c3-matrix-mult-rect", 3, "multi_variable", "Rectangular matrix multiplication", """
        // A is n × m, B is m × k, C is n × k
        for i = 1 to n
            for j = 1 to k
                C[i][j] = 0
                for t = 1 to m
                    C[i][j] = C[i][j] + A[i][t] * B[t][j]
        """, "nmk",
        ["Find the bound for each loop from the matrix dimensions in the comment.",
         "i ranges over rows of A (n), j over columns of B (k), t over the shared dimension (m).",
         "Multiply all three."],
        ["i-loop: n", "j-loop: k per i", "t-loop: m per (i, j)",
         "C[i][j] = 0 adds nk, which is dominated.",
         "T = nk + nmk ∈ Θ(nmk)"],
        [("for i = 1 to n", "n"), ("for j = 1 to k", "× k"), ("for t = 1 to m", "× m")],
        options=["nmk", "n³", "nk", "n + m + k", "nm + k"]),

    ident("c3-square-bound", 3, "irregular_loops", "Looping up to n²", """
        for i = 1 to n * n
            print(i)
        """, N2,
        ["There's only one loop - but check the bound.",
         "How many iterations when n = 10?",
         "A single loop can be quadratic if its bound is quadratic."],
        ["The loop runs n × n = n² times.",
         "Each iteration is O(1).",
         "T(n) = n² → Θ(n²). The number of loops is not what matters; the number of iterations is."],
        [("for i = 1 to n * n", "n² iterations")]),
]
