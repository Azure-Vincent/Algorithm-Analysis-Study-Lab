/* ExerciseRunner - renders any exercise type, handles hints, submission, feedback, and solutions. */
(function () {
  "use strict";
  const esc = BT.esc, el = BT.el;

  function md(s) {
    return esc(s).replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\n/g, "<br>");
  }
  function wrapOpt(wrap, o) { return wrap && !/^No single/.test(o) ? wrap + "(" + o + ")" : o; }

  function Runner(root, opts) {
    this.root = root;
    this.opts = opts || {};
  }

  Runner.prototype.load = async function (id) {
    this.root.innerHTML = '<div class="runner"><p class="muted">Loading…</p></div>';
    try {
      this.view = await BT.api("/api/exercise/" + encodeURIComponent(id));
    } catch (e) {
      this.root.innerHTML = '<div class="runner"><div class="callout red">Could not load exercise: ' + esc(e.message) + "</div></div>";
      return;
    }
    if (this.view.type === "tn") {                 // T(n) Analysis exercises have their own screen (tn.js)
      new TnRunner(this.root, this.opts).show(this.view);
      return;
    }
    this.state = { instance: BT.uuid(), hints: 0, attempts: 0, locked: false, correct: false, revealed: false,
                   stage: 0, parts: {}, line: null, order: null };
    this.render();
  };

  // ======================================================================= layout
  Runner.prototype.render = function () {
    const v = this.view, self = this;
    this.root.innerHTML = "";
    const box = el("div", { class: "runner" });
    this.root.appendChild(box);

    const head = el("div", { class: "ex-head" }, [el("h2", { text: v.title })]);
    if (v.mistake_status) head.insertAdjacentHTML("beforeend", BT.statusBadge(v.mistake_status === "open" ? "missed" : v.mistake_status));
    box.appendChild(head);
    const meta = el("div", { class: "ex-meta" });
    meta.innerHTML =
      '<span class="badge ' + (v.track === "complexity" ? "blue" : "purple") + '">' + (v.track === "complexity" ? "Complexity" : "Pseudocode") + "</span>" +
      '<span class="badge">' + esc(v.type_label) + "</span>" +
      '<span class="badge">' + esc(v.topic_label) + "</span>" +
      '<span class="badge">' + esc(v.level_label || ("Level " + v.level)) + "</span>" +
      '<span class="badge ' + ({ beginner: "green", intermediate: "amber", advanced: "red" }[v.difficulty] || "") + '">' + esc(v.difficulty) + "</span>";
    box.appendChild(meta);

    const method = el("details", { class: "method" });
    method.innerHTML = "<summary>" + (v.track === "complexity" || v.type === "to_complexity" ? "The analysis method" : "The pseudocode method") +
      "</summary><ol>" + v.method.map(function (m) { return "<li>" + esc(m) + "</li>"; }).join("") + "</ol>";
    box.appendChild(method);

    box.appendChild(el("p", { class: "prompt", html: md(v.prompt || "") }));
    this.body = el("div", { class: "ex-body" });
    box.appendChild(this.body);
    this.hintBox = el("div", { class: "hints" });
    box.appendChild(this.hintBox);

    const controls = el("div", { class: "controls" });
    this.hintBtn = el("button", { class: "btn", onclick: function () { self.hint(); } });
    this.submitBtn = el("button", { class: "btn primary", text: "Submit", onclick: function () { self.submit(); } });
    this.solBtn = el("button", { class: "btn ghost", text: "Show solution", onclick: function () { self.reveal(); } });
    controls.appendChild(this.hintBtn);
    controls.appendChild(this.submitBtn);
    controls.appendChild(this.solBtn);
    if (this.hasEditor()) {
      this.resetBtn = el("button", { class: "btn ghost", text: "Reset", onclick: function () { if (self.editor) self.editor.reset(); } });
      controls.appendChild(this.resetBtn);
    }
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

    const t = v.type;
    if (v.track === "complexity" || t === "to_complexity") this.renderParts();
    else if (t === "fill") this.renderFill();
    else if (t === "order") this.renderOrder();
    else if (t === "complete") this.renderComplete();
    else if (t === "write") this.renderWrite();
    else if (t === "debug") this.renderDebug();
    else if (t === "trace") this.renderTrace();
    this.updateHintBtn();
  };

  Runner.prototype.hasEditor = function () {
    return ["complete", "write", "debug"].indexOf(this.view.type) >= 0;
  };

  Runner.prototype.updateHintBtn = function () {
    const n = this.view.hint_count;
    this.hintBtn.textContent = this.state.hints >= n ? "No more hints" : "Hint " + (this.state.hints + 1) + "/" + n;
    this.hintBtn.disabled = this.state.hints >= n || this.state.locked;
  };

  Runner.prototype.hint = async function () {
    const n = this.state.hints + 1;
    try {
      const r = await BT.api("/api/exercise/" + this.view.id + "/hint", { n: n });
      this.state.hints = n;
      this.hintBox.appendChild(el("div", { class: "hint", html: "<b>Hint " + n + ".</b> " + md(r.hint) }));
      this.updateHintBtn();
    } catch (e) { BT.toast(e.message); }
  };

  // ======================================================================= complexity parts
  Runner.prototype.renderParts = function () {
    const v = this.view, self = this, body = this.body;
    if (v.type === "to_complexity") {
      body.appendChild(el("p", { class: "muted", html: "Source exercise: <b>" + esc(v.source_title || v.source) + "</b>" }));
      if (v.my_solution) {
        const d = el("details", { class: "method" });
        d.innerHTML = "<summary>Your accepted solution (" + esc(v.my_solution.created_at.replace("T", " ")) + ")</summary>";
        d.appendChild(BT.renderCode(v.my_solution.code));
        d.appendChild(el("p", { class: "muted", text: "The question below is about the reference version. Does yours have the same structure (same loops)? If not, analyze both!" }));
        body.appendChild(d);
      }
    }
    if (v.formula) body.appendChild(el("div", { class: "formula", text: v.formula }));
    this.codeHolder = el("div");
    if (v.code) this.codeHolder.appendChild(BT.renderCode(v.code));
    body.appendChild(this.codeHolder);
    if (v.algos) this.renderEstimator(body, v.algos);
    if (v.scratch) {
      body.appendChild(el("div", { class: "muted", style: "font-size:.88rem;margin-top:8px", text: "Scratch area (optional, not graded) - e.g. outer loop = n, inner loop = n, n × n = n²" }));
      this.scratch = el("textarea", { class: "scratch", placeholder: "outer loop = ...\ninner loop = ...\nT(n) = ..." });
      body.appendChild(this.scratch);
    }
    this.partEls = {};
    v.parts.forEach(function (p, i) {
      const box = el("div", { class: "part" });
      box.appendChild(el("div", { class: "plabel", html: md(p.label) }));
      const inputs = el("div");
      box.appendChild(inputs);
      self.renderPartInput(p, inputs);
      const inline = el("div", { class: "inline-result" });
      box.appendChild(inline);
      if (v.staged && i < v.parts.length - 1) {
        const chk = el("button", { class: "btn small", text: "Check this step →", style: "margin-top:10px",
          onclick: function () { self.checkStage(p, i, chk); } });
        box.appendChild(chk);
      }
      if (v.staged && i > 0) box.classList.add("locked-part");
      self.partEls[p.id] = { box: box, inputs: inputs, inline: inline };
      body.appendChild(box);
    });
    if (v.staged) this.submitBtn.disabled = true;
  };

  Runner.prototype.renderPartInput = function (p, holder) {
    const st = this.state;
    if (p.kind === "choice" || p.kind === "multi") {
      const wide = !p.wrap && p.options.some(function (o) { return o.length > 18; });
      const opts = el("div", { class: "opts" + (wide ? " stack" : "") });
      p.options.forEach(function (o) {
        const b = el("div", { class: "opt" + (wide ? " wide" : ""), role: p.kind === "choice" ? "radio" : "checkbox", tabindex: "0", text: wrapOpt(p.wrap, o) });
        b.dataset.value = o;
        const pick = function () {
          if (b.getAttribute("aria-disabled") === "true") return;
          if (p.kind === "choice") {
            opts.querySelectorAll(".opt").forEach(function (x) { x.classList.remove("sel"); });
            b.classList.add("sel");
            st.parts[p.id] = o;
          } else {
            b.classList.toggle("sel");
            const cur = new Set(st.parts[p.id] || []);
            if (b.classList.contains("sel")) cur.add(o); else cur.delete(o);
            st.parts[p.id] = p.options.filter(function (x) { return cur.has(x); });
          }
        };
        b.addEventListener("click", pick);
        b.addEventListener("keydown", function (e) { if (e.key === " " || e.key === "Enter") { e.preventDefault(); pick(); } });
        opts.appendChild(b);
      });
      holder.appendChild(opts);
      if (p.kind === "multi") st.parts[p.id] = [];
    } else if (p.kind === "number") {
      const inp = el("input", { type: "text", class: "number-input", placeholder: "number", inputmode: "numeric" });
      inp.addEventListener("input", function () { st.parts[p.id] = inp.value; });
      holder.appendChild(inp);
    } else if (p.kind === "order") {
      st.parts[p.id] = p.options.slice();
      const self = this;
      const list = new OrderList(holder, p.options.map(function (o) { return { id: o, text: o, indent: 0 }; }), function (items) {
        st.parts[p.id] = items.map(function (x) { return x.id; });
      });
      this.orderLists = this.orderLists || {};
      this.orderLists[p.id] = list;
    }
  };

  Runner.prototype.lockPart = function (pid) {
    const pe = this.partEls[pid];
    pe.inputs.querySelectorAll(".opt").forEach(function (o) { o.setAttribute("aria-disabled", "true"); });
    pe.inputs.querySelectorAll("input").forEach(function (i) { i.disabled = true; });
    if (this.orderLists && this.orderLists[pid]) this.orderLists[pid].lock();
    pe.box.querySelectorAll("button").forEach(function (b) { b.disabled = true; });
  };

  Runner.prototype.checkStage = async function (p, i, btn) {
    const val = this.state.parts[p.id];
    if (val === undefined || val === "" || (Array.isArray(val) && !val.length && p.kind !== "multi")) { BT.toast("Answer this step first."); return; }
    try {
      const r = await BT.api("/api/exercise/" + this.view.id + "/check_part", { part: p.id, value: val });
      this.markPart(p, r);
      this.lockPart(p.id);
      const pe = this.partEls[p.id];
      pe.inline.innerHTML = (r.correct ? '<span class="ok-mark">✓ Correct.</span> ' : '<span class="bad-mark">✗ Not quite.</span> The answer is <b class="mono">' + esc(r.expected) + "</b>.") +
        (r.why ? ' <span class="muted">' + esc(r.why) + "</span>" : "") + (r.correct ? "" : " Carry that value into the next step.");
      this.state.stage = i + 1;
      const next = this.view.parts[i + 1];
      if (next) this.partEls[next.id].box.classList.remove("locked-part");
      if (i + 1 === this.view.parts.length - 1) this.submitBtn.disabled = false;
    } catch (e) { BT.toast(e.message); }
  };

  Runner.prototype.markPart = function (p, r) {
    const pe = this.partEls[p.id];
    if (!pe) return;
    if (p.kind === "choice") {
      pe.inputs.querySelectorAll(".opt").forEach(function (o) {
        const val = o.dataset.value;
        const exp = r.expected;
        const isAns = wrapOpt(p.wrap, val) === exp || val === exp;
        if (isAns) o.classList.add("right");
        else if (o.classList.contains("sel")) o.classList.add("wrong");
      });
    } else if (p.kind === "multi" && r.details) {
      const byOpt = {};
      r.details.forEach(function (d) { byOpt[d.option] = d; });
      pe.inputs.querySelectorAll(".opt").forEach(function (o) {
        const d = byOpt[wrapOpt(p.wrap, o.dataset.value)];
        if (!d) return;
        o.classList.remove("sel");
        if (d.selected && d.valid) o.classList.add("right");
        else if (d.selected && !d.valid) o.classList.add("wrong");
        else if (!d.selected && d.valid) o.classList.add("missed");
      });
    } else if (p.kind === "number") {
      const inp = pe.inputs.querySelector("input");
      inp.style.borderColor = r.correct ? "var(--green)" : "var(--red)";
    } else if (p.kind === "order" && this.orderLists[p.id]) {
      this.orderLists[p.id].markAgainst(this.view.parts.find(function (x) { return x.id === p.id; }), r);
    }
  };

  Runner.prototype.renderEstimator = function (body, algos) {
    const wrap = el("div", { class: "part" });
    wrap.innerHTML = '<div class="plabel">Estimate operation counts</div><div class="range-row"><label class="field">Values of n (comma separated)' +
      '<input type="text" value="10, 100, 1000" class="est-n" style="width:240px"></label></div><div class="est-table"></div>' +
      '<div class="chart-wrap" style="margin-top:10px"><canvas class="chart" style="height:240px"></canvas></div>' +
      '<div class="range-row" style="margin-top:6px"><span class="muted">Chart range: n from 1 to</span><input type="range" min="5" max="200" value="60" class="est-range"><span class="est-max mono">60</span></div>';
    body.appendChild(wrap);
    const inp = wrap.querySelector(".est-n"), tbl = wrap.querySelector(".est-table"), cv = wrap.querySelector("canvas");
    const rng = wrap.querySelector(".est-range"), mx = wrap.querySelector(".est-max");
    const colors = ["#6ea8fe", "#e6b450", "#4fc48b", "#b48cf2"];
    function l10(a, n) { const f = Growth.BY_KEY[a.cls]; return f.log10(n) + Math.log10(a.coef || 1); }
    function update() {
      const ns = inp.value.split(/[,\s]+/).map(Number).filter(function (x) { return x >= 1 && x <= 1e7; }).slice(0, 8);
      let h = '<table class="data"><tr><th>n</th>' + algos.map(function (a) { return "<th class=num>" + esc(a.label) + ": " + esc(a.formula) + "</th>"; }).join("") + "<th>Fewer operations</th></tr>";
      ns.forEach(function (n) {
        const vals = algos.map(function (a) { return l10(a, n); });
        let best = 0; vals.forEach(function (x, i) { if (x < vals[best]) best = i; });
        const tie = vals.every(function (x) { return Math.abs(x - vals[0]) < 1e-9; });
        h += "<tr><td class=mono>" + n.toLocaleString() + "</td>" + vals.map(function (x) { return "<td class='num mono'>" + Growth.fmtBig(x) + "</td>"; }).join("") +
          "<td>" + (tie ? "tie" : esc(algos[best].label)) + "</td></tr>";
      });
      tbl.innerHTML = h + "</table>";
      const N = +rng.value; mx.textContent = N;
      Growth.drawChart(cv, algos.map(function (a, i) {
        return { label: a.label, color: colors[i % 4], fn: function (x) { return Math.pow(10, l10(a, x)); } };
      }), { xmin: 1, xmax: N, logY: false });
    }
    inp.addEventListener("input", update);
    rng.addEventListener("input", update);
    setTimeout(update, 0);
  };

  // ======================================================================= fill
  Runner.prototype.renderFill = function () {
    const v = this.view;
    const wrap = el("div", { class: "code fillcode" });
    this.blanks = [];
    const self = this;
    v.template.split("\n").forEach(function (line, i) {
      const row = el("div", { class: "row" });
      row.appendChild(el("div", { class: "ln", text: String(i + 1) }));
      const src = el("div", { class: "src" });
      const bits = line.split(/\[\[(\d+)\]\]/);
      bits.forEach(function (b, k) {
        if (k % 2 === 0) { src.insertAdjacentHTML("beforeend", BT.highlight(b)); return; }
        const inp = el("input", { type: "text", size: "14", "aria-label": "blank " + (+b + 1), placeholder: "blank " + (+b + 1) });
        inp.addEventListener("keydown", function (e) { if (e.key === "Enter") self.submit(); });
        self.blanks[+b] = inp;
        src.appendChild(inp);
      });
      row.appendChild(src);
      row.appendChild(el("div", { class: "ann" }));
      wrap.appendChild(row);
    });
    this.body.appendChild(wrap);
  };

  // ======================================================================= order
  function OrderList(holder, items, onChange) {
    this.items = items.slice();
    this.onChange = onChange;
    this.showIndent = true;
    this.ul = el("ul", { class: "order-list" });
    holder.appendChild(this.ul);
    this.locked = false;
    this.draw();
  }
  OrderList.prototype.draw = function () {
    const self = this;
    this.ul.innerHTML = "";
    this.items.forEach(function (it, i) {
      const li = el("li", { draggable: self.locked ? "false" : "true" });
      li.dataset.idx = i;
      li.appendChild(el("span", { class: "pos", text: String(i + 1) }));
      li.appendChild(el("span", { class: "handle", text: "⋮⋮", title: "drag" }));
      const txt = el("span", { class: "txt", html: (self.showIndent ? "&nbsp;".repeat(4 * (it.indent || 0)) : "") + BT.highlight(it.text) });
      li.appendChild(txt);
      if (!self.locked) {
        const mv = el("span", { class: "mv" });
        mv.appendChild(el("button", { type: "button", text: "↑", title: "move up", onclick: function () { self.move(i, i - 1); } }));
        mv.appendChild(el("button", { type: "button", text: "↓", title: "move down", onclick: function () { self.move(i, i + 1); } }));
        li.appendChild(mv);
        li.addEventListener("dragstart", function (e) { self.dragFrom = i; li.classList.add("dragging"); e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", String(i)); });
        li.addEventListener("dragend", function () { li.classList.remove("dragging"); });
        li.addEventListener("dragover", function (e) { e.preventDefault(); li.classList.add("drop-target"); });
        li.addEventListener("dragleave", function () { li.classList.remove("drop-target"); });
        li.addEventListener("drop", function (e) { e.preventDefault(); li.classList.remove("drop-target"); if (self.dragFrom !== undefined) self.move(self.dragFrom, i); });
      }
      if (it.mark) li.classList.add(it.mark);
      self.ul.appendChild(li);
    });
  };
  OrderList.prototype.move = function (a, b) {
    if (b < 0 || b >= this.items.length || a === b) return;
    const it = this.items.splice(a, 1)[0];
    this.items.splice(b, 0, it);
    this.items.forEach(function (x) { delete x.mark; });
    this.draw();
    if (this.onChange) this.onChange(this.items);
  };
  OrderList.prototype.lock = function () { this.locked = true; this.draw(); };
  OrderList.prototype.markAgainst = function (part, r) {
    const ans = r.expected.split(" < ");
    this.items.forEach(function (it, i) { it.mark = ans[i] === it.id ? "right" : "wrong"; });
    this.draw();
  };
  window.OrderList = OrderList;

  Runner.prototype.renderOrder = function () {
    const self = this;
    const bar = el("div", { class: "btn-row", style: "margin:4px 0" });
    const cb = el("input", { type: "checkbox", id: "indent-" + this.state.instance, checked: "checked" });
    bar.appendChild(el("label", { class: "muted", style: "font-size:.88rem;display:flex;gap:6px;align-items:center" }, [cb, "Show indentation (a structural hint)"]));
    this.body.appendChild(bar);
    const holder = el("div");
    this.body.appendChild(holder);
    this.orderList = new OrderList(holder, this.view.items.map(function (x) { return { id: x.id, text: x.text, indent: x.indent }; }), null);
    cb.addEventListener("change", function () { self.orderList.showIndent = cb.checked; self.orderList.draw(); });
  };

  // ======================================================================= code-writing types
  Runner.prototype.renderComplete = function () {
    const v = this.view;
    this.body.appendChild(el("div", { class: "muted", style: "font-size:.85rem", text: "Given:" }));
    this.body.appendChild(BT.renderCode(v.header, { extraClass: "readonly-code" }));
    this.body.appendChild(el("div", { class: "editor-bar", html: "Your code - it replaces the <code>// Complete this section</code> line. Indent relative to your own first line. <span class='kbd'>Tab</span> indents." }));
    const ed = el("div");
    this.body.appendChild(ed);
    this.editor = new PseudoEditor(ed, { value: "", minLines: 6, placeholder: "for i = 0 to length(numbers) - 1\n    ...", focus: false });
    if (v.footer) {
      this.body.appendChild(el("div", { class: "muted", style: "font-size:.85rem", text: "…followed by:" }));
      this.body.appendChild(BT.renderCode(v.footer, { extraClass: "readonly-code" }));
    }
  };

  Runner.prototype.renderWrite = function () {
    this.body.appendChild(el("div", { class: "editor-bar", html: "Write your pseudocode below. Arrays are 0-indexed; <code>for i = 0 to n - 1</code> is inclusive. <span class='kbd'>Tab</span> / <span class='kbd'>Shift+Tab</span> indent, <span class='kbd'>Enter</span> auto-indents. Graded by running tests plus a structure check - variable names and minor syntax differences are fine." }));
    const ed = el("div");
    this.body.appendChild(ed);
    this.editor = new PseudoEditor(ed, { value: this.view.starter || "", minLines: 12 });
  };

  Runner.prototype.renderDebug = function () {
    const self = this, v = this.view;
    this.body.appendChild(el("div", { class: "plabel", html: "<b>Step 1.</b> Click the line that contains the bug." }));
    this.lineCode = BT.renderCode(v.code, { clickable: true, onLineClick: function (n) { self.state.line = n; self.lineInfo.textContent = "Selected line " + n; } });
    this.body.appendChild(this.lineCode);
    this.lineInfo = el("div", { class: "muted", style: "font-size:.88rem", text: "No line selected yet." });
    this.body.appendChild(this.lineInfo);
    this.body.appendChild(el("div", { class: "plabel", style: "margin-top:14px", html: "<b>Step 2.</b> Fix the code. Your fix is tested on several inputs." }));
    const ed = el("div");
    this.body.appendChild(ed);
    this.editor = new PseudoEditor(ed, { value: v.code, minLines: 6 });
  };

  Runner.prototype.renderTrace = function () {
    const v = this.view;
    const rc = {}; rc[v.snap_line] = "snap";
    this.body.appendChild(BT.renderCode(v.code, { rowClass: rc }));
    const inputs = Object.keys(v.inputs).map(function (k) { return "<code>" + esc(k) + " = " + esc(v.inputs[k]) + "</code>"; }).join(" &nbsp; ");
    this.body.appendChild(el("p", { html: "Input: " + inputs + '<br><span class="muted" style="font-size:.88rem">Highlighted line: ' +
      (v.snap_kind === "loop" ? "write the values at the END of each iteration of this loop." : "write the values each time this line finishes.") + "</span>" }));
    const t = el("table", { class: "trace" });
    let h = "<tr><th>" + (v.snap_kind === "loop" ? "Iteration" : "Row") + "</th>" + v.watch.map(function (w) { return "<th>" + esc(w) + "</th>"; }).join("") + "</tr>";
    for (let r = 0; r < v.row_count; r++) {
      h += "<tr><td class=rowlab>" + (r + 1) + "</td>" + v.watch.map(function (w, c) {
        return '<td><input type="text" data-r="' + r + '" data-c="' + c + '" aria-label="' + esc(w) + " row " + (r + 1) + '"></td>';
      }).join("") + "</tr>";
    }
    t.innerHTML = h;
    this.body.appendChild(t);
    this.traceTable = t;
    t.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      const inputs = Array.from(t.querySelectorAll("input"));
      const i = inputs.indexOf(e.target);
      if (i >= 0 && i + 1 < inputs.length) { e.preventDefault(); inputs[i + 1].focus(); }
    });
  };

  // ======================================================================= submit
  Runner.prototype.collect = function () {
    const v = this.view, t = v.type;
    if (v.track === "complexity" || t === "to_complexity") return { parts: this.state.parts, scratch: this.scratch ? this.scratch.value : "" };
    if (t === "fill") return { blanks: this.blanks.map(function (i) { return i.value; }) };
    if (t === "order") return { order: this.orderList.items.map(function (x) { return x.id; }) };
    if (t === "complete" || t === "write") return { code: this.editor.getValue() };
    if (t === "debug") return { line: this.state.line, code: this.editor.getValue() };
    if (t === "trace") {
      const rows = [];
      this.traceTable.querySelectorAll("input").forEach(function (i) {
        const r = +i.dataset.r, c = +i.dataset.c;
        rows[r] = rows[r] || [];
        rows[r][c] = i.value;
      });
      return { rows: rows };
    }
    return {};
  };

  Runner.prototype.validate = function (ans) {
    const v = this.view;
    if (v.parts) {
      for (const p of v.parts) {
        const val = ans.parts[p.id];
        if (p.kind === "choice" && !val) return "Choose an answer for: " + p.label;
        if (p.kind === "number" && (val === undefined || String(val).trim() === "")) return "Enter a number for: " + p.label;
      }
    }
    if ((v.type === "write" || v.type === "complete") && !ans.code.trim()) return "Write some pseudocode first.";
    if (v.type === "debug" && ans.line == null) return "Click the line with the bug first (step 1).";
    return null;
  };

  Runner.prototype.submit = async function () {
    if (this.state.locked || this.busy) return;
    const ans = this.collect();
    const problem = this.validate(ans);
    if (problem) { BT.toast(problem); return; }
    this.busy = true;
    this.submitBtn.disabled = true;
    try {
      const r = await BT.api("/api/exercise/" + this.view.id + "/submit", {
        answer: ans, instance_id: this.state.instance, hints_used: this.state.hints,
        session_id: this.opts.sessionId || null, context: this.opts.context || "free",
      });
      this.state.attempts = r.attempt_no;
      this.state.correct = r.correct;
      this.showResult(r);
    } catch (e) {
      BT.toast("Error: " + e.message);
    } finally {
      this.busy = false;
      if (!this.state.locked) this.submitBtn.disabled = false;
    }
  };

  Runner.prototype.reveal = async function () {
    if (this.state.revealed) return;
    if (!this.state.locked && !confirm("Show the full solution? This question will count as missed (it's saved to Review Mistakes).")) return;
    try {
      const r = await BT.api("/api/exercise/" + this.view.id + "/reveal", {
        instance_id: this.state.instance, hints_used: this.state.hints, session_id: this.opts.sessionId || null,
        context: this.opts.context || "free", answer_text: this.state.attempts ? "" : "",
      });
      this.state.revealed = true;
      this.lock();
      if (!this.state.correct && !this.state.attempts) {
        this.feedback.innerHTML = '<div class="verdict info">Solution <span class="sub">- this one was added to Review Mistakes.</span></div>';
      }
      this.showSolution(r.solution);
      this.finish();
    } catch (e) { BT.toast(e.message); }
  };

  Runner.prototype.lock = function () {
    this.state.locked = true;
    this.submitBtn.disabled = true;
    this.hintBtn.disabled = true;
    this.solBtn.disabled = true;
    if (this.editor) this.editor.setReadOnly(true);
    this.root.querySelectorAll(".opt").forEach(function (o) { o.setAttribute("aria-disabled", "true"); });
    this.root.querySelectorAll(".ex-body input, .ex-body textarea:not(.scratch)").forEach(function (i) { i.disabled = true; });
    if (this.orderList) this.orderList.lock();
    const ol = this.orderLists || {};
    Object.keys(ol).forEach(function (k) { ol[k].lock(); });
    if (this.resetBtn) this.resetBtn.disabled = true;
  };

  Runner.prototype.finish = function () {
    if (this.nextBtn) { this.nextBtn.textContent = this.opts.nextDoneLabel || "Next question →"; this.nextBtn.classList.add("primary"); this.nextBtn.focus(); }
    if (this.opts.onFinish) this.opts.onFinish(this.state);
  };

  Runner.prototype.showResult = function (r) {
    const v = this.view, t = v.type, fb = this.feedback;
    fb.innerHTML = "";
    const attempts = r.attempt_no > 1 ? " (attempt " + r.attempt_no + ")" : "";
    const hintsTxt = this.state.hints ? " · " + this.state.hints + " hint" + (this.state.hints > 1 ? "s" : "") + " used" : "";
    fb.appendChild(el("div", { class: "verdict " + (r.correct ? "ok" : "bad"),
      html: (r.correct ? "✓ Correct" : "✗ Not quite") + '<span class="sub">' + esc(attempts + hintsTxt) + (r.mistake_status && r.mistake_status !== "open" && r.correct ? " · review status: " + esc(r.mistake_status) : "") + "</span>" }));
    if (r.note) fb.appendChild(el("div", { class: "callout green", text: r.note }));

    if (v.track === "complexity" || t === "to_complexity") this.feedbackParts(r);
    else if (t === "fill") this.feedbackFill(r);
    else if (t === "order") this.feedbackOrder(r);
    else if (t === "complete" || t === "write") this.feedbackCode(r);
    else if (t === "debug") this.feedbackDebug(r);
    else if (t === "trace") this.feedbackTrace(r);

    if (r.locked) {
      this.lock();
      if (r.solution) this.showSolution(r.solution);
      this.finish();
    } else {
      this.statusEl.textContent = "Fix it and submit again, or use a hint.";
      this.submitBtn.textContent = "Submit again";
    }
  };

  Runner.prototype.feedbackParts = function (r) {
    const self = this, fb = this.feedback;
    const byId = {};
    r.parts.forEach(function (p) { byId[p.id] = p; });
    this.view.parts.forEach(function (p) { self.markPart(p, byId[p.id]); });
    if (r.parts.length > 1) {
      let h = '<table class="data"><tr><th></th><th>Part</th><th>Your answer</th><th>Correct answer</th></tr>';
      r.parts.forEach(function (p) {
        h += "<tr><td>" + (p.correct ? '<span class="ok-mark">✓</span>' : '<span class="bad-mark">✗</span>') + "</td><td>" + md(p.label) +
          "</td><td class=mono>" + esc(p.given) + "</td><td class=mono>" + esc(p.expected) + "</td></tr>";
      });
      fb.appendChild(el("div", { class: "fb-block", html: "<h4>Your answers</h4>" + h + "</table>" }));
    } else if (!r.correct) {
      const p = r.parts[0];
      fb.appendChild(el("div", { class: "fb-block", html: "You answered <b class=mono>" + esc(p.given) + "</b>; the correct answer is <b class=mono>" + esc(p.expected) + "</b>." }));
    }
    r.parts.forEach(function (p) {
      if (p.why) fb.appendChild(el("div", { class: "callout " + (p.correct ? "green" : "amber"), html: "<b>" + esc(p.given) + ":</b> " + esc(p.why) }));
      if (p.details) {
        let h = '<h4>' + md(p.label) + '</h4><ul class="why-list">';
        p.details.forEach(function (d) {
          const mark = d.selected === d.valid ? '<span class="ok-mark">✓</span>' : (d.selected ? '<span class="bad-mark">✗</span>' : '<span class="warn-mark">!</span>');
          h += "<li>" + mark + '<span class="opt-name">' + esc(d.option) + "</span><span>" + (d.valid ? "<b>valid</b>" : "<b>not valid</b>") + (d.why ? " - " + esc(d.why) : "") +
            (d.selected !== d.valid ? (d.selected ? ' <span class="bad-mark">(you selected it)</span>' : ' <span class="warn-mark">(you missed it)</span>') : "") + "</span></li>";
        });
        fb.appendChild(el("div", { class: "fb-block", html: h + "</ul>" }));
      }
    });
  };

  function testsTable(tests) {
    if (!tests) return "";
    if (!tests.runnable) return '<div class="callout red"><b>Couldn\'t run your code:</b> ' + esc(tests.error) + "</div>";
    let h = '<h4>Tests: ' + tests.passed + " / " + tests.total + ' passed</h4><table class="tests"><tr><th></th><th>Input</th><th>Expected</th><th>Got</th></tr>';
    tests.results.forEach(function (t) {
      h += "<tr><td>" + (t.ok ? '<span class="ok-mark">✓</span>' : '<span class="bad-mark">✗</span>') + "</td><td>" + esc(t.input) + "</td><td>" + esc(t.expected) +
        "</td><td>" + (t.error ? '<span class="bad-mark">' + esc(t.error) + "</span>" : esc(t.got)) + "</td></tr>";
    });
    return h + "</table>";
  }

  Runner.prototype.feedbackFill = function (r) {
    const self = this;
    r.blanks.forEach(function (b) {
      const inp = self.blanks[b.index];
      inp.classList.remove("right", "wrong");
      inp.classList.add(b.correct ? "right" : "wrong");
    });
    const wrong = r.blanks.filter(function (b) { return !b.correct; }).length;
    if (wrong) this.feedback.appendChild(el("p", { text: wrong + " blank" + (wrong > 1 ? "s need" : " needs") + " another look (marked in red)." }));
    if (r.tests && !r.correct) this.feedback.appendChild(el("div", { class: "fb-block", html: testsTable(r.tests) }));
  };

  Runner.prototype.feedbackOrder = function (r) {
    if (r.error) { this.feedback.appendChild(el("div", { class: "callout red", text: r.error })); return; }
    const right = r.positions.filter(function (p) { return p.correct; }).length;
    if (!r.correct) {
      this.feedback.appendChild(el("p", { text: right + " of " + r.positions.length + " lines are in the reference position. Look at what must exist before each line can run." }));
      const byId = {};
      r.positions.forEach(function (p) { byId[p.id] = p.correct; });
      this.orderList.items.forEach(function (it) { it.mark = byId[it.id] ? "right" : "wrong"; });
      this.orderList.draw();
      if (r.tests) this.feedback.appendChild(el("div", { class: "fb-block", html: testsTable(r.tests) }));
    } else {
      this.orderList.items.forEach(function (it) { it.mark = "right"; });
      this.orderList.draw();
    }
  };

  Runner.prototype.feedbackCode = function (r) {
    const fb = this.feedback;
    if (r.structure_only) {
      fb.appendChild(el("div", { class: "callout amber", html: "<b>Structure check only.</b> Your code couldn't be executed (" + esc(r.tests.error) +
        "), so it was graded on its structure. Try to follow the convention shown in <a href='/learn#convention'>Learn → Pseudocode convention</a>." }));
    }
    if (r.rubric && r.rubric.length) {
      let h = '<h4>Structural concepts</h4><ul class="checklist">';
      r.rubric.forEach(function (it) {
        h += "<li>" + (it.ok ? '<span class="ok-mark">✓</span> ' : '<span class="warn-mark">○</span> ') + esc(it.label) +
          (it.ok ? "" : '<span class="h">' + esc(it.hint) + (r.correct ? " (not detected, but your code works)" : "") + "</span>") + "</li>";
      });
      fb.appendChild(el("div", { class: "fb-block", html: h + "</ul>" }));
    }
    if (!r.structure_only) fb.appendChild(el("div", { class: "fb-block", html: testsTable(r.tests) }));
  };

  Runner.prototype.feedbackDebug = function (r) {
    const fb = this.feedback;
    fb.appendChild(el("div", { class: "fb-block", html:
      "<p>" + (r.line_ok ? '<span class="ok-mark">✓</span> You found the buggy line.' : '<span class="bad-mark">✗</span> Line ' + esc(r.line) + " isn't where the bug is.") + "</p><p>" +
      (r.fix_ok ? '<span class="ok-mark">✓</span> Your fix passes every test.' : (r.unchanged ? '<span class="bad-mark">✗</span> The code is unchanged - edit it in the editor.' : '<span class="bad-mark">✗</span> Your fixed code doesn\'t pass all tests yet.')) + "</p>" }));
    if (r.tests && !r.fix_ok && !r.unchanged) fb.appendChild(el("div", { class: "fb-block", html: testsTable(r.tests) }));
  };

  Runner.prototype.feedbackTrace = function (r) {
    const inputs = this.traceTable.querySelectorAll("input");
    inputs.forEach(function (i) {
      const cell = r.table[+i.dataset.r][+i.dataset.c];
      const td = i.parentElement;
      td.classList.add(cell.correct ? "right" : "wrong");
      if (!cell.correct) td.insertAdjacentHTML("beforeend", '<span class="exp">' + esc(cell.expected) + "</span>");
    });
    if (!r.correct) this.feedback.appendChild(el("p", { text: r.wrong_cells + " cell" + (r.wrong_cells > 1 ? "s differ" : " differs") + " from the actual execution (correct values shown in green)." }));
  };

  // ======================================================================= solution
  Runner.prototype.showSolution = function (sol) {
    const v = this.view, t = v.type, fb = this.feedback;
    if (!sol) return;
    if (sol.answers && !this.state.attempts) {
      let h = '<table class="data">';
      sol.answers.forEach(function (a) { h += "<tr><td>" + md(a.label) + "</td><td class=mono><b>" + esc(a.answer) + "</b></td></tr>"; });
      fb.appendChild(el("div", { class: "fb-block", html: "<h4>Answer</h4>" + h + "</table>" }));
    }
    if (sol.highlights && sol.highlights.length && sol.code) {
      this.codeHolder.innerHTML = "";
      this.codeHolder.appendChild(BT.renderCode(sol.code, { highlights: sol.highlights }));
      const leg = el("div", { class: "legend" });
      sol.highlights.forEach(function (h) { leg.appendChild(el("span", { class: "c" + (h.color % 4), text: "line " + h.lines.join(", ") + ": " + h.label })); });
      this.codeHolder.appendChild(leg);
    }
    if (sol.steps && sol.steps.length) {
      fb.appendChild(el("div", { class: "fb-block", html: "<h4>" + (v.track === "complexity" || t === "to_complexity" ? "Step-by-step analysis" : "Explanation") + "</h4>" }));
      fb.lastChild.appendChild(el("div", { class: "steps", text: sol.steps.join("\n") }));
    }
    if (sol.note) fb.appendChild(el("div", { class: "callout", text: sol.note }));
    if (t === "fill" && sol.blanks) {
      fb.appendChild(el("div", { class: "fb-block", html: "<h4>Blanks</h4>" + sol.blanks.map(function (b, i) { return "<div>Blank " + (i + 1) + ": <code>" + esc(b) + "</code></div>"; }).join("") }));
    }
    if (t === "trace" && sol.rows) {
      let h = '<h4>Complete trace table</h4><table class="trace"><tr><th>#</th>' + sol.watch.map(function (w) { return "<th>" + esc(w) + "</th>"; }).join("") + "</tr>";
      sol.rows.forEach(function (r, i) { h += "<tr><td class=rowlab>" + (i + 1) + "</td>" + r.map(function (c) { return "<td>" + esc(c) + "</td>"; }).join("") + "</tr>"; });
      fb.appendChild(el("div", { class: "fb-block", html: h + "</table>" }));
    }
    if (t === "debug" && sol.code) {
      const a = sol.buggy.split("\n"), b = sol.code.split("\n");
      const rcA = {}, rcB = {};
      if (a.length === b.length) a.forEach(function (l, i) { if (l !== b[i]) { rcA[i + 1] = "removed"; rcB[i + 1] = "changed"; } });
      const blk = el("div", { class: "fb-block", html: "<h4>Buggy (red) → corrected (green)</h4>" });
      blk.appendChild(BT.renderCode(sol.buggy, { rowClass: rcA }));
      blk.appendChild(BT.renderCode(sol.code, { rowClass: rcB }));
      fb.appendChild(blk);
    } else if (sol.code && ["fill", "order", "complete", "write"].indexOf(t) >= 0) {
      const blk = el("div", { class: "fb-block", html: "<h4>Reference solution</h4>" });
      blk.appendChild(BT.renderCode(sol.code));
      if (t === "write" || t === "complete") blk.appendChild(el("p", { class: "muted", style: "font-size:.88rem", text: "Any solution that passes the tests is accepted - this is one possible version." }));
      fb.appendChild(blk);
    }
  };

  window.ExerciseRunner = Runner;
})();
