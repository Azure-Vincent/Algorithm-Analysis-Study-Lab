/* ProofRunner - Time Complexity Proofs: prove/disprove with structured steps (type "proof") and
   proof construction with blanks (type "proof_fill"). Same options as ExerciseRunner (context, sessionId,
   test, onNext, nextLabel, nextDoneLabel, onFinish). */
(function () {
  "use strict";
  const esc = BT.esc, el = BT.el;
  const CONST_LABEL = { c: "c", c1: "c₁", c2: "c₂", n0: "n₀" };

  function md(s) { return esc(s).replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\n/g, "<br>"); }

  function ProofRunner(root, opts) {
    this.root = root;
    this.opts = opts || {};
  }

  ProofRunner.prototype.show = function (view) {
    this.view = view;
    this.state = { instance: BT.uuid(), hints: 0, attempts: 0, correct: false, revealed: false, recorded: false, verdict: null };
    this.render();
  };

  // ======================================================================= layout
  ProofRunner.prototype.render = function () {
    const v = this.view, self = this;
    this.root.innerHTML = "";
    const box = el("div", { class: "runner proof-runner" });
    this.root.appendChild(box);

    const head = el("div", { class: "ex-head" }, [el("h2", { text: v.title })]);
    if (v.mistake_status) head.insertAdjacentHTML("beforeend", BT.statusBadge(v.mistake_status === "open" ? "missed" : v.mistake_status));
    box.appendChild(head);
    const meta = el("div", { class: "ex-meta" });
    meta.innerHTML = '<span class="badge green">Proofs</span><span class="badge">' + esc(v.type_label) + '</span><span class="badge">' +
      esc(v.topic_label) + '</span><span class="badge">' + esc(v.level_label || "Level " + v.level) + '</span><span class="badge ' +
      ({ beginner: "green", intermediate: "amber", advanced: "red" }[v.difficulty] || "") + '">' + esc(v.difficulty) + "</span>";
    box.appendChild(meta);
    if (v.tn_source) {
      box.appendChild(el("p", { class: "muted", style: "font-size:.88rem",
        html: 'From T(n) Analysis: <a href="/exercise/' + encodeURIComponent(v.tn_source) + '?ctx=free">back to the T(n) exercise</a> · Pseudocode → operation counting → T(n) → hypothesis → <b>formal proof</b> → Θ' }));
    }

    const method = el("details", { class: "method" });
    method.innerHTML = "<summary>The proof method</summary><ol>" + v.method.map(function (m) { return "<li>" + esc(m) + "</li>"; }).join("") + "</ol>";
    box.appendChild(method);
    if (v.definition) box.appendChild(el("div", { class: "defn proof-defn", html: "<b>Definition.</b> " + esc(v.definition) }));
    box.appendChild(el("p", { class: "prompt", html: md(v.prompt || "") }));

    this.body = el("div", { class: "ex-body" });
    box.appendChild(this.body);
    this.hintBox = el("div", { class: "hints" });
    box.appendChild(this.hintBox);

    const controls = el("div", { class: "controls" });
    this.hintBtn = el("button", { class: "btn", onclick: function () { self.hint(); } });
    this.submitBtn = el("button", { class: "btn primary", text: "Submit", onclick: function () { self.submit(); } });
    this.solBtn = el("button", { class: "btn ghost", text: "Show solution", onclick: function () { self.reveal(); } });
    if (!this.opts.test) controls.appendChild(this.hintBtn);
    controls.appendChild(this.submitBtn);
    if (!this.opts.test) controls.appendChild(this.solBtn);
    controls.appendChild(el("span", { class: "spacer" }));
    this.statusEl = el("span", { class: "muted", style: "font-size:.88rem" });
    controls.appendChild(this.statusEl);
    if (this.opts.onNext) {
      this.nextBtn = el("button", { class: "btn", text: this.opts.nextLabel || "Skip →", onclick: function () { self.opts.onNext(self.state); } });
      controls.appendChild(this.nextBtn);
    }
    box.appendChild(controls);
    this.feedback = el("div", { class: "feedback" });
    box.appendChild(this.feedback);

    if (v.type === "proof") this.renderProof(); else this.renderFill();
    this.updateHintBtn();
  };

  function thetaDiagram(g) {
    return '<div class="theta-diagram" aria-label="Θ needs both bounds">' +
      '<div class="td-f">f(n)</div>' +
      '<div class="td-row"><div class="td-box lower"><b>Lower bound</b><span>Ω(' + esc(g) + ')</span><small>c₁·g(n) ≤ f(n)</small></div>' +
      '<div class="td-box upper"><b>Upper bound</b><span>O(' + esc(g) + ')</span><small>f(n) ≤ c₂·g(n)</small></div></div>' +
      '<div class="td-theta">both ⇒ <b>Θ(' + esc(g) + ')</b></div></div>';
  }

  ProofRunner.prototype.renderProof = function () {
    const v = this.view, self = this, body = this.body;
    body.appendChild(el("div", { class: "formula", html: "Prove or disprove:&nbsp; <b>" + esc(v.claim) + "</b>" }));
    if (v.rel === "theta") body.insertAdjacentHTML("beforeend", thetaDiagram(v.g_text));

    const explore = el("details", { class: "method" });
    let t = '<summary>Explore numerically - builds intuition, it is <b>not</b> a proof</summary><table class="data proof-table"><tr><th class=num>n</th><th class=num>f(n) = ' +
      esc(v.f_text) + "</th><th class=num>g(n) = " + esc(v.g_text) + "</th><th class=num>f(n) / g(n)</th></tr>";
    v.table.forEach(function (r) { t += "<tr><td class=num>" + r.n + "</td><td class=num>" + esc(r.f) + "</td><td class=num>" + esc(r.g) + "</td><td class=num>" + esc(r.ratio) + "</td></tr>"; });
    explore.innerHTML = t + '</table><p class="muted" style="font-size:.85rem;margin:6px 0 0">A table checks finitely many n. The definition needs the inequality for <b>every</b> n ≥ n₀ - and the ratio column hints at whether a fixed c can exist. Try more values in the <a href="/proofs/sandbox?f=' +
      encodeURIComponent(v.f_src) + "&g=" + encodeURIComponent(v.g_src) + "&rel=" + encodeURIComponent(v.rel) + '" target="_blank">Proof sandbox</a>.</p>';
    body.appendChild(explore);

    // the decision
    const decide = el("div", { class: "part" });
    decide.appendChild(el("div", { class: "plabel", text: "Can this statement be proven?" }));
    const opts = el("div", { class: "opts" });
    [["true", "True - it can be proven"], ["false", "False - no constants can work"]].forEach(function (o) {
      const b = el("div", { class: "opt wide", role: "radio", tabindex: "0", text: o[1] });
      b.dataset.value = o[0];
      const pick = function () {
        if (b.getAttribute("aria-disabled") === "true") return;
        opts.querySelectorAll(".opt").forEach(function (x) { x.classList.remove("sel"); });
        b.classList.add("sel");
        self.state.verdict = o[0];
        self.trueBox.classList.toggle("hidden", o[0] !== "true");
        self.falseBox.classList.toggle("hidden", o[0] !== "false");
      };
      b.addEventListener("click", pick);
      b.addEventListener("keydown", function (e) { if (e.key === " " || e.key === "Enter") { e.preventDefault(); pick(); } });
      opts.appendChild(b);
    });
    decide.appendChild(opts);
    body.appendChild(decide);
    this.verdictOpts = opts;

    // true: the four steps
    this.inputs = {};
    const tb = el("div", { class: "proof-steps hidden" });
    tb.appendChild(this.step("inequality", "Step 1 - Write the required inequality",
      "e.g. " + v.required + " (you can write f(n), g(n), c" + (v.rel === "theta" ? "1, c2" : "") + ", <=)", "input"));
    v.constants.filter(function (k) { return k !== "n0"; }).forEach(function (k, i) {
      tb.appendChild(self.step(k, "Step 2" + (v.constants.length > 2 ? String.fromCharCode(97 + i) : "") + " - Choose " + CONST_LABEL[k],
        CONST_LABEL[k] + " = (any valid positive value - not necessarily the smallest)", "const"));
    });
    tb.appendChild(this.step("n0", "Step 3 - Choose n₀", "n₀ = (the inequality must hold for EVERY n ≥ n₀)", "const"));
    tb.appendChild(this.step("explanation", "Step 4 - Explain why the inequality holds for every n ≥ n₀",
      "e.g. For n ≥ 1, … ≤ … ≤ …, so …", "text"));
    body.appendChild(tb);
    this.trueBox = tb;

    const fb = el("div", { class: "proof-steps hidden" });
    fb.appendChild(this.step("why_false", "Explain why no fixed c can make the required inequality hold for all sufficiently large n",
      "e.g. f(n)/g(n) = … grows without bound, so f(n) ≤ c·g(n) fails once n > …, whatever c is.", "text"));
    body.appendChild(fb);
    this.falseBox = fb;
  };

  ProofRunner.prototype.step = function (key, label, placeholder, kind) {
    const wrap = el("div", { class: "proof-step", "data-step": key });
    const id = "pf-" + key + "-" + this.state.instance.slice(0, 6);
    wrap.appendChild(el("label", { class: "plabel", for: id, html: esc(label) + ' <span class="step-mark"></span>' }));
    let input;
    if (kind === "text") input = el("textarea", { id: id, class: "scratch", rows: "3", placeholder: placeholder.replace(/<[^>]+>/g, "") });
    else input = el("input", { id: id, type: "text", class: kind === "const" ? "number-input" : "proof-ineq", placeholder: placeholder.replace(/<[^>]+>/g, ""),
                                autocomplete: "off", spellcheck: "false" });
    wrap.appendChild(input);
    this.inputs[key] = input;
    return wrap;
  };

  ProofRunner.prototype.renderFill = function () {
    const v = this.view, self = this;
    this.body.appendChild(el("div", { class: "formula", html: "<b>" + esc(v.claim) + "</b>" }));
    const wrap = el("div", { class: "proof-fill" });
    this.blanks = [];
    v.template.split("\n").forEach(function (line) {
      const row = el("div", { class: "pf-line" });
      line.split(/\[\[(\d+)\]\]/).forEach(function (bit, k) {
        if (k % 2 === 0) { row.appendChild(document.createTextNode(bit)); return; }
        const inp = el("input", { type: "text", size: "6", class: "pf-blank", "aria-label": "blank " + (+bit + 1), placeholder: "?", autocomplete: "off" });
        inp.addEventListener("keydown", function (e) { if (e.key === "Enter") self.submit(); });
        self.blanks[+bit] = inp;
        row.appendChild(inp);
      });
      wrap.appendChild(row);
    });
    this.body.appendChild(wrap);
  };

  // ======================================================================= hints / submit
  ProofRunner.prototype.updateHintBtn = function () {
    const n = this.view.hint_count;
    this.hintBtn.textContent = this.state.hints >= n ? "No more hints" : "Hint " + (this.state.hints + 1) + "/" + n;
    this.hintBtn.disabled = this.state.hints >= n || this.state.correct || this.state.revealed;
  };

  ProofRunner.prototype.hint = async function () {
    const n = this.state.hints + 1;
    try {
      const r = await BT.api("/api/exercise/" + this.view.id + "/hint", { n: n });
      this.state.hints = n;
      this.hintBox.appendChild(el("div", { class: "hint", html: "<b>Hint " + n + ".</b> " + md(r.hint) }));
      this.updateHintBtn();
    } catch (e) { BT.toast(e.message); }
  };

  ProofRunner.prototype.collect = function () {
    const v = this.view, self = this;
    if (v.type === "proof_fill") return { blanks: this.blanks.map(function (i) { return i.value; }) };
    const a = { verdict: this.state.verdict };
    if (this.state.verdict === "true") {
      a.inequality = this.inputs.inequality.value;
      v.constants.forEach(function (k) { a[k] = self.inputs[k].value; });
      a.explanation = this.inputs.explanation.value;
    } else if (this.state.verdict === "false") {
      a.explanation = this.inputs.why_false.value;
    }
    return a;
  };

  ProofRunner.prototype.validate = function (a) {
    const v = this.view;
    if (v.type === "proof_fill") return a.blanks.some(function (b) { return !String(b || "").trim(); }) ? "Fill in every blank." : null;
    if (!a.verdict) return "First decide whether the statement can be proven (True / False).";
    if (a.verdict === "true") {
      if (!a.inequality.trim()) return "Step 1: write the inequality the definition requires.";
      for (const k of v.constants) if (!String(a[k] || "").trim()) return "Choose a value for " + CONST_LABEL[k] + ".";
      if (!a.explanation.trim()) return "Step 4: explain why the inequality holds for every n ≥ n₀.";
    } else if (!a.explanation.trim()) return "Explain why no fixed c can work.";
    return null;
  };

  ProofRunner.prototype.submit = async function () {
    if (this.state.correct || this.state.revealed || this.state.recorded || this.busy) return;
    const a = this.collect();
    const problem = this.validate(a);
    if (problem) { BT.toast(problem); return; }
    this.busy = true;
    this.submitBtn.disabled = true;
    try {
      const r = await BT.api("/api/exercise/" + this.view.id + "/submit", {
        answer: a, instance_id: this.state.instance, hints_used: this.state.hints,
        session_id: this.opts.sessionId || null, context: this.opts.context || "free",
      });
      this.state.attempts = r.attempt_no;
      this.showResult(r);
    } catch (e) { BT.toast("Error: " + e.message); }
    finally { this.busy = false; if (!this.state.correct && !this.state.recorded) this.submitBtn.disabled = false; }
  };

  ProofRunner.prototype.reveal = async function () {
    if (this.state.revealed || this.state.correct) return;
    if (!confirm("Show the worked proof? This exercise will count as missed (it's saved to Review Mistakes).")) return;
    try {
      const r = await BT.api("/api/exercise/" + this.view.id + "/reveal", {
        instance_id: this.state.instance, hints_used: this.state.hints, session_id: this.opts.sessionId || null, context: this.opts.context || "free",
      });
      this.state.revealed = true;
      this.lock();
      this.feedback.innerHTML = '<div class="verdict info">Worked proof <span class="sub">- this one was added to Review Mistakes.</span></div>';
      this.showSolution(r.solution);
      this.finish();
    } catch (e) { BT.toast(e.message); }
  };

  ProofRunner.prototype.lock = function () {
    this.submitBtn.disabled = true;
    this.solBtn.disabled = true;
    this.updateHintBtn();
    this.body.querySelectorAll("input, textarea").forEach(function (i) { i.disabled = true; });
    this.body.querySelectorAll(".opt").forEach(function (o) { o.setAttribute("aria-disabled", "true"); });
  };

  ProofRunner.prototype.finish = function () {
    if (this.nextBtn) { this.nextBtn.textContent = this.opts.nextDoneLabel || "Next question →"; this.nextBtn.classList.add("primary"); }
    if (this.opts.onFinish) this.opts.onFinish(this.state);
  };

  // ======================================================================= feedback
  ProofRunner.prototype.showResult = function (r) {
    const fb = this.feedback, self = this;
    fb.innerHTML = "";
    if (r.recorded) {
      this.state.recorded = true;
      this.lock();
      fb.innerHTML = '<div class="verdict info">Answer recorded <span class="sub">- results and explanations appear when you finish the test.</span></div>';
      this.finish();
      return;
    }
    const extra = (r.attempt_no > 1 ? "attempt " + r.attempt_no : "") + (this.state.hints ? (r.attempt_no > 1 ? " · " : "") + this.state.hints + " hint" + (this.state.hints > 1 ? "s" : "") : "");
    fb.appendChild(el("div", { class: "verdict " + (r.correct ? "ok" : "bad"), html: (r.correct ? "✓ Correct" : "✗ Not yet") + '<span class="sub">' + esc(extra) + "</span>" }));
    if (r.messages && r.messages.length) {
      const ul = el("ul", { class: "proof-msgs" });
      r.messages.forEach(function (m) { ul.appendChild(el("li", { text: m })); });
      fb.appendChild(el("div", { class: "fb-block " + (r.correct ? "" : "proof-wrong") }, [ul]));
    }
    if (this.view.type === "proof") {
      const mark = function (key, ok) {
        const st = self.body.querySelector('.proof-step[data-step="' + key + '"] .step-mark');
        if (st) st.innerHTML = ok === null || ok === undefined ? "" : (ok ? '<span class="ok-mark">✓</span>' : '<span class="bad-mark">✗</span>');
      };
      self.body.querySelectorAll(".step-mark").forEach(function (m) { m.innerHTML = ""; });
      Object.keys(r.steps || {}).forEach(function (k) {
        const st = r.steps[k];
        if (k === "inequality") mark("inequality", st.correct);
        else if (k === "explanation") { mark("explanation", st.correct); mark("why_false", st.correct); }
        else if (k === "constants") {
          self.view.constants.forEach(function (key) {
            mark(key, key === "n0" ? ("n0_ok" in st ? st.n0_ok : st.correct) : ("c_ok" in st ? st.c_ok : st.correct));
          });
        }
      });
    } else if (r.blanks) {
      r.blanks.forEach(function (b) { const i = self.blanks[b.index]; i.classList.remove("right", "wrong"); i.classList.add(b.correct ? "right" : "wrong"); });
    }
    if (r.correct) {
      this.state.correct = true;
      this.statusEl.textContent = "";
      this.lock();
      this.showSolution(r.solution);
      this.finish();
    } else {
      this.statusEl.textContent = "Fix it and submit again, or use a hint.";
      this.submitBtn.textContent = "Submit again";
    }
  };

  /** Worked proof, revealed one step at a time. Intuition and the limit argument are labelled separately. */
  ProofRunner.prototype.showSolution = function (sol) {
    if (!sol) return;
    const fb = this.feedback, v = this.view;
    const blk = el("div", { class: "fb-block" });
    if (v.type === "proof_fill" && sol.filled) {
      blk.appendChild(el("h4", { text: "Completed proof" }));
      blk.appendChild(el("pre", { class: "plain proof-text", text: sol.filled }));
    }
    if (v.type === "proof") {
      blk.appendChild(el("h4", { text: sol.truth ? "Worked proof (from the definition)" : "Why the claim is false" }));
      if (sol.truth && sol.constants) {
        blk.appendChild(el("p", { class: "muted", style: "font-size:.88rem", text: "One valid choice: " + Object.keys(sol.constants).map(function (k) { return CONST_LABEL[k] + " = " + sol.constants[k]; }).join(", ") +
          ". Any other constants that satisfy the definition are just as valid - nobody needs the smallest ones." }));
      }
    }
    const steps = sol.steps || [];
    const ol = el("ol", { class: "worked" });
    steps.forEach(function (s, i) { ol.appendChild(el("li", { text: s, class: i === 0 ? "" : "hidden" })); });
    blk.appendChild(ol);
    if (steps.length > 1) {
      const row = el("div", { class: "btn-row" });
      let shown = 1;
      const nextBtn = el("button", { class: "btn small", text: "Show next step", onclick: function () {
        if (shown < steps.length) ol.children[shown++].classList.remove("hidden");
        if (shown >= steps.length) row.remove();
      } });
      row.appendChild(nextBtn);
      row.appendChild(el("button", { class: "btn small ghost", text: "Show all", onclick: function () {
        Array.from(ol.children).forEach(function (li) { li.classList.remove("hidden"); }); row.remove();
      } }));
      blk.appendChild(row);
    }
    if (sol.intuition) blk.appendChild(el("div", { class: "callout", html: "<b>Intuition (not a proof):</b> " + esc(sol.intuition) }));
    if (sol.limit) blk.appendChild(el("div", { class: "callout", html: "<b>Limit argument (a separate, rigorous route):</b> " + esc(sol.limit) }));
    if (sol.note) blk.appendChild(el("div", { class: "callout green", text: sol.note }));
    fb.appendChild(blk);
  };

  window.ProofRunner = ProofRunner;
})();
