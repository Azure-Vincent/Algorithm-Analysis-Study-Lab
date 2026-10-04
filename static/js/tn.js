/* TnRunner - the T(n) Analysis exercise screen (operation table, direct entry, guided derivation). */
(function () {
  "use strict";
  const esc = BT.esc, el = BT.el;

  function md(s) { return esc(s).replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\n/g, "<br>"); }
  function caseLabel(c) { return c === "all" ? "" : c === "best" ? "Best case" : c === "worst" ? "Worst case" : c; }
  function storeGet(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } }
  function storeSet(k, v) { try { sessionStorage.setItem(k, v); } catch (e) { /* storage unavailable */ } }

  function TnRunner(root, opts) {
    this.root = root;
    this.opts = opts || {};
  }

  TnRunner.prototype.show = function (view) {
    this.view = view;
    this.state = { instance: BT.uuid(), hints: 0, attempts: 0, correct: false, revealed: false, mode: view.mode, guidedDone: {} };
    if (this.opts.test && this.state.mode === "guided") this.state.mode = "table";   // guided steps are checked one by one
    this.render();
  };

  // ======================================================================= layout
  TnRunner.prototype.render = function () {
    const v = this.view, self = this;
    this.root.innerHTML = "";
    const box = el("div", { class: "runner tn-runner" });
    this.root.appendChild(box);

    const head = el("div", { class: "ex-head" }, [el("h2", { text: v.title })]);
    if (v.mistake_status) head.insertAdjacentHTML("beforeend", BT.statusBadge(v.mistake_status === "open" ? "missed" : v.mistake_status));
    box.appendChild(head);
    const meta = el("div", { class: "ex-meta" });
    meta.innerHTML = '<span class="badge amber">T(n) Analysis</span><span class="badge">' + esc(v.topic_label) + '</span><span class="badge">' +
      esc(v.level_label) + '</span><span class="badge ' + ({ beginner: "green", intermediate: "amber", advanced: "red" }[v.difficulty] || "") + '">' + esc(v.difficulty) + "</span>";
    box.appendChild(meta);

    const fns = v.cases.map(function (c) { return v.fn[c]; }).join(" and ");
    box.appendChild(el("p", { class: "prompt", html: (v.prompt ? md(v.prompt) + " " : "") + "Derive <b>" + esc(fns) + "</b> for this algorithm under the counting model, then classify it with Θ." }));
    if (v.cases.length > 1) {
      box.appendChild(el("div", { class: "callout amber", html: "<b>Input-dependent.</b> The operation count depends on the data, not only on n, so give a separate function for the best and the worst case." }));
    }

    const grid = el("div", { class: "tn-grid" });
    box.appendChild(grid);
    const left = el("div", { class: "tn-main" });
    const right = el("div", { class: "tn-side" });
    grid.appendChild(left);
    grid.appendChild(right);

    // code + model
    left.appendChild(BT.renderCode(v.code));
    if (v.assumptions) left.appendChild(el("p", { class: "muted", style: "font-size:.88rem;margin-top:-4px", html: "<b>Assume:</b> " + esc(v.assumptions) }));
    const model = el("details", { class: "method" });
    if (v.level <= 2) model.setAttribute("open", "open");
    model.innerHTML = "<summary>Counting model - what counts as one operation</summary>" + modelTable(v.model) +
      '<p class="muted" style="font-size:.85rem;margin:6px 0 2px">A loop <code>for (init; condition; update)</code> whose body runs I times: init 1×, condition I + 1 times (the last check fails), update I times. T(n) counts operations under this model; it is not a count of CPU instructions. <a href="/learn/tn#model" target="_blank">Learn → T(n) analysis</a></p>';
    left.appendChild(model);

    // mode tabs
    const tabs = el("div", { class: "seg tn-tabs" });
    [["table", "Operation table"], ["direct", "Direct"], ["guided", "Guided derivation"]].filter(function (m) {
      return !(self.opts.test && m[0] === "guided");
    }).forEach(function (m) {
      const b = el("button", { type: "button", text: m[1], "data-mode": m[0] });
      b.addEventListener("click", function () { if (!self.state.correct && !self.state.revealed) { self.state.mode = m[0]; self.drawMode(); } });
      tabs.appendChild(b);
    });
    this.tabs = tabs;
    left.appendChild(tabs);
    this.modeBox = el("div", { class: "tn-mode" });
    left.appendChild(this.modeBox);

    this.hintBox = el("div", { class: "hints" });
    left.appendChild(this.hintBox);

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
    left.appendChild(controls);
    this.feedback = el("div", { class: "feedback" });
    left.appendChild(this.feedback);

    // scratch work (kept while you work on this exercise, also across reloads in this tab)
    const key = "bt_scratch_" + v.id;
    right.appendChild(el("div", { class: "plabel", text: "Scratch work" }));
    right.appendChild(el("div", { class: "muted", style: "font-size:.8rem;margin-bottom:6px", text: "Not graded. Kept while you work on this exercise." }));
    const scratch = el("textarea", { class: "scratch tn-scratch", placeholder: "outer = n\ninner = n per outer\nbody = 2 ops\nbody total = 2n²" });
    scratch.value = storeGet(key) || "";
    scratch.addEventListener("input", function () { storeSet(key, scratch.value); });
    right.appendChild(scratch);

    this.inputs = { T: {}, theta: {}, cells: {} };
    this.drawMode();
    this.updateHintBtn();
  };

  function modelTable(rules) {
    let h = '<table class="data tn-model">';
    rules.forEach(function (r) { h += "<tr><td class=mono>" + esc(r[0]) + "</td><td>" + esc(r[1]) + "</td><td class=num><b>" + r[2] + "</b></td></tr>"; });
    return h + "</table>";
  }

  TnRunner.prototype.drawMode = function () {
    const self = this, mode = this.state.mode, v = this.view;
    this.tabs.querySelectorAll("button").forEach(function (b) { b.classList.toggle("on", b.dataset.mode === mode); });
    const saved = this.collect();
    this.modeBox.innerHTML = "";
    this.inputs = { T: {}, theta: {}, cells: {} };
    if (mode === "table") this.drawTable();
    if (mode === "guided") { this.drawGuided(); this.submitBtn.classList.add("hidden"); }
    else this.submitBtn.classList.remove("hidden");
    if (mode !== "guided") this.drawAnswerInputs();
    // carry typed answers across tabs
    Object.keys(saved.T || {}).forEach(function (c) { if (self.inputs.T[c] && saved.T[c]) { self.inputs.T[c].value = saved.T[c]; self.inputs.T[c].dispatchEvent(new Event("input")); } });
    Object.keys(saved.theta || {}).forEach(function (c) { if (self.inputs.theta[c] && saved.theta[c]) self.inputs.theta[c].value = saved.theta[c]; });
  };

  // ---------------------------------------------------------------- operation table
  TnRunner.prototype.drawTable = function () {
    const v = this.view, self = this;
    const blank = v.table_blank;
    const wrap = el("div", { class: "tn-table-wrap" });
    const caseNote = v.cases.length > 1 ? " - " + caseLabel(v.table_case).toLowerCase() : "";
    wrap.appendChild(el("p", { class: "muted", style: "font-size:.88rem;margin:6px 0", html:
      (blank === "cost" ? "Fill in the <b>cost</b> of each row (every row here runs once)." :
        "Fill in how many times each row <b>executes</b>" + esc(caseNote) + ". Use n" + (v.vars.length > 1 ? ", " + v.vars.slice(1).join(", ") : "") + ", +, *, /, ^ and log(n).") }));
    const t = el("table", { class: "trace tn-table" });
    t.innerHTML = "<tr><th>Line</th><th>Row</th><th>Cost</th><th>Executions" + esc(caseNote) + "</th><th>Cost × executions</th></tr>";
    v.rows.forEach(function (r) {
      const tr = el("tr");
      tr.appendChild(el("td", { class: "rowlab", text: String(r.line) }));
      tr.appendChild(el("td", { class: "tn-stmt", html: "<code>" + esc(r.text) + "</code>" + (r.role === "cond" ? ' <span class="faint" style="font-size:.75rem">condition</span>' : r.role === "init" ? ' <span class="faint" style="font-size:.75rem">init</span>' : r.role === "update" ? ' <span class="faint" style="font-size:.75rem">update</span>' : "") }));
      const costTd = el("td");
      let costIn = null, execIn = null;
      if (r.cost === null) {
        costIn = el("input", { type: "text", class: "tn-cell", "aria-label": "cost of " + r.text, placeholder: "?" });
        costTd.appendChild(costIn);
      } else costTd.textContent = String(r.cost);
      tr.appendChild(costTd);
      const execTd = el("td");
      if (blank === "cost") execTd.textContent = "1";
      else {
        execIn = el("input", { type: "text", class: "tn-cell wide", "aria-label": "executions of " + r.text, placeholder: "?" });
        execTd.appendChild(execIn);
      }
      tr.appendChild(execTd);
      const tot = el("td", { class: "mono tn-total" });
      tr.appendChild(tot);
      const upd = function () {
        const c = costIn ? costIn.value.trim() : String(r.cost);
        const e = execIn ? execIn.value.trim() : "1";
        tot.textContent = c && e ? (e === "1" ? c : c === "1" ? e : c + " · (" + e + ")") : "";
      };
      [costIn, execIn].forEach(function (i) { if (i) i.addEventListener("input", upd); });
      upd();
      self.inputs.cells[r.key] = { cost: costIn, exec: execIn, row: r };
      t.appendChild(tr);
    });
    wrap.appendChild(t);
    const build = el("button", { class: "btn small", type: "button", text: "Build T(n) from the table ↓", onclick: function () { self.buildSum(); } });
    wrap.appendChild(el("div", { class: "btn-row", style: "margin-top:6px" }, [build,
      el("span", { class: "muted", style: "font-size:.82rem", text: "Writes Σ cost × executions into the T box - you still simplify it." })]));
    this.modeBox.appendChild(wrap);
  };

  TnRunner.prototype.buildSum = function () {
    const v = this.view, cells = this.inputs.cells, parts = [];
    let missing = false;
    v.rows.forEach(function (r) {
      const c = cells[r.key];
      const cost = c.cost ? c.cost.value.trim() : String(r.cost);
      const exec = c.exec ? c.exec.value.trim() : "1";
      if (!cost || !exec) { missing = true; return; }
      if (cost === "0" || exec === "0") return;
      parts.push(exec === "1" ? cost : cost === "1" ? "(" + exec + ")" : cost + "(" + exec + ")");
    });
    if (missing) { BT.toast("Fill in every cell first."); return; }
    const target = this.inputs.T[v.table_case];
    target.value = parts.join(" + ") || "0";
    target.dispatchEvent(new Event("input"));
    target.focus();
  };

  // ---------------------------------------------------------------- answers (T and Θ, per case)
  TnRunner.prototype.drawAnswerInputs = function () {
    const v = this.view, self = this;
    const wrap = el("div", { class: "tn-answers" });
    v.cases.forEach(function (c) {
      const part = el("div", { class: "part tn-part" });
      if (c !== "all") part.appendChild(el("div", { class: "plabel", text: caseLabel(c) }));
      // Part A
      const rowA = el("div", { class: "tn-answer-row" });
      rowA.appendChild(el("span", { class: "tn-label tn-label-T", text: "A · " + v.fn[c] + " =" }));
      const tIn = el("input", { type: "text", class: "tn-expr", placeholder: "e.g. 4n^2 + 3n + 2", "aria-label": v.fn[c], autocomplete: "off", spellcheck: "false" });
      rowA.appendChild(tIn);
      part.appendChild(rowA);
      const prev = el("div", { class: "tn-preview muted" });
      part.appendChild(prev);
      self.attachPreview(tIn, prev);
      // Part B
      const rowB = el("div", { class: "tn-answer-row" });
      rowB.appendChild(el("span", { class: "tn-label tn-label-theta", text: "B · " + v.fn[c] + " ∈ Θ(" }));
      const thIn = el("input", { type: "text", class: "tn-expr short", placeholder: "n^2", "aria-label": "Theta of " + v.fn[c], autocomplete: "off", spellcheck: "false" });
      rowB.appendChild(thIn);
      rowB.appendChild(el("span", { class: "tn-label tn-label-theta", text: ")" }));
      part.appendChild(rowB);
      [tIn, thIn].forEach(function (i) { i.addEventListener("keydown", function (e) { if (e.key === "Enter") self.submit(); }); });
      self.inputs.T[c] = tIn;
      self.inputs.theta[c] = thIn;
      wrap.appendChild(part);
    });
    wrap.appendChild(el("p", { class: "muted", style: "font-size:.82rem", html: "Type <code>n^2</code> or <code>n²</code>, <code>3n</code>, <code>n(n+1)/2</code>, <code>log(n)</code> (base 2). Any equivalent form is accepted." }));
    this.modeBox.appendChild(wrap);
  };

  TnRunner.prototype.attachPreview = function (input, out) {
    const vars = this.view.vars;
    let timer = null;
    input.addEventListener("input", function () {
      clearTimeout(timer);
      const text = input.value;
      if (!text.trim()) { out.textContent = ""; return; }
      timer = setTimeout(async function () {
        try {
          const r = await BT.api("/api/tn/preview", { text: text, vars: vars });
          if (input.value !== text) return;
          out.innerHTML = r.ok ? "reads as <span class=mono>" + esc(r.pretty) + "</span>" : '<span class="warn-mark">' + esc(r.error) + "</span>";
        } catch (e) { out.textContent = ""; }
      }, 280);
    });
  };

  // ---------------------------------------------------------------- guided derivation
  TnRunner.prototype.drawGuided = function () {
    const v = this.view, self = this;
    const list = el("div", { class: "tn-guided" });
    list.appendChild(el("p", { class: "muted", style: "font-size:.88rem", text: "Work through the derivation one step at a time. Each step unlocks the next." }));
    this.guidedEls = [];
    v.guided.forEach(function (s, i) {
      const box = el("div", { class: "part tn-step" + (i > 0 && !self.state.guidedDone[v.guided[i - 1].id] ? " locked-part" : "") });
      box.appendChild(el("div", { class: "plabel", html: "<span class='faint'>Step " + (i + 1) + ".</span> " + md(s.q) }));
      const row = el("div", { class: "tn-answer-row" });
      if (s.kind === "bound") row.appendChild(el("span", { class: "tn-label tn-label-theta", text: "Θ(" }));
      const inp = el("input", { type: "text", class: "tn-expr" + (s.kind === "bound" ? " short" : ""), autocomplete: "off", spellcheck: "false",
        placeholder: s.allowed.length > v.vars.length ? "may use " + s.allowed.join(", ") : "" });
      row.appendChild(inp);
      if (s.kind === "bound") row.appendChild(el("span", { class: "tn-label tn-label-theta", text: ")" }));
      const chk = el("button", { class: "btn small", type: "button", text: "Check" });
      const show = el("button", { class: "btn small ghost hidden", type: "button", text: "Show this step" });
      row.appendChild(chk);
      row.appendChild(show);
      box.appendChild(row);
      const res = el("div", { class: "inline-result" });
      box.appendChild(res);
      const done = function (r) {
        self.state.guidedDone[s.id] = { value: inp.value, revealed: !!r.revealed };
        inp.disabled = true; chk.disabled = true; show.classList.add("hidden");
        res.innerHTML = (r.revealed ? '<span class="warn-mark">Shown:</span> ' : '<span class="ok-mark">✓</span> ') + '<b class="mono">' + esc(r.expected) + "</b>" +
          (r.explain ? ' <span class="muted">' + md(r.explain) + "</span>" : "");
        const next = self.guidedEls[i + 1];
        if (next) { next.box.classList.remove("locked-part"); next.inp.focus(); }
        else self.finishGuided();
      };
      const check = async function (reveal) {
        if (!reveal && !inp.value.trim()) { BT.toast("Enter an answer first."); return; }
        try {
          const r = await BT.api("/api/exercise/" + v.id + "/tn_step", reveal ? { step: s.id, reveal: true } : { step: s.id, value: inp.value });
          if (r.correct || r.revealed) {
            if (r.revealed) inp.value = r.expected.replace(/^Θ\((.*)\)$/, "$1");
            done(r);
          } else {
            res.innerHTML = '<span class="bad-mark">✗</span> ' + esc(r.error || "Not quite - try again.");
            show.classList.remove("hidden");
          }
        } catch (e) { BT.toast(e.message); }
      };
      chk.addEventListener("click", function () { check(false); });
      show.addEventListener("click", function () { check(true); });
      inp.addEventListener("keydown", function (e) { if (e.key === "Enter") check(false); });
      self.guidedEls.push({ box: box, inp: inp, step: s });
      list.appendChild(box);
    });
    this.modeBox.appendChild(list);
  };

  TnRunner.prototype.finishGuided = function () {
    // the final simplified T and Θ steps become the graded answer
    const v = this.view, ans = { mode: "guided", T: {}, theta: {} };
    let revealed = false;
    this.guidedEls.forEach(function (g) {
      const d = this.state.guidedDone[g.step.id];
      if (d && d.revealed) revealed = true;
      const m = g.step.id.match(/^(\w+)-(simplify|theta)$/);
      if (m) ans[m[2] === "simplify" ? "T" : "theta"][m[1]] = d ? d.value : "";
    }, this);
    this.statusEl.textContent = revealed ? "Some steps were shown, so this counts as missed." : "";
    this.send(ans, revealed);
  };

  // ======================================================================= hints / submit / reveal
  TnRunner.prototype.updateHintBtn = function () {
    const n = this.view.hint_count;
    this.hintBtn.textContent = this.state.hints >= n ? "No more hints" : "Hint " + (this.state.hints + 1) + "/" + n;
    this.hintBtn.disabled = this.state.hints >= n || this.state.correct || this.state.revealed;
  };

  TnRunner.prototype.hint = async function () {
    const n = this.state.hints + 1;
    try {
      const r = await BT.api("/api/exercise/" + this.view.id + "/hint", { n: n });
      this.state.hints = n;
      this.hintBox.appendChild(el("div", { class: "hint", html: "<b>Hint " + n + ".</b> " + md(r.hint) }));
      this.updateHintBtn();
    } catch (e) { BT.toast(e.message); }
  };

  TnRunner.prototype.collect = function () {
    const out = { mode: this.state.mode, T: {}, theta: {}, cells: {} };
    const inp = this.inputs || { T: {}, theta: {}, cells: {} };
    Object.keys(inp.T).forEach(function (c) { out.T[c] = inp.T[c].value; });
    Object.keys(inp.theta).forEach(function (c) { out.theta[c] = inp.theta[c].value; });
    Object.keys(inp.cells).forEach(function (k) {
      const c = inp.cells[k];
      out.cells[k] = {};
      if (c.cost) out.cells[k].cost = c.cost.value;
      if (c.exec) out.cells[k].exec = c.exec.value;
    });
    return out;
  };

  TnRunner.prototype.submit = function () {
    if (this.state.correct || this.state.revealed || this.state.recorded || this.busy) return;
    const ans = this.collect();
    const missing = this.view.cases.some(function (c) { return !(ans.T[c] || "").trim() || !(ans.theta[c] || "").trim(); });
    if (missing) { BT.toast("Fill in both T(n) and Θ" + (this.view.cases.length > 1 ? " for each case" : "") + "."); return; }
    this.send(ans, false);
  };

  TnRunner.prototype.send = async function (ans, revealedSteps) {
    this.busy = true;
    this.submitBtn.disabled = true;
    try {
      const r = await BT.api("/api/exercise/" + this.view.id + "/submit", {
        answer: ans, instance_id: this.state.instance, hints_used: this.state.hints + (revealedSteps ? 1 : 0),
        session_id: this.opts.sessionId || null, context: this.opts.context || "free",
      });
      this.state.attempts = r.attempt_no;
      this.showResult(r);
    } catch (e) { BT.toast("Error: " + e.message); }
    finally { this.busy = false; if (!this.state.correct && !this.state.recorded) this.submitBtn.disabled = false; }
  };

  TnRunner.prototype.reveal = async function () {
    if (this.state.revealed || this.state.correct) return;
    if (!confirm("Show the full derivation? This exercise will count as missed (it's saved to Review Mistakes).")) return;
    try {
      const r = await BT.api("/api/exercise/" + this.view.id + "/reveal", {
        instance_id: this.state.instance, hints_used: this.state.hints, session_id: this.opts.sessionId || null, context: this.opts.context || "free",
      });
      this.state.revealed = true;
      this.lock();
      this.feedback.innerHTML = '<div class="verdict info">Derivation <span class="sub">- this one was added to Review Mistakes.</span></div>';
      this.showSolution(r.solution);
      this.finish();
    } catch (e) { BT.toast(e.message); }
  };

  TnRunner.prototype.lock = function () {
    this.submitBtn.disabled = true;
    this.solBtn.disabled = true;
    this.updateHintBtn();
    this.modeBox.querySelectorAll("input, button").forEach(function (i) { i.disabled = true; });
  };

  TnRunner.prototype.finish = function () {
    if (this.nextBtn) { this.nextBtn.textContent = this.opts.nextDoneLabel || "Next question →"; this.nextBtn.classList.add("primary"); }
    if (this.opts.onFinish) this.opts.onFinish(this.state);
  };

  // ======================================================================= feedback
  TnRunner.prototype.showResult = function (r) {
    const v = this.view, fb = this.feedback, self = this;
    fb.innerHTML = "";
    if (r.recorded) {
      this.state.recorded = true;
      this.statusEl.textContent = "";
      this.lock();
      fb.innerHTML = '<div class="verdict info">Answer recorded <span class="sub">- results and explanations appear when you finish the test.</span></div>';
      this.finish();
      return;
    }
    const extra = (r.attempt_no > 1 ? "attempt " + r.attempt_no : "") + (this.state.hints ? (r.attempt_no > 1 ? " · " : "") + this.state.hints + " hint" + (this.state.hints > 1 ? "s" : "") : "");
    fb.appendChild(el("div", { class: "verdict " + (r.correct ? "ok" : "bad"), html: (r.correct ? "✓ Correct" : "✗ Not yet") + '<span class="sub">' + esc(extra) + "</span>" }));

    // independent part results
    const parts = el("div", { class: "tn-results" });
    v.cases.forEach(function (c) {
      const tr = r.T[c], th = r.theta[c];
      const label = c === "all" ? "" : " (" + c + ")";
      parts.appendChild(partCard("Part A · " + v.fn[c] + label, tr, "tn-T"));
      parts.appendChild(partCard("Part B · Θ" + label, th, "tn-theta"));
    });
    fb.appendChild(parts);

    if (r.mode === "table" && r.cells) {
      let wrong = 0;
      Object.keys(r.cells).forEach(function (k) {
        const cols = r.cells[k], cell = self.inputs.cells[k];
        Object.keys(cols).forEach(function (col) {
          const input = cell && cell[col];
          if (!input) return;
          input.classList.remove("right", "wrong");
          input.classList.add(cols[col].correct ? "right" : "wrong");
          if (!cols[col].correct) wrong++;
        });
      });
      if (wrong) fb.appendChild(el("p", { text: wrong + " table cell" + (wrong > 1 ? "s are" : " is") + " marked in red - fix " + (wrong > 1 ? "them" : "it") + " before submitting again." }));
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

  function partCard(title, res, cls) {
    const card = el("div", { class: "tn-card " + cls + " " + (res.correct ? "ok" : "bad") });
    let h = '<div class="tn-card-title">' + (res.correct ? '<span class="ok-mark">✓</span> ' : '<span class="bad-mark">✗</span> ') + esc(title) + "</div>";
    if (res.given_text) h += '<div class="muted" style="font-size:.85rem">You wrote: <span class="mono">' + esc(res.given_text) + "</span></div>";
    if (res.correct) { if (res.note) h += '<div style="font-size:.88rem">' + esc(res.note) + "</div>"; }
    else h += "<div><b>" + esc(res.headline || "Not quite.") + "</b></div>" + (res.detail ? '<div style="font-size:.9rem">' + esc(res.detail) + "</div>" : "");
    card.innerHTML = h;
    return card;
  }

  TnRunner.prototype.showSolution = function (sol) {
    if (!sol) return;
    const fb = this.feedback;
    Object.keys(sol.cases).forEach(function (c) {
      const s = sol.cases[c];
      const blk = el("div", { class: "fb-block" });
      blk.appendChild(el("h4", { text: "Derivation" + (c === "all" ? "" : " - " + caseLabel(c).toLowerCase()) }));
      if (sol.case_notes && sol.case_notes[c]) blk.appendChild(el("p", { class: "muted", style: "font-size:.9rem", text: sol.case_notes[c] }));
      let h = '<table class="data tn-solution"><tr><th>Line</th><th>Row</th><th class=num>Cost</th><th class=num>Executions</th><th class=num>Total</th></tr>';
      s.table.forEach(function (t) {
        h += "<tr><td class=rowlab>" + t.line + "</td><td><code>" + esc(t.text) + "</code>" + (t.ops.length ? ' <span class="faint" style="font-size:.75rem">' + esc(t.ops.join(" ")) + "</span>" : "") +
          "</td><td class='num mono'>" + t.cost + "</td><td class='num mono'>" + esc(t.exec) + "</td><td class='num mono'>" + esc(t.total) + "</td></tr>";
      });
      blk.insertAdjacentHTML("beforeend", h + "</table>");
      blk.appendChild(el("div", { class: "steps", text: sol.fn[c] + " = " + s.sum + "\n" + sol.fn[c] + " = " + s.T_text }));
      const panels = el("div", { class: "tn-panels" });
      panels.innerHTML =
        '<div class="tn-panel p1"><div class="k">Operation-count model</div><div class="v mono">' + esc(sol.fn[c]) + " = " + esc(s.T_text) + '</div><div class="d">exact under this app\'s counting model</div></div>' +
        '<div class="tn-arrow">→</div><div class="tn-panel p2"><div class="k">Dominant term</div><div class="v mono">' + esc(s.dominant) + '</div><div class="d">fastest-growing term</div></div>' +
        '<div class="tn-arrow">→</div><div class="tn-panel p3"><div class="k">Asymptotic result</div><div class="v mono">Θ(' + esc(s.theta) + ')</div><div class="d">drop the constant</div></div>';
      blk.appendChild(panels);
      fb.appendChild(blk);
    });
    if (sol.note) fb.appendChild(el("div", { class: "callout", text: sol.note }));
  };

  window.TnRunner = TnRunner;
})();
