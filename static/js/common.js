/* Shared helpers: API calls, escaping, syntax highlighting, code views. */
(function () {
  "use strict";

  async function api(path, body, method) {
    const opts = { method: method || (body !== undefined ? "POST" : "GET"), headers: {} };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const r = await fetch(path, opts);
    let data = null;
    try { data = await r.json(); } catch (e) { data = null; }
    if (!r.ok) {
      const msg = (data && data.error) || r.statusText || "Request failed";
      throw new Error(msg);
    }
    return data;
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  const KW = new Set(("procedure function algorithm if else elseif for to downto step while return and or not mod div " +
    "each in then do end repeat until break continue call set by of new").split(" "));
  const LIT = new Set("true false null nil infinity".split(" "));
  const FN = new Set("length floor ceil sqrt abs min max swap print append push pop top len size log".split(" "));
  const TOKEN_RE = /(\/\/.*$)|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|(\b\d+(?:\.\d+)?\b)|([A-Za-z_]\w*)|([\s\S])/gm;

  function highlight(line) {
    let out = "";
    TOKEN_RE.lastIndex = 0;
    let m;
    while ((m = TOKEN_RE.exec(line)) !== null) {
      if (m[0] === "") { TOKEN_RE.lastIndex++; continue; }
      if (m[1]) out += '<span class="tok-com">' + esc(m[1]) + "</span>";
      else if (m[2]) out += '<span class="tok-str">' + esc(m[2]) + "</span>";
      else if (m[3]) out += '<span class="tok-num">' + esc(m[3]) + "</span>";
      else if (m[4]) {
        const w = m[4], lw = w.toLowerCase();
        if (KW.has(lw)) out += '<span class="tok-kw">' + esc(w) + "</span>";
        else if (LIT.has(lw)) out += '<span class="tok-lit">' + esc(w) + "</span>";
        else if (FN.has(lw)) out += '<span class="tok-fn">' + esc(w) + "</span>";
        else out += esc(w);
      } else out += esc(m[5]);
    }
    return out;
  }

  /**
   * Render pseudocode with line numbers.
   * opts: highlights [{lines:[..], label, color}], clickable, onLineClick(n), selected (n),
   *       rowClass {n: "cls"}, startLine
   */
  function renderCode(code, opts) {
    opts = opts || {};
    const lines = String(code || "").split("\n");
    const start = opts.startLine || 1;
    const hlByLine = {};
    (opts.highlights || []).forEach(function (h) {
      h.lines.forEach(function (ln, i) {
        if (!hlByLine[ln]) hlByLine[ln] = { color: h.color, labels: [] };
        if (i === h.lines.length - 1 || h.lines.length === 1) hlByLine[ln].labels.push(h.label);
      });
    });
    const wrap = document.createElement("div");
    wrap.className = "code" + (opts.clickable ? " clickable" : "") + (opts.extraClass ? " " + opts.extraClass : "");
    lines.forEach(function (text, i) {
      const n = i + start;
      const row = document.createElement("div");
      row.className = "row";
      row.dataset.line = n;
      const h = hlByLine[n];
      if (h) row.classList.add("hl" + (h.color % 4));
      if (opts.rowClass && opts.rowClass[n]) row.classList.add(opts.rowClass[n]);
      if (opts.selected === n) row.classList.add("selected");
      row.innerHTML = '<div class="ln">' + n + '</div><div class="src">' + (opts.raw ? text : highlight(text)) + " </div>" +
        '<div class="ann' + (h ? " c" + (h.color % 4) : "") + '">' + (h && h.labels.length ? "← " + esc(h.labels.join("; ")) : "") + "</div>";
      if (opts.clickable) {
        row.addEventListener("click", function () {
          wrap.querySelectorAll(".row.selected").forEach(function (r) { r.classList.remove("selected"); });
          row.classList.add("selected");
          if (opts.onLineClick) opts.onLineClick(n);
        });
      }
      wrap.appendChild(row);
    });
    return wrap;
  }

  function el(tag, attrs, children) {
    const e = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "class") e.className = attrs[k];
        else if (k === "html") e.innerHTML = attrs[k];
        else if (k === "text") e.textContent = attrs[k];
        else if (k.startsWith("on")) e.addEventListener(k.slice(2), attrs[k]);
        else e.setAttribute(k, attrs[k]);
      });
    }
    (children || []).forEach(function (c) {
      if (c == null) return;
      e.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return e;
  }

  function uuid() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      const r = Math.random() * 16 | 0; return (c === "x" ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }

  function toast(msg) {
    const t = el("div", { class: "toast", text: msg });
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 2600);
  }

  function statusLabel(s) {
    return { solved: "solved", missed: "missed", improving: "improving", mastered: "mastered", unseen: "not tried", open: "open" }[s] || s;
  }

  function statusBadge(s) {
    const cls = { solved: "green", mastered: "green", missed: "red", open: "red", improving: "amber" }[s] || "";
    return '<span class="badge ' + cls + '">' + esc(statusLabel(s)) + "</span>";
  }

  window.BT = { api: api, esc: esc, highlight: highlight, renderCode: renderCode, el: el, uuid: uuid, toast: toast,
                statusBadge: statusBadge, statusLabel: statusLabel };
})();
