/* A lightweight pseudocode editor: line numbers, highlighting, Tab/Shift+Tab, auto-indent. */
(function () {
  "use strict";
  const INDENT = "    ";
  const OPENERS = /^\s*(procedure|function|algorithm|if|else|elseif|else if|for|while|repeat)\b.*$/i;

  function PseudoEditor(container, opts) {
    opts = opts || {};
    this.initial = opts.value || "";
    this.minLines = opts.minLines || 8;
    this.onChange = opts.onChange || null;
    container.innerHTML = "";
    const root = document.createElement("div");
    root.className = "editor";
    root.innerHTML = '<div class="gutter"></div><div class="area"><pre aria-hidden="true"></pre>' +
      '<textarea spellcheck="false" autocapitalize="off" autocomplete="off" autocorrect="off" wrap="off"></textarea></div>';
    container.appendChild(root);
    this.root = root;
    this.gutter = root.querySelector(".gutter");
    this.pre = root.querySelector("pre");
    this.ta = root.querySelector("textarea");
    this.ta.value = this.initial;
    if (opts.placeholder) this.ta.placeholder = opts.placeholder;
    const self = this;
    this.ta.addEventListener("input", function () { self.refresh(); if (self.onChange) self.onChange(); });
    this.ta.addEventListener("scroll", function () { self.syncScroll(); });
    this.ta.addEventListener("keydown", function (e) { self.onKey(e); });
    this.refresh();
    if (opts.focus) setTimeout(function () { self.focusEnd(); }, 30);
  }

  PseudoEditor.prototype.refresh = function () {
    const v = this.ta.value;
    const lines = v.split("\n");
    const n = Math.max(lines.length, this.minLines);
    let g = "";
    for (let i = 1; i <= lines.length; i++) g += i + "\n";
    this.gutter.textContent = g;
    this.pre.innerHTML = lines.map(function (l) { return BT.highlight(l); }).join("\n") + "\n";
    const lineH = 21.6;
    this.ta.style.minHeight = (n * lineH + 22) + "px";
    this.ta.style.height = "auto";
    this.ta.style.height = Math.max(this.ta.scrollHeight, n * lineH + 22) + "px";
    this.syncScroll();
  };

  PseudoEditor.prototype.syncScroll = function () {
    this.pre.scrollTop = this.ta.scrollTop;
    this.pre.scrollLeft = this.ta.scrollLeft;
    this.gutter.scrollTop = this.ta.scrollTop;
  };

  PseudoEditor.prototype.getValue = function () { return this.ta.value; };
  PseudoEditor.prototype.setValue = function (v) { this.ta.value = v; this.refresh(); };
  PseudoEditor.prototype.reset = function () { this.setValue(this.initial); this.focusEnd(); };
  PseudoEditor.prototype.setReadOnly = function (ro) { this.ta.readOnly = !!ro; };
  PseudoEditor.prototype.focusEnd = function () {
    this.ta.focus();
    const L = this.ta.value.length;
    this.ta.setSelectionRange(L, L);
  };

  PseudoEditor.prototype.replaceRange = function (start, end, text, selStart, selEnd) {
    const ta = this.ta;
    ta.setSelectionRange(start, end);
    let ok = false;
    try { ok = document.execCommand && document.execCommand("insertText", false, text); } catch (e) { ok = false; }
    if (!ok) {
      ta.value = ta.value.slice(0, start) + text + ta.value.slice(end);
    }
    ta.setSelectionRange(selStart, selEnd === undefined ? selStart : selEnd);
    this.refresh();
    if (this.onChange) this.onChange();
  };

  PseudoEditor.prototype.onKey = function (e) {
    const ta = this.ta;
    if (ta.readOnly) return;
    const v = ta.value, s = ta.selectionStart, en = ta.selectionEnd;
    if (e.key === "Tab") {
      e.preventDefault();
      const lineStart = v.lastIndexOf("\n", s - 1) + 1;
      if (s === en && !e.shiftKey) {
        this.replaceRange(s, en, INDENT, s + INDENT.length);
        return;
      }
      // indent / dedent every selected line
      const blockEnd = en > s && v[en - 1] === "\n" ? en - 1 : en;
      const lineEnd = v.indexOf("\n", blockEnd);
      const stop = lineEnd === -1 ? v.length : lineEnd;
      const block = v.slice(lineStart, stop);
      let lines = block.split("\n");
      let delta0 = 0, total = 0;
      lines = lines.map(function (l, i) {
        if (e.shiftKey) {
          const m = l.match(/^( {1,4}|\t)/);
          const cut = m ? m[0].length : 0;
          if (i === 0) delta0 = -cut;
          total -= cut;
          return l.slice(cut);
        }
        if (i === 0) delta0 = INDENT.length;
        total += INDENT.length;
        return INDENT + l;
      });
      const newBlock = lines.join("\n");
      const ns = Math.max(lineStart, s + delta0);
      this.replaceRange(lineStart, stop, newBlock, s === en ? ns : lineStart, s === en ? ns : lineStart + newBlock.length);
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      const lineStart = v.lastIndexOf("\n", s - 1) + 1;
      const cur = v.slice(lineStart, s);
      let indent = (cur.match(/^\s*/) || [""])[0];
      if (OPENERS.test(cur) && !/^\s*(return|end)\b/i.test(cur)) indent += INDENT;
      const ins = "\n" + indent;
      this.replaceRange(s, en, ins, s + ins.length);
      return;
    }
    if (e.key === "Backspace" && s === en) {
      const lineStart = v.lastIndexOf("\n", s - 1) + 1;
      const before = v.slice(lineStart, s);
      if (before.length > 0 && /^ +$/.test(before)) {
        const cut = before.length % 4 === 0 ? 4 : before.length % 4;
        e.preventDefault();
        this.replaceRange(s - cut, s, "", s - cut);
      }
    }
  };

  window.PseudoEditor = PseudoEditor;
})();
