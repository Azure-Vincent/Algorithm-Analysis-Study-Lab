"""Browser walkthrough of the T(n) Analysis workflow (plus a smoke check of the other tracks).

Starts `python app.py` on a throwaway database, drives it in Chromium with Playwright,
restarts the server and checks that everything persisted.

    pip install playwright        # Chromium must be available
    python tests/e2e_browser.py
    E2E_EXE=dist/AlgorithmStudy python tests/e2e_browser.py     # same walkthrough against the packaged app
"""
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from playwright.sync_api import sync_playwright  # noqa: E402

from data import seed_exercises  # noqa: E402

TN = {e["title"]: e for e in seed_exercises() if e["track"] == "tn"}
results, errors = [], []


def check(cond, msg):
    results.append(("PASS " if cond else "FAIL ") + msg)
    print(results[-1], flush=True)
    if not cond:
        errors.append(msg)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def start_server(db_path, port):
    env = dict(os.environ, BIGO_DB=db_path, PORT=str(port), APP_ENV="development")
    exe = os.environ.get("E2E_EXE")
    cmd = [os.path.abspath(exe), "--no-browser", "--port", str(port)] if exe else [sys.executable, "app.py"]
    proc = subprocess.Popen(cmd, cwd=ROOT if not exe else tempfile.gettempdir(), env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=1)
            return proc
        except Exception:
            time.sleep(0.2)
    proc.kill()
    raise RuntimeError("server did not start")


def theta_input(theta):
    """Turn the display form (n², log n, n log n) into something typed."""
    t = theta.replace("²", "^2").replace("³", "^3").replace("log n", "log(n)")
    return re.sub(r"(\S)\s+(log)", r"\1*\2", t)


def current_exercise(page):
    title = page.inner_text(".tn-runner .ex-head h2").strip()
    return TN[title]


def fill_table_and_answer(page, ex):
    """Operation-table mode: fill every blank cell, build T(n) from the table, give Θ, submit."""
    page.click(".tn-tabs button[data-mode=table]")
    case = "worst" if "worst" in ex["cases"] else ex["cases"][0]
    table = {r["key"]: r for r in ex["solution"][case]["table"]}
    rows = page.locator(".tn-table tr")
    for i, row in enumerate(ex["rows"]):
        tr = rows.nth(i + 1)
        inputs = tr.locator("input.tn-cell")
        if inputs.count() == 2:
            inputs.nth(0).fill(str(table[row["key"]]["cost"]))
            inputs.nth(1).fill(table[row["key"]]["exec"])
        elif inputs.count() == 1:
            is_cost = "cost" in (inputs.nth(0).get_attribute("aria-label") or "")
            inputs.nth(0).fill(str(table[row["key"]]["cost"]) if is_cost else table[row["key"]]["exec"])
    page.click("button:has-text('Build T(n) from the table')")
    for c in ex["cases"]:
        idx = ex["cases"].index(c)
        t_box = page.locator(".tn-answers input.tn-expr:not(.short)").nth(idx)
        if c != case:
            t_box.fill(ex["solution"][c]["T"])
        page.locator(".tn-answers input.tn-expr.short").nth(idx).fill(theta_input(ex["solution"][c]["theta"]))
    page.wait_for_timeout(400)
    page.click(".tn-runner button:has-text('Submit')")
    page.wait_for_selector(".tn-runner .verdict")


