/* Growth functions and a small dependency-free canvas line chart. */
(function () {
  "use strict";

  function log2(x) { return x > 1 ? Math.log2(x) : 0; }

  // log10 of n! (exact sum for small n, Stirling for large n)
  function log10Fact(n) {
    if (n < 2) return 0;
    if (n <= 5000) { let s = 0; for (let i = 2; i <= n; i++) s += Math.log10(i); return s; }
    return (n * Math.log(n) - n + 0.5 * Math.log(2 * Math.PI * n) + 1 / (12 * n)) / Math.LN10;
  }

  const FUNCS = [
    { key: "1", label: "1", color: "#8b95a5", log10: function () { return 0; } },
    { key: "log n", label: "log n", color: "#4fc48b", log10: function (n) { const v = log2(n); return v > 0 ? Math.log10(v) : -Infinity; } },
    { key: "√n", label: "√n", color: "#7fd1c7", log10: function (n) { return 0.5 * Math.log10(n); } },
    { key: "n", label: "n", color: "#6ea8fe", log10: function (n) { return Math.log10(n); } },
    { key: "n log n", label: "n log n", color: "#b48cf2", log10: function (n) { const v = log2(n); return v > 0 ? Math.log10(n * v) : -Infinity; } },
    { key: "n²", label: "n²", color: "#e6b450", log10: function (n) { return 2 * Math.log10(n); } },
    { key: "n³", label: "n³", color: "#f29e4c", log10: function (n) { return 3 * Math.log10(n); } },
    { key: "2ⁿ", label: "2ⁿ", color: "#f07178", log10: function (n) { return n * Math.log10(2); } },
    { key: "n!", label: "n!", color: "#ff5c8a", log10: function (n) { return log10Fact(n); } },
  ];
  const BY_KEY = {};
  FUNCS.forEach(function (f) { BY_KEY[f.key] = f; });

  function value(key, n) {
    const l = BY_KEY[key].log10(n);
    return l === -Infinity ? 0 : Math.pow(10, l);
  }

  function fmtBig(log10v) {
    if (log10v === -Infinity) return "0";
    if (log10v < 15) {
      const v = Math.pow(10, log10v);
      if (v < 10 && Math.abs(v - Math.round(v)) > 1e-9) return v.toFixed(2);
      return Math.round(v).toLocaleString();
    }
    const e = Math.floor(log10v);
    const m = Math.pow(10, log10v - e);
    return m.toFixed(2) + " × 10^" + e.toLocaleString();
  }

  function fmtTime(log10ops, opsPerSec) {
    const ls = log10ops - Math.log10(opsPerSec || 1e9);
    if (ls === -Infinity) return "instant";
    const s = Math.pow(10, ls);
    if (ls < -6) return "< 1 µs";
    if (s < 1e-3) return (s * 1e6).toFixed(1) + " µs";
    if (s < 1) return (s * 1e3).toFixed(1) + " ms";
    if (s < 60) return s.toFixed(1) + " s";
    if (s < 3600) return (s / 60).toFixed(1) + " min";
    if (s < 86400) return (s / 3600).toFixed(1) + " hours";
    if (s < 3.15e7) return (s / 86400).toFixed(1) + " days";
    const years = ls - Math.log10(3.15e7);
    if (years < 6) return Math.round(Math.pow(10, years)).toLocaleString() + " years";
    return "10^" + Math.floor(years) + " years" + (years > 10.14 ? " (≫ age of the universe)" : "");
  }

  /**
   * series: [{label, color, fn(x) -> y}] ; opts: {xmin, xmax, logY, ymax, xlabel, ylabel, points}
   */
  function drawChart(canvas, series, opts) {
    opts = opts || {};
    const dpr = window.devicePixelRatio || 1;
    const W = canvas.clientWidth || 700, H = canvas.clientHeight || 380;
    canvas.width = W * dpr; canvas.height = H * dpr;
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    const pad = { l: 64, r: 16, t: 14, b: 38 };
    const pw = W - pad.l - pad.r, ph = H - pad.t - pad.b;
    const xmin = opts.xmin || 1, xmax = Math.max(opts.xmax || 20, xmin + 1);
    const steps = Math.min(400, Math.max(40, Math.floor(pw)));
    const logY = !!opts.logY;
    // collect data
    const data = series.map(function (s) {
      const pts = [];
      for (let i = 0; i <= steps; i++) {
        let x = xmin + (xmax - xmin) * i / steps;
        if (s.integer) x = Math.round(x);
        let y = s.fn(x);
        if (!isFinite(y)) y = Number.MAX_VALUE;
        pts.push([x, y]);
      }
      return pts;
    });
    let ymax = opts.ymax;
    if (!ymax) {
      ymax = 1;
      data.forEach(function (pts) { pts.forEach(function (p) { if (p[1] < 1e300) ymax = Math.max(ymax, p[1]); }); });
    }
    const yminLog = 0, ymaxLog = Math.max(1, Math.log10(ymax));
    function ty(y) {
      if (logY) {
        const ly = y <= 1 ? 0 : Math.log10(y);
        return pad.t + ph - Math.min(1.02, (ly - yminLog) / (ymaxLog - yminLog)) * ph;
      }
      return pad.t + ph - Math.min(1.05, y / ymax) * ph;
    }
    function tx(x) { return pad.l + (x - xmin) / (xmax - xmin) * pw; }

    // grid
    ctx.strokeStyle = "#232a35"; ctx.fillStyle = "#6d7684"; ctx.lineWidth = 1;
    ctx.font = "11px " + getComputedStyle(document.body).fontFamily;
    ctx.textAlign = "right"; ctx.textBaseline = "middle";
    const yt = 5;
    for (let i = 0; i <= yt; i++) {
      const frac = i / yt;
      const y = pad.t + ph - frac * ph;
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
      let lab;
      if (logY) lab = "10^" + (yminLog + frac * (ymaxLog - yminLog)).toFixed(ymaxLog > 20 ? 0 : 1);
      else lab = fmtAxis(frac * ymax);
      ctx.fillText(lab, pad.l - 6, y);
    }
    ctx.textAlign = "center"; ctx.textBaseline = "top";
    const xt = 6;
    for (let i = 0; i <= xt; i++) {
      const x = xmin + (xmax - xmin) * i / xt;
      const px = tx(x);
      ctx.beginPath(); ctx.moveTo(px, pad.t); ctx.lineTo(px, pad.t + ph); ctx.stroke();
      ctx.fillText(fmtAxis(x), px, pad.t + ph + 6);
    }
    if (opts.xlabel) { ctx.fillText(opts.xlabel, pad.l + pw / 2, H - 14); }

    // lines
    ctx.save();
    ctx.beginPath(); ctx.rect(pad.l, pad.t - 2, pw, ph + 4); ctx.clip();
    series.forEach(function (s, si) {
      ctx.strokeStyle = s.color; ctx.lineWidth = s.width || 2.2;
      ctx.beginPath();
      data[si].forEach(function (p, i) {
        const X = tx(p[0]), Y = Math.max(pad.t - 50, ty(p[1]));
        if (i === 0) ctx.moveTo(X, Y); else ctx.lineTo(X, Y);
      });
      ctx.stroke();
    });
    ctx.restore();
    // labels at the right edge / top
    ctx.textAlign = "left"; ctx.textBaseline = "middle"; ctx.font = "bold 11px " + getComputedStyle(document.body).fontFamily;
    series.forEach(function (s, si) {
      const pts = data[si];
      let last = pts[pts.length - 1];
      for (let i = 0; i < pts.length; i++) { if (ty(pts[i][1]) < pad.t) { last = pts[Math.max(0, i - 1)]; break; } }
      const X = Math.min(tx(last[0]) + 4, W - pad.r - 40), Y = Math.max(pad.t + 6, Math.min(pad.t + ph - 6, ty(last[1])));
      ctx.fillStyle = s.color; ctx.fillText(s.label, X, Y);
    });
    if (opts.marker) {
      ctx.strokeStyle = "#e4e8ee"; ctx.setLineDash([4, 4]);
      const X = tx(opts.marker);
      ctx.beginPath(); ctx.moveTo(X, pad.t); ctx.lineTo(X, pad.t + ph); ctx.stroke(); ctx.setLineDash([]);
    }
  }

  function fmtAxis(v) {
    if (v === 0) return "0";
    if (Math.abs(v) >= 1e6) return v.toExponential(1).replace("e+", "e");
    if (Math.abs(v) >= 1000) return Math.round(v).toLocaleString();
    if (Math.abs(v) < 10 && v % 1) return v.toFixed(1);
    return String(Math.round(v));
  }

  window.Growth = { FUNCS: FUNCS, BY_KEY: BY_KEY, value: value, fmtBig: fmtBig, fmtTime: fmtTime, drawChart: drawChart, log10Fact: log10Fact };
})();
