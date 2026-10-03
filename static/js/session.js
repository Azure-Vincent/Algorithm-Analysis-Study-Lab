/* SessionRunner - drives practice, adaptive, and review sessions and renders the end-of-session report. */
(function () {
  "use strict";
  const esc = BT.esc, el = BT.el;

  function SessionRunner(root, opts) {
    this.root = root;
    this.opts = opts || {};
  }

  SessionRunner.prototype.start = async function (config) {
    this.config = config;
    try {
      const s = await BT.api("/api/session", config);
      this.sid = s.id;
      this.total = s.config.count || null;
      if (!s.pool_size && s.config.review) {
        this.root.innerHTML = '<div class="empty">Nothing to review right now - no open or improving mistakes. 🎉</div>';
        return;
      }
    } catch (e) { BT.toast(e.message); return; }
    this.root.innerHTML = "";
    this.bar = el("div", { class: "session-bar" });
    this.root.appendChild(this.bar);
    this.exHolder = el("div");
    this.root.appendChild(this.exHolder);
    this.answered = 0;
    this.next();
  };

  SessionRunner.prototype.drawBar = function (index) {
    const self = this;
    const pct = this.total ? Math.round(100 * (index - 1) / this.total) : 0;
    this.bar.innerHTML = "<span>Question <b>" + index + "</b>" + (this.total ? " of " + this.total : " (unlimited)") + "</span>" +
      (this.total ? '<div class="bar"><span style="width:' + pct + '%"></span></div>' : "") + '<span class="spacer"></span>';
    this.bar.appendChild(el("button", { class: "btn small ghost", text: "End session & see report", onclick: function () { self.end(); } }));
  };

  SessionRunner.prototype.next = async function () {
    try {
      const r = await BT.api("/api/session/" + this.sid + "/next", {});
      if (r.done) { this.end(r.reason); return; }
      this.drawBar(r.index);
      const self = this;
      const isLast = this.total && r.index >= this.total;
      const runner = new ExerciseRunner(this.exHolder, {
        context: this.config.mode, sessionId: this.sid,
        onNext: function () { self.next(); },
        nextLabel: "Skip →",
        nextDoneLabel: isLast ? "Finish & see report →" : "Next question →",
      });
      await runner.load(r.exercise_id);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) { BT.toast(e.message); }
  };

  SessionRunner.prototype.end = async function (reason) {
    try {
      const s = await BT.api("/api/session/" + this.sid + "/end", {});
      this.renderSummary(s, reason);
    } catch (e) { BT.toast(e.message); }
  };

  SessionRunner.prototype.renderSummary = function (s, reason) {
    const self = this;
    this.root.innerHTML = "";
    const box = el("div", { class: "card pad-lg" });
    box.appendChild(el("h2", { text: "Session report" }));
    if (reason) box.appendChild(el("div", { class: "callout", text: reason }));
    if (!s.answered) {
      box.appendChild(el("p", { class: "muted", text: "No questions were answered in this session." }));
    } else {
      const acc = s.accuracy === null ? "-" : s.accuracy + "%";
      box.insertAdjacentHTML("beforeend",
        '<div class="stat-grid">' +
        stat(s.correct, "Correct answers") + stat(s.incorrect, "Incorrect / revealed") + stat(acc, "Accuracy (first try)") +
        stat(s.no_hints, "Correct without hints") + stat(s.after_hints, "Correct after hints") +
        stat(s.avg_attempts == null ? "-" : s.avg_attempts, "Average attempts") + "</div>");
      if (s.difficult_topics.length) {
        let h = '<h3 style="margin-top:20px">Topics that caused difficulty</h3><table class="data"><tr><th>Topic</th><th class=num>Missed</th><th class=num>Accuracy</th><th></th></tr>';
        s.difficult_topics.forEach(function (d) {
          h += "<tr><td>" + esc(d.label) + "</td><td class=num>" + d.missed + " / " + d.total + "</td><td class=num>" + d.accuracy + "%</td><td style='width:35%'><div class='bar " +
            (d.accuracy < 50 ? "red" : "amber") + "'><span style='width:" + d.accuracy + "%'></span></div></td></tr>";
        });
        box.insertAdjacentHTML("beforeend", h + "</table>");
      } else {
        box.insertAdjacentHTML("beforeend", '<div class="callout green" style="margin-top:16px">No topic caused trouble this session - every question was right on the first try.</div>');
      }
      if (s.per_topic.length > 1) {
        let h = '<h3 style="margin-top:20px">By topic</h3><table class="data"><tr><th>Topic</th><th class=num>Questions</th><th class=num>First-try accuracy</th></tr>';
        s.per_topic.forEach(function (d) { h += "<tr><td>" + esc(d.label) + "</td><td class=num>" + d.total + "</td><td class=num>" + d.accuracy + "%</td></tr>"; });
        box.insertAdjacentHTML("beforeend", h + "</table>");
      }
    }
    const row = el("div", { class: "btn-row", style: "margin-top:20px" });
    row.appendChild(el("button", { class: "btn primary", text: "Start another session", onclick: function () { if (self.opts.onRestart) self.opts.onRestart(); } }));
    row.appendChild(el("a", { class: "btn", href: "/review", text: "Review mistakes" }));
    row.appendChild(el("a", { class: "btn ghost", href: "/progress", text: "Progress" }));
    box.appendChild(row);
    this.root.appendChild(box);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  function stat(v, l) { return '<div class="stat"><span class="v">' + esc(v) + '</span><span class="l">' + esc(l) + "</span></div>"; }

  window.SessionRunner = SessionRunner;
})();
