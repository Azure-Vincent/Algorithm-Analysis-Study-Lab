/* MockExam - take a generated mock exam (free navigation, flags, autosave) and review the graded results. */
(function () {
  "use strict";
  const esc = BT.esc, el = BT.el;
  const $ = (id) => document.getElementById(id);

  function textBlock(s) { return el("p", { class: "mock-text", text: s }); }

  const MockExam = {
    init: function (examId) {
      const self = this;
      if (!examId) {
        let count = 12;
        document.querySelectorAll("#mock-count button").forEach(function (b) {
          b.addEventListener("click", function () {
            document.querySelectorAll("#mock-count button").forEach(function (x) { x.classList.remove("on"); });
            b.classList.add("on");
            count = +b.dataset.v;
          });
        });
        $("mock-start").addEventListener("click", async function () {
          this.disabled = true;
          this.textContent = "Generating your exam…";
          try {
            const r = await BT.api("/api/mock", { count: count });
            window.location.href = "/mock/" + r.id;
          } catch (e) { BT.toast(e.message); this.disabled = false; this.textContent = "Start mock exam"; }
        });
        return;
      }
      this.id = examId;
      this.root = $("mock-root");
      this.load();
      window.addEventListener("beforeunload", function () { self.flush(true); });
    },

    load: async function () {
      try { this.exam = await BT.api("/api/mock/" + this.id); } catch (e) { this.root.innerHTML = '<div class="callout red">' + esc(e.message) + "</div>"; return; }
      if (this.exam.submitted) { this.renderResults(); return; }
      this.answers = this.exam.answers || {};
      this.flags = new Set(this.exam.flags || []);
      this.cur = 0;
      this.dirty = {};
      this.renderExam();
    },

    // ===================================================================== taking the exam
    renderExam: function () {
      const self = this, ex = this.exam;
      this.root.innerHTML = "";
      const head = el("div", { class: "page-head" });
      head.appendChild(el("div", {}, [el("h1", { text: "Mock exam" }),
        el("p", { class: "muted", text: ex.questions.length + " questions · answers stay hidden until you submit · your work is saved automatically" })]));
      this.root.appendChild(head);
      const layout = el("div", { class: "mock-layout" });
      this.nav = el("nav", { class: "mock-nav card", "aria-label": "Questions" });
      this.main = el("div", { class: "mock-main" });
      layout.appendChild(this.nav);
      layout.appendChild(this.main);
      this.root.appendChild(layout);
      this.drawNav();
      this.drawQuestion();
    },

    answered: function (q) {
      const a = this.answers[q.qid] || {};
      return Object.keys(a).some(function (k) { return String(a[k] || "").trim() !== ""; });
    },

    drawNav: function () {
      const self = this, ex = this.exam;
      this.nav.innerHTML = '<div class="plabel">Questions</div>';
      const grid = el("div", { class: "mock-nav-grid" });
      ex.questions.forEach(function (q, i) {
        const b = el("button", { type: "button", class: "mock-nav-btn" + (i === self.cur ? " current" : "") + (self.answered(q) ? " answered" : "") +
          (self.flags.has(q.qid) ? " flagged" : ""), text: String(q.number), title: q.category_label + (self.flags.has(q.qid) ? " · flagged" : ""),
          "aria-label": "Question " + q.number + (self.answered(q) ? ", answered" : ", not answered") + (self.flags.has(q.qid) ? ", flagged for review" : "") });
        b.addEventListener("click", function () { self.go(i); });
        grid.appendChild(b);
      });
      this.nav.appendChild(grid);
      const done = ex.questions.filter(function (q) { return self.answered(q); }).length;
      this.nav.appendChild(el("p", { class: "muted", style: "font-size:.85rem;margin:10px 0 4px",
        html: done + " / " + ex.questions.length + " answered" + (self.flags.size ? " · " + self.flags.size + " flagged" : "") }));
      this.nav.appendChild(el("div", { class: "mock-legend", html: '<span class="sw answered"></span>answered <span class="sw flagged"></span>flagged' }));
      this.nav.appendChild(el("button", { class: "btn primary", style: "width:100%;margin-top:12px", text: "Submit exam", onclick: function () { self.submit(); } }));
    },

    go: function (i) {
      this.flush(false);
      this.cur = Math.max(0, Math.min(this.exam.questions.length - 1, i));
      this.drawNav();
      this.drawQuestion();
      window.scrollTo({ top: 0, behavior: "smooth" });
    },

    drawQuestion: function () {
      const self = this, q = this.exam.questions[this.cur];
      const ans = this.answers[q.qid] = this.answers[q.qid] || {};
      this.main.innerHTML = "";
      const card = el("div", { class: "card pad-lg mock-q" });
      const top = el("div", { class: "mock-q-head" });
      top.appendChild(el("span", { class: "mock-q-num", text: "Question " + q.number + " of " + this.exam.questions.length }));
      top.appendChild(el("span", { class: "badge " + ({ asym: "blue", panalysis: "amber", design: "purple", discrete: "green" }[q.category] || ""), text: q.category_label }));
      top.appendChild(el("span", { class: "muted", style: "font-size:.85rem", text: q.points + " points" }));
      if (this.flags.has(q.qid)) top.appendChild(el("span", { class: "badge red", text: "flagged for review" }));
      card.appendChild(top);
      card.appendChild(el("h2", { text: q.title }));
      card.appendChild(textBlock(q.text));
      if (q.code) card.appendChild(BT.renderCode(q.code));
      const form = el("div", { class: "mock-fields" });
      q.fields.forEach(function (f) { form.appendChild(self.field(q, f, ans)); });
      card.appendChild(form);

      const ctl = el("div", { class: "controls" });
      const prev = el("button", { class: "btn", text: "← Previous", onclick: function () { self.go(self.cur - 1); } });
      prev.disabled = this.cur === 0;
      ctl.appendChild(prev);
      const flagged = this.flags.has(q.qid);
      ctl.appendChild(el("button", { class: "btn" + (flagged ? " flag-on" : ""), "aria-pressed": flagged ? "true" : "false",
        text: flagged ? "⚑ Flagged - remove flag" : "⚑ Flag for review", onclick: function () { self.toggleFlag(q); } }));
      ctl.appendChild(el("span", { class: "spacer" }));
      this.saveState = el("span", { class: "muted", style: "font-size:.85rem", text: "Saved" });
      ctl.appendChild(this.saveState);
      if (this.cur < this.exam.questions.length - 1) ctl.appendChild(el("button", { class: "btn primary", text: "Next →", onclick: function () { self.go(self.cur + 1); } }));
      else ctl.appendChild(el("button", { class: "btn primary", text: "Submit exam", onclick: function () { self.submit(); } }));
      card.appendChild(ctl);
      this.main.appendChild(card);
      if (this.editor) this.editor.refresh();
    },

    field: function (q, f, ans) {
      const self = this, wrap = el("div", { class: "mock-field" });
      const id = "f-" + q.qid + "-" + f.id;
      wrap.appendChild(el("label", { class: "plabel", for: id, text: f.label }));
      const onChange = function (v) { ans[f.id] = v; self.markDirty(q); };
      if (f.kind === "code") {
        const holder = el("div", { id: id });
        wrap.appendChild(holder);
        this.editor = new PseudoEditor(holder, { value: ans.code || f.placeholder || "", minLines: 10 });
        this.editor.onChange = function () { onChange(self.editor.getValue()); };
        if (!ans.code && f.placeholder) ans.code = f.placeholder;
      } else if (f.kind === "textarea") {
        const t = el("textarea", { id: id, class: "scratch", rows: "5", placeholder: f.placeholder || "" });
        t.value = ans[f.id] || "";
        t.addEventListener("input", function () { onChange(t.value); });
        wrap.appendChild(t);
      } else if (f.kind === "choice") {
        const seg = el("div", { class: "seg", role: "radiogroup", "aria-label": f.label });
        f.options.forEach(function (o) {
          const b = el("button", { type: "button", text: o, class: ans[f.id] === o ? "on" : "", role: "radio", "aria-checked": ans[f.id] === o ? "true" : "false" });
          b.addEventListener("click", function () {
            seg.querySelectorAll("button").forEach(function (x) { x.classList.remove("on"); x.setAttribute("aria-checked", "false"); });
            b.classList.add("on"); b.setAttribute("aria-checked", "true");
            onChange(o);
          });
          seg.appendChild(b);
        });
        wrap.appendChild(seg);
      } else {
        const inp = el("input", { id: id, type: "text", autocomplete: "off", spellcheck: "false", placeholder: f.placeholder || "",
          class: f.kind === "number" ? "number-input" : "mock-input" });
        inp.value = ans[f.id] || "";
        inp.addEventListener("input", function () { onChange(inp.value); });
        wrap.appendChild(inp);
      }
      return wrap;
    },

    markDirty: function (q) {
      const self = this;
      this.dirty[q.qid] = true;
      if (this.saveState) this.saveState.textContent = "Saving…";
      clearTimeout(this.timer);
      this.timer = setTimeout(function () { self.flush(false); }, 700);
    },

    flush: function (sync) {
      const self = this;
      clearTimeout(this.timer);
      const ids = Object.keys(this.dirty || {});
      this.dirty = {};
      ids.forEach(function (qid) {
        const body = JSON.stringify({ qid: qid, answer: self.answers[qid] || {} });
        if (sync && navigator.sendBeacon) {
          navigator.sendBeacon("/api/mock/" + self.id + "/answer", new Blob([body], { type: "application/json" }));
        } else {
          BT.api("/api/mock/" + self.id + "/answer", { qid: qid, answer: self.answers[qid] || {} })
            .then(function () { if (self.saveState) self.saveState.textContent = "Saved"; self.refreshNavState(); })
            .catch(function (e) { if (self.saveState) self.saveState.textContent = "Not saved: " + e.message; });
        }
      });
      if (!ids.length && this.saveState) this.saveState.textContent = "Saved";
    },

    refreshNavState: function () {
      const self = this;
      this.nav.querySelectorAll(".mock-nav-btn").forEach(function (b, i) { b.classList.toggle("answered", self.answered(self.exam.questions[i])); });
    },

    toggleFlag: async function (q) {
      const on = !this.flags.has(q.qid);
      try {
        await BT.api("/api/mock/" + this.id + "/answer", { qid: q.qid, flagged: on });
        if (on) this.flags.add(q.qid); else this.flags.delete(q.qid);
        this.drawNav();
        this.drawQuestion();
      } catch (e) { BT.toast(e.message); }
    },

    submit: async function () {
      const self = this, qs = this.exam.questions;
      this.flush(false);
      const open = qs.filter(function (q) { return !self.answered(q); }).length;
      const msg = "Submit the exam now?" + (open ? "\n\n" + open + " question" + (open > 1 ? "s are" : " is") + " unanswered." : "") +
        (this.flags.size ? "\n" + this.flags.size + " question" + (this.flags.size > 1 ? "s are" : " is") + " flagged for review." : "") +
        "\n\nAfter submitting you can't change your answers.";
      if (!confirm(msg)) return;
      this.main.innerHTML = '<div class="card pad-lg"><p>Grading your exam - running your pseudocode against test inputs…</p></div>';
      try {
        await new Promise(function (r) { setTimeout(r, 300); });     // let the last autosave land first
        for (const qid of Object.keys(this.answers)) {
          await BT.api("/api/mock/" + this.id + "/answer", { qid: qid, answer: this.answers[qid] || {} });
        }
        this.exam = await BT.api("/api/mock/" + this.id + "/submit", {});
        this.renderResults();
        window.scrollTo({ top: 0 });
      } catch (e) { BT.toast(e.message); this.drawQuestion(); }
    },

    // ===================================================================== results
    renderResults: function () {
      const ex = this.exam, res = ex.results;
      const byQ = {};
      res.questions.forEach(function (r) { byQ[r.qid] = r; });
      this.root.innerHTML = "";
      const head = el("div", { class: "page-head" });
      head.appendChild(el("div", {}, [el("h1", { text: "Mock exam results" }), el("p", { class: "muted", text: "Submitted · " + ex.questions.length + " questions" })]));
      head.appendChild(el("div", { class: "btn-row" }, [el("a", { class: "btn primary", href: "/mock", text: "New mock exam" })]));
      this.root.appendChild(head);

      const summary = el("div", { class: "grid grid-2" });
      const scoreCard = el("div", { class: "card pad-lg mock-score" });
      scoreCard.innerHTML = '<div class="plabel">Overall</div><div class="mock-big">' + res.score + '%</div><div class="muted">' + res.earned + " / " + res.max + " points</div>";
      summary.appendChild(scoreCard);
      const catCard = el("div", { class: "card pad-lg" });
      let h = '<div class="plabel">By category</div><table class="data">';
      res.categories.forEach(function (c) {
        const p = c.percent;
        h += "<tr><td>" + esc(c.label) + '</td><td style="width:45%"><div class="bar ' + (p < 55 ? "red" : p < 75 ? "amber" : "green") + '"><span style="width:' + p + '%"></span></div></td><td class="num"><b>' + p + "%</b></td><td class=\"num muted\">" + c.earned + "/" + c.max + "</td></tr>";
      });
      catCard.innerHTML = h + "</table>";
      summary.appendChild(catCard);
      this.root.appendChild(summary);

      const list = el("div", { class: "mock-results" });
      ex.questions.forEach(function (q) {
        const r = byQ[q.qid], a = (ex.answers || {})[q.qid] || {};
        const status = r.earned >= r.max ? "ok" : r.earned > 0 ? "partial" : "bad";
        const d = el("details", { class: "mistake test-q " + (status === "ok" ? "ok" : "bad") });
        if (status !== "ok") d.setAttribute("open", "open");
        d.innerHTML = "<summary>" + { ok: '<span class="ok-mark">✓</span>', partial: '<span class="warn-mark">◐</span>', bad: '<span class="bad-mark">✗</span>' }[status] +
          " <b>" + q.number + ". " + esc(q.title) + '</b> <span class="muted">' + esc(q.category_label) + '</span> <span class="badge">' + r.earned + " / " + r.max + " points</span></summary>";
        const body = el("div", { class: "body" });
        body.appendChild(el("div", { class: "plabel", text: "Question" }));
        body.appendChild(textBlock(q.text));
        if (q.code) body.appendChild(BT.renderCode(q.code));
        body.appendChild(el("div", { class: "plabel", text: "Your answer" }));
        const yours = el("div", { class: "mock-yours" });
        q.fields.forEach(function (f) {
          const v = a[f.id];
          yours.appendChild(el("div", { class: "plabel muted", style: "font-weight:400", text: f.label }));
          if (f.kind === "code" && v) yours.appendChild(BT.renderCode(v));
          else yours.appendChild(el("pre", { class: "plain", text: v && String(v).trim() ? String(v) : "(no answer)" }));
        });
        body.appendChild(yours);
        let t = '<div class="plabel">Points</div><table class="data mock-rubric"><tr><th>Criterion</th><th class="num">Points</th><th>Feedback</th></tr>';
        r.rubric.forEach(function (it) {
          t += "<tr><td>" + esc(it.label) + '</td><td class="num">' + (it.earned >= it.max ? '<span class="ok-mark">' : it.earned > 0 ? '<span class="warn-mark">' : '<span class="bad-mark">') +
            it.earned + "</span> / " + it.max + "</td><td>" + esc(it.note || "") + "</td></tr>";
        });
        body.insertAdjacentHTML("beforeend", t + "</table>");
        body.appendChild(el("div", { class: "plabel", text: "Correct answer" }));
        body.appendChild(el("p", { text: r.answer_key }));
        body.appendChild(el("div", { class: "plabel", text: "Model solution / explanation" }));
        body.appendChild(el("pre", { class: "plain mock-model", text: r.model.join("\n") }));
        d.appendChild(body);
        list.appendChild(d);
      });
      this.root.appendChild(el("h3", { text: "Question by question" }));
      this.root.appendChild(list);
    },
  };

  window.MockExam = MockExam;
})();
