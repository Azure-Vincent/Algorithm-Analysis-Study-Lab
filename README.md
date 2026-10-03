# Big-O Trainer

A local study app for algorithm analysis with three tracks: **Complexity** (Big O, Big Θ, Big Ω),
**T(n) Analysis** (exact operation-count functions), and a **Pseudocode Lab**.
Flask backend, vanilla HTML/CSS/JS frontend, SQLite. It runs only on your own computer: there is no sign-in,
no hosting and no external API or CDN.

## Install and run

Requires Python 3.10+.

**macOS / Linux**
```bash
cd bigo-trainer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

**Windows (PowerShell)**
```powershell
cd bigo-trainer
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**. The app opens straight to the dashboard. On first launch the database
(`instance/trainer.db`) is created and seeded automatically. Progress from earlier versions (including the version
with accounts) is kept: it all belongs to the single local profile.
Use another port with `PORT=5050 python app.py` (PowerShell: `$env:PORT=5050; python app.py`).
The server listens on 127.0.0.1 only, so other machines on your network can't reach it.

### Desktop app (AlgorithmStudy.exe)

The app can also run as a desktop program, without typing any commands. Double-click **AlgorithmStudy.exe**:
it starts the app on a local server (Waitress, bound to 127.0.0.1 only), waits until it's ready, and opens
your default browser. A small window shows the address. Keep it open while you study, and close it (or press
Ctrl+C) to quit. Starting it again while it's already running just opens the browser on the running copy.

