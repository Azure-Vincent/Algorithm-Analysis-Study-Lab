  function QuickPractice(opts) {
    const self = this;
    this.opts = opts;
    this.count = 10;
    this.matching = null;
    const bar = opts.bar;
    bar.classList.add("quick-practice");
    this.info = el("div", { class: "qp-info" });
    bar.appendChild(this.info);
    const seg = el("div", { class: "seg", "data-key": "count" });
    [5, 10, 20, 0].forEach(function (n) {
      const b = el("button", { "data-v": String(n), text: n ? String(n) : "Unlimited", class: n === self.count ? "on" : "" });
      b.addEventListener("click", function () {
        seg.querySelectorAll("button").forEach(function (x) { x.classList.remove("on"); });
        b.classList.add("on");
        self.count = n;
      });
      seg.appendChild(b);
    });
    bar.appendChild(el("span", { class: "qp-lab muted", text: "Questions" }));
    bar.appendChild(seg);
    this.startBtn = el("button", { class: "btn primary qp-start", text: "Start practicing", onclick: function () { self.start(); } });
    bar.appendChild(this.startBtn);
    this.runner = new SessionRunner(opts.session, { onRestart: function () { self.back(); } });
  }

  /** Called by the page whenever its filters change: n = number of bank exercises that match. */
  QuickPractice.prototype.update = function (n) {
    this.matching = n;
    const f = this.opts.filters();
    this.info.innerHTML = "<b>Practice " + esc(f.label || "this track") + "</b><span class='muted'>" +
      (n ? n + " matching exercise" + (n === 1 ? "" : "s") + " · questions repeat once all are seen" : "No exercises match these filters") + "</span>";
    this.startBtn.disabled = !n;
  };

  QuickPractice.prototype.start = function () {
    const f = this.opts.filters();
    const cfg = { mode: "practice", count: this.count, track: this.opts.track };
    if (f.subtopic) cfg.subtopic = f.subtopic;
    if (f.type) cfg.type = f.type;
    if (f.level) cfg.level = +f.level;
    if (f.difficulty) cfg.difficulty = f.difficulty;
    this.opts.browse.classList.add("hidden");
    this.opts.session.innerHTML = "";
    const backRow = el("div", { class: "qp-back" });
    const self = this;
    backRow.appendChild(el("button", { class: "btn small ghost", text: "← Back to " + (this.opts.title || "exercises"), onclick: function () {
      if (self.runner.sid && !self.runner.finished) BT.api("/api/session/" + self.runner.sid + "/end", {}).catch(function () {});
      self.back();
    } }));
    backRow.appendChild(el("span", { class: "muted", text: "Practicing: " + (f.label || "this track") }));
    this.opts.session.parentNode.insertBefore(backRow, this.opts.session);
    this.backRow = backRow;
    this.runner.start(cfg);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  QuickPractice.prototype.back = function () {
    this.opts.session.innerHTML = "";
    if (this.backRow) { this.backRow.remove(); this.backRow = null; }
    this.opts.browse.classList.remove("hidden");
    if (this.opts.onReturn) this.opts.onReturn();
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  window.QuickPractice = QuickPractice;
})();