with tempfile.TemporaryDirectory() as tmp:
    db_path = os.path.join(tmp, "e2e.db")
    port = free_port()
    BASE = f"http://127.0.0.1:{port}"
    server = start_server(db_path, port)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={"width": 1366, "height": 900})
            page = ctx.new_page()
            page.on("pageerror", lambda e: errors.append(f"JS error: {e}"))
            page.on("dialog", lambda d: d.accept())

            # 1. open the app - straight to the dashboard, no sign-in
            page.goto(BASE + "/")
            check("/login" not in page.url and "Dashboard" in page.title() + page.inner_text("nav"), "app opens straight to the dashboard")
            check("T(n) Analysis" in page.inner_text("main"), "dashboard shows the T(n) Analysis track")

            # 2. navigate to T(n) Analysis
            check(page.locator(".topnav .navlinks a").count() == 5, "header shows only the five basic tabs")
            page.click(".topnav >> text=Practice")
            page.click(".subnav >> text=T(n) Analysis")
            page.wait_for_selector(".ex-item")
            check(page.url.endswith("/tn") and page.locator(".ex-item").count() >= 50, "T(n) section lists 50+ exercises")
            page.click("text=How T(n) works")
            check("/learn/tn" in page.url and page.locator(".topnav a.active").inner_text() == "Learn",
                  "T(n) learning material lives under Learn")
            check("not a stopwatch" in page.inner_text("main") and "4n + 4" in page.inner_text("main"), "reference page with worked examples")
            page.go_back()

            # 3. beginner practice session in operation-table mode
            check(page.locator("#qp .qp-start").is_enabled(), "T(n) page offers in-place practice")
            page.click("#qp .seg[data-key=count] button[data-v='5']")
            page.click("text=Practice: beginner")
            check(page.url.endswith("/tn") and page.locator("#browse").is_hidden(), "beginner session starts in place on the T(n) page")
            for i in range(5):
                page.wait_for_selector(".tn-runner")
                ex = current_exercise(page)
                check(ex["difficulty"] == "beginner", f"Q{i + 1} is a beginner T(n) exercise ({ex['id']})")
                if i == 0:
                    scratch = page.locator(".tn-scratch")
                    scratch.fill("outer runs n times\nbody costs 2")
                    page.click(".tn-tabs button[data-mode=direct]")
                    page.click(".tn-tabs button[data-mode=table]")
                    check(scratch.input_value() == "outer runs n times\nbody costs 2", "scratch work is preserved while switching modes")
                fill_table_and_answer(page, ex)
                fb = page.inner_text(".feedback")
                check("Correct" in page.inner_text(".verdict") and "Part A" in fb and "Part B" in fb,
                      f"Q{i + 1}: table-built T(n) and Θ accepted with part feedback")
                check(page.locator(".tn-panel.p1").count() >= 1 and "dominant term" in fb.lower() and "asymptotic result" in fb.lower(),
                      f"Q{i + 1}: T(n) → dominant term → Θ panels shown")
                page.locator(".controls .btn", has_text="→").last.click()
                if i < 4:
                    page.wait_for_function("() => !document.querySelector('.tn-runner .verdict')")
            page.wait_for_selector("text=Session report")
            check("correct answers" in page.inner_text("#session").lower(), "beginner session finished with a report")

            # 4. nested problem: hint, wrong T(n), targeted feedback, correction
            page.goto(BASE + "/tn")
            page.wait_for_selector(".ex-item")
            page.select_option("#f-level", "4")
            page.click(".ex-item:has-text('Count all pairs')")
            page.wait_for_selector(".tn-runner")
            ex = current_exercise(page)
            check(ex["topic"] == "tn_nested", f"opened a nested-loop exercise ({ex['id']})")
            page.click(".tn-tabs button[data-mode=direct]")
            page.click(".tn-runner button:has-text('Hint 1/')")
            page.wait_for_selector(".hint")
            check("Hint 1." in page.inner_text(".hints") and ex["solution"]["all"]["T_text"] not in page.inner_text(".hints"),
                  "first hint shown without revealing T(n)")
            # inner loop counted only once in total
            page.fill(".tn-answers input.tn-expr:not(.short)", "4n+4")
            page.wait_for_selector(".tn-preview:has-text('reads as')")
            page.fill(".tn-answers input.tn-expr.short", "n^2")
            page.click(".tn-runner button:has-text('Submit')")
            page.wait_for_selector(".verdict.bad")
            fb = page.inner_text(".feedback")
            check("Not yet" in fb and "inner loop" in fb.lower(), "wrong T(n) gets inner-loop-specific feedback")
            check(page.locator(".tn-card.tn-T.bad").count() == 1 and page.locator(".tn-card.tn-theta.ok").count() == 1,
                  "T(n) marked wrong while Θ is marked right (graded separately)")
            check(ex["solution"]["all"]["T_text"] not in fb, "full T(n) not revealed after a wrong answer")
            page.fill(".tn-answers input.tn-expr:not(.short)", "4n^2 + 4n + 4")
            page.click(".tn-runner button:has-text('Submit again')")
            page.wait_for_selector(".verdict.ok")
            check("attempt 2" in page.inner_text(".verdict"), "corrected answer accepted on attempt 2")

            # 5. statistics
            page.goto(BASE + "/tn")
            stats = page.inner_text("main")
            check("correct t(n)" in stats.lower() and "Nested loops" in stats,
                  "T(n) page shows statistics by topic")
            page.goto(BASE + "/progress")
            prog = page.inner_text("#tn-progress")
            check("t(n) first try" in prog.lower() and "θ first try" in prog.lower() and "Nested loops" in prog, "progress page shows separate T(n)/Θ accuracy")

            # 6. review mistakes: details and retry
            page.goto(BASE + "/review")
            page.select_option("#f-track", "tn")
            page.wait_for_selector(".mistake")
            page.locator(".mistake summary").first.click()
            body = page.inner_text(".mistake .body")
            check("Mistake category" in body and "4n + 4" in body.replace("4n+4", "4n + 4") and "4n² + 4n + 4" in body,
                  "mistake shows category, given and expected T(n)")
            page.click("button:has-text('Retry now')")
            page.wait_for_selector(".modal .tn-runner")
            page.click(".modal .tn-tabs button[data-mode=direct]")
            page.fill(".modal .tn-answers input.tn-expr:not(.short)", "4n(n+1) + 4")
            page.fill(".modal .tn-answers input.tn-expr.short", "n^2")
            page.click(".modal .tn-runner button:has-text('Submit')")
            page.wait_for_selector(".modal .verdict.ok")
            check(True, "retry from Review Mistakes accepted an equivalent form")
            page.click(".modal button:has-text('Close')")

            # 7. other tracks still work
            page.goto(BASE + "/exercise/c2-nested-two")
            page.wait_for_selector(".runner .controls")
            check(True, "complexity exercise still loads")
            page.goto(BASE + "/exercise/pw-count-even")
            page.wait_for_selector(".editor textarea")
            check(True, "pseudocode exercise still loads")
            page.goto(BASE + "/visualizer")
            check("n!" in page.inner_text("#ops"), "visualizer works")

            # 7b. time complexity proofs: c / n₀ feedback, worked proof, sandbox, T(n) → proof
            page.goto(BASE + "/exercise/pf-o-n3-2n")
            page.wait_for_selector(".proof-runner")
            page.click(".opt:has-text('True - it can be proven')")
            page.fill(".proof-step[data-step=inequality] input", "n^3 <= c * 2^n")
            page.fill(".proof-step[data-step=c] input", "1")
            page.fill(".proof-step[data-step=n0] input", "1")
            page.fill(".proof-step[data-step=explanation] textarea", "for n >= 10, n^3 <= 2^n by induction")
            page.click(".proof-runner button:has-text('Submit')")
            page.wait_for_selector(".verdict.bad")
            check("fails at n = 2" in page.inner_text(".feedback") and "larger n₀" in page.inner_text(".feedback"),
                  "proof: n₀ too small is explained with a counterexample")
            page.fill(".proof-step[data-step=n0] input", "10")
            page.click(".proof-runner button:has-text('Submit again')")
            page.wait_for_selector(".verdict.ok")
            page.click("button:has-text('Show all')")
            fb = page.inner_text(".feedback")
            check("Choose c = 1 and n₀ = 10" in fb and "not a proof" in fb.lower() and "limit argument" in fb.lower(),
                  "proof accepted; worked proof separates intuition and the limit argument")
            page.goto(BASE + "/proofs/sandbox?f=n^2&g=n&rel=O")
            page.wait_for_selector("#sb-table table")
            page.fill("#sb-c", "10")
            page.click("#sb-check")
            page.wait_for_selector("#sb-check-out .callout")
            check("n = 11" in page.inner_text("#sb-check-out") and "not a mathematical proof" in page.inner_text("main"),
                  "sandbox shows the first counterexample and that testing is not proof")
            page.goto(BASE + "/exercise/tn2-sum")
            page.wait_for_selector(".tn-runner")
            page.click(".tn-runner button:has-text('Show solution')")
            page.click("button:has-text('Prove its complexity')")
            page.wait_for_selector(".theta-diagram")
            check("pf-tn-tn2-sum" in page.url, "T(n) exercise leads to a Θ proof of its T(n)")

            # 7c. mock exam: balanced, navigable, answers kept, graded by category after submission
            page.goto(BASE + "/mock")
            page.click("#mock-count button[data-v='4']")
            page.click("#mock-start")
            page.wait_for_selector(".mock-q")
            check(page.locator(".mock-nav-btn").count() == 4 and "Question 1 of 4" in page.inner_text(".mock-q"),
                  "mock exam generated with the chosen number of questions")
            page.locator(".mock-q textarea.scratch").first.fill("for n > 1: each term <= coefficient * n^2")
            page.click("button:has-text('Flag for review')")
            page.click("button:has-text('Next →')")
            page.click("button:has-text('← Previous')")
            check("each term" in page.locator(".mock-q textarea.scratch").first.input_value() and
                  page.locator(".mock-nav-btn.flagged").count() == 1, "mock exam keeps work and flags while navigating")
            check("Model solution" not in page.inner_text("main"), "no answers shown while the exam is active")
            page.click(".mock-nav button:has-text('Submit exam')")
            page.wait_for_selector(".mock-big", timeout=60000)
            res = page.inner_text("main")
            check(all(c in res for c in ("Asymptotic Analysis", "Pseudocode Analysis", "Algorithm Design", "Discrete Mathematics"))
                  and "Model solution" in res, "mock exam results by category with model solutions")
            browser.close()

        # 8. restart the server: progress persists
        server.terminate()
        server.wait(10)
        server = start_server(db_path, port)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(BASE + "/progress")
            prog = page.inner_text("#tn-progress")
            check("Nested loops" in prog and page.locator(".sess-link").count() >= 1, "after restart: T(n) stats and sessions persisted")
            page.goto(BASE + "/review")
            page.select_option("#f-status", "all")
            page.select_option("#f-track", "tn")
            page.wait_for_selector(".mistake")
            check("improving" in page.inner_text("#list").lower() or "mastered" in page.inner_text("#list").lower(),
                  "after restart: mistake and its retry status persisted")
            browser.close()
    finally:
        server.terminate()

print("\n".join(errors) if errors else f"\nALL {len(results)} CHECKS PASSED")
sys.exit(1 if errors else 0)