**Get the .exe:** download it from the repository's **Releases** page (built automatically by GitHub
Actions for every `v*` tag), or build it yourself:
```powershell
git clone https://github.com/YOUR-USERNAME/bigo-trainer.git
cd bigo-trainer
build.bat
```
`build.bat` creates `.venv` if needed, installs `requirements-build.txt` if anything is missing, removes the old
`build\` and `dist\` folders, runs PyInstaller with `AlgorithmStudy.spec`, and prints where the result is:
**`dist\AlgorithmStudy.exe`** (a single file you can copy anywhere). On macOS/Linux, `./build.sh` builds `dist/AlgorithmStudy`.
Windows may show "Windows protected your PC" the first time, because the .exe isn't code-signed: click
*More info → Run anyway*.

**Where the desktop app keeps your progress:** `%LOCALAPPDATA%\AlgorithmStudy\trainer.db`
(macOS: `~/Library/Application Support/AlgorithmStudy/`, Linux: `~/.local/share/AlgorithmStudy/`).
It's outside the executable, so closing, updating or rebuilding the app never resets it. Running from source
(`python app.py`) keeps using `instance/trainer.db`. To carry progress over, copy that file to the folder above
(with the app closed). Options: `AlgorithmStudy.exe --port 5050`, `--data-dir D:\Study`, or set `BIGO_DB`.

To try the desktop behaviour from source: `pip install -r requirements.txt` then `python launcher.py`.
Check a build with `python tests/smoke_exe.py dist\AlgorithmStudy.exe` (starts it, exercises pages, grading and
the pseudocode sandbox, checks it only listens on 127.0.0.1, restarts it and confirms progress persisted).

### Tests
```bash
python -m unittest discover -s tests -v      # 76 tests: content, parser security, grading, API, stats, persistence
pip install playwright                         # optional: browser walkthrough (needs Chromium)
python tests/e2e_browser.py                    # starts its own server on a temporary database
E2E_EXE=dist/AlgorithmStudy python tests/e2e_browser.py   # same walkthrough against a built executable
```
The browser script walks the whole T(n) workflow: open the app → T(n) Analysis → beginner session in
operation-table mode → T(n) and Θ → nested-loop problem with a hint → wrong T(n) with targeted feedback →
correction → session report → statistics → Review Mistakes retry → server restart → progress still there.

## What's inside

| Area | Contents |
|---|---|
| Complexity Practice | 108 exercises across 6 levels. Modes: identify, O/Θ/Ω bounds, analyze, count operations, compare algorithms, best/average/worst case |
| **T(n) Analysis** | 67 exercises across 9 levels (constant → single loops → sequential → nested → dependent/summations → logarithmic → n, m, k → best/worst case → common algorithms). Operation-table, direct and guided modes; T(n) and Θ graded separately; reference page |
| Pseudocode Lab | 52 exercises (fill in, order, complete, write, pseudocode → complexity) plus 16 tracing and 17 debugging exercises |
| Practice sessions | 5 / 10 / 20 / unlimited; difficulty; topic (including "T(n) derivation"). Report with accuracy, hints, attempts, difficult topics |
| Adaptive practice | Weights topics, including T(n) topics, by smoothed first-try accuracy |
| Review Mistakes | Every miss with your answer, the correct answer, the explanation, attempts, hints and history; T(n) misses also store the mistake category. 3 clean retries → mastered |
| Learn / Visualizer / Compare / Generator | Reference with worked examples; growth-rate charts; algorithm comparison; question generator |

## T(n) Analysis

**Counting model** (shown on every exercise and on the reference page, `/tn/reference`):
assignment 1 · each arithmetic operator 1 · each comparison 1 · each logical operator 1 · `i++` 1 ·
return 1 + its expression · call 1 + its arguments · reading a variable, a constant or `A[i]` 0.
A loop whose body runs I times costs: init once, condition **I + 1** times (the last check fails), update I times.
T(n) is the count under this model. It is not a claim about the exact number of CPU instructions.

- **Operation table**: fill in each row's executions (or its cost), build Σ cost × executions, then simplify.
- **Direct**: type T(n) and Θ. Any equivalent form is accepted: `3n+4`, `4+3n` and `n+n+n+4` all match, and `n(n+1)/2` matches `(n^2+n)/2`.
- **Guided**: one step at a time (loop iterations → condition checks → body cost → total → combine → simplify → Θ). A step's answer is only shown when you get it right or ask for it.
- **Feedback** names the specific slip, for example a missing final loop check, an inner loop counted once in total, loop control left out, n and m merged, a missing log factor, O/Ω used instead of Θ, or Θ written in the T(n) box.
- **Hints** are progressive, and none of them reveals the complete T(n).
- **Scratch area** next to each exercise keeps your notes while you work, including across mode switches and reloads.
- **Results** show T(n) → dominant term → Θ as three separate panels, with the full derivation table.
- **Progress** tracks T(n) and Θ separately: first-try accuracy by topic and difficulty, eventual correctness, hints and attempts.

**Expression input is never evaluated.** `engine/tnmath.py` is a hand-written tokenizer and recursive-descent parser
that builds SymPy objects directly. It accepts only numbers, `n`/`m`/`k`, `+ - * / ^` (or `**`), parentheses,
implicit multiplication, `log(...)` (base 2), `²`/`³` and a `Θ/O/Ω(...)` wrapper. It doesn't use `eval`, `exec`,
`sympify` or `parse_expr`, and it limits length, tokens, nesting, exponents, digits and expanded degree.
The tests feed it injection attempts (`__import__`, attribute access, lambdas, f-strings, …) and oversized inputs.

Every expected T(n) in the bank is checked by a simulator that runs the algorithm and counts operations at several
input sizes, including the best and worst cases (`python -c "from data.tn_bank import SPECS; from engine import tn; print([tn.verify(s) for s in SPECS])"`).

## Project layout
```
app.py              Flask app factory, pages, JSON API, error handling, security headers
launcher.py         desktop launcher: Waitress on 127.0.0.1, opens the browser, per-user data folder
AlgorithmStudy.spec PyInstaller build recipe; build.bat / build.sh run it
requirements-build.txt  build-only dependencies (PyInstaller) on top of requirements.txt
.github/workflows/  builds and smoke-tests the Windows .exe, attaches it to Releases
profile.py          the single local profile; API writes must be JSON
config.py           settings from environment variables (.env.example)
db.py               SQLite schema, migrations, seeding, queries
engine/
  tn.py             T(n) model: op counting, derivation, simulator, grading, guided steps, feedback
  tnmath.py         safe expression parser, equivalence, simplification check, dominant term / Θ
  pseudo.py         pseudocode interpreter        sandbox.py  isolated runner for student code
  grading.py        grading for complexity and pseudocode exercises
  generator.py      challenge generator            stats.py   statistics, sessions, adaptive selection
  growth.py, catalog.py
data/               exercise banks (tn_bank.py holds the T(n) exercises)
templates/          Jinja pages (tn_browse.html, tn_reference.html, …)
static/css, static/js   styles; runner.js, tn.js (T(n) screen), session.js, …
tests/              test_app.py, test_tn.py, e2e_browser.py, smoke_exe.py
```

Your data lives in `instance/trainer.db`. Back it up by copying the file, or delete it to start over.
