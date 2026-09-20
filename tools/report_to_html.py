#!/usr/bin/env python3
"""Render REPORT.md (and the executive summary) as standalone, self-contained HTML.

One input -> one output, no template files, no network: CSS, figures and the Plotly
runtime are all embedded, so each page works from a file:// URL, an email attachment,
or any static server.

Figure callouts
---------------
The reports carry figures as blockquote "callouts":

    > **Figure 3.1b — Title** *(interactive — toggle the key ...)*
    >
    > How to read: ...
    >
    > ![alt text](analysis/figures/fig_true_gold_pareto.png)
    >
    > **Takeaway:** ...

This renderer turns each into a styled <figure class="callout"> card:

* *(interactive ...)* -> a live Plotly chart built from
  `analysis/figures/interactive/<base>.json` (legend keys toggle series, the CI
  toggle redraws error bars), with a static SVG fallback inside <details> for
  readers without JavaScript;
* *(static figure)* -> the vector SVG inlined as a base64 data URI.

Markdown remains the source of truth: the Markdown files are what the chain and the
checksum set cover; this tool only renders them. Run it after regenerating figures:

    .venv/bin/python tools/report_to_html.py
"""
from __future__ import annotations

import base64
import html
import json
import re
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
FIGDIR = ROOT / "analysis/figures"
INTERACTIVE = FIGDIR / "interactive"
PLOTLY_JS = FIGDIR / "vendor_plotly.min.js"

CSS = """
:root { color-scheme: light; --ink:#16191d; --ink2:#3f4650; --muted:#6b7280; --accent:#0b5cad; --accent-wash:#eaf2fb;
  --rule:#e3e6ea; --rule-strong:#c9cfd6; --bg:#fcfcfd; --surface:#ffffff; --tint:#f6f7f9;
  --measure:54rem;   /* prose measure; tables, figures and folds may use the full content width */ }
* { box-sizing:border-box; }
/* Type and layout scale with the viewport: 16px on a laptop, ~24px on a 2560px-wide display, 26px max. */
html { font-size:clamp(16px, 0.7vw + 6px, 26px); scroll-behavior:smooth; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior:auto; } }
body { margin:0; background:var(--bg); color:var(--ink); line-height:1.6;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; font-size:1rem; }
.page { max-width:86rem; margin:0 auto; padding:0 1.5rem 5rem; }
main { min-width:0; }
@media (max-width: 700px) { .page { padding:0 14px 4rem; } }

/* ---- navigation: a sticky sidebar on wide screens, a collapsible list above the text otherwise ---- */
details.toc > summary { list-style:none; } details.toc > summary::-webkit-details-marker { display:none; }
@media (min-width: 1180px) {
  .page { display:grid; grid-template-columns:17rem minmax(0, 1fr); column-gap:2.75rem; }
  details.toc { position:sticky; top:0; align-self:start; max-height:100vh; overflow-y:auto; padding:2.2rem 8px 2rem 0;
    font-size:.86rem; scrollbar-width:thin; }
  details.toc > summary { display:none; }
}
@media (max-width: 1179px) {
  details.toc { margin:1.4rem 0 .4rem; border:1px solid var(--rule); border-radius:10px; background:var(--surface); padding:0 14px; font-size:.92rem; }
  details.toc > summary { cursor:pointer; padding:10px 0; font-weight:700; }
  details.toc > summary::before { content:"▸ "; color:var(--muted); } details.toc[open] > summary::before { content:"▾ "; }
  nav.toc .toc-head { display:none; }
  nav.toc .toc-body { padding-bottom:10px; }
}
nav.toc .toc-head { font-size:.72rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:0 0 .5rem; }
nav.toc ul { list-style:none; margin:0; padding:0; }
nav.toc ul ul { margin:.1rem 0 .3rem .8rem; border-left:1px solid var(--rule); padding-left:.7rem; }
nav.toc li { margin:0; }
nav.toc a { display:block; color:var(--ink2); padding:.22rem 0; line-height:1.35; text-decoration:none; border-left:2px solid transparent; margin-left:-2px; }
nav.toc ul ul a { color:var(--muted); font-size:.95em; }
nav.toc a:hover { color:var(--ink); text-decoration:none; }
nav.toc a.active { color:var(--accent); font-weight:600; }
nav.toc .toc-links { margin-top:1rem; padding-top:.8rem; border-top:1px solid var(--rule); }
nav.toc .toc-links a { color:var(--accent); }

/* ---- prose measure and headings ---- */
/* Prose is centred in the content column; tables, figure cards and folds span it, breaking out symmetrically. */
main > p, main > ul, main > ol, main > blockquote, main > h1, main > h2, main > h3, main > h4, main > pre, main > .meta,
main > .generated, main > footer { max-width:var(--measure); margin-left:auto; margin-right:auto; }
h1,h2,h3,h4 { line-height:1.22; font-weight:700; letter-spacing:-.012em; scroll-margin-top:1rem; color:var(--ink); text-wrap:balance; }
h1 { font-size:2.05rem; letter-spacing:-.022em; margin:2.6rem 0 .9rem; }
h2 { font-size:1.5rem; margin:3.2rem 0 .9rem; padding-top:1.2rem; border-top:1px solid var(--rule-strong); }
h3 { font-size:1.17rem; margin:2.1rem 0 .6rem; }
h4 { font-size:.98rem; margin:1.6rem 0 .5rem; color:var(--ink2); }
h1 a.toclink, h2 a.toclink, h3 a.toclink, h4 a.toclink { color:inherit; }
p { margin:0 0 1rem; }
a { color:var(--accent); text-decoration:none; }
a:hover { text-decoration:underline; }
.meta { display:flex; flex-wrap:wrap; gap:.35rem .5rem; align-items:center; margin:0 0 1.6rem; font-size:.86rem; color:var(--muted); }
.meta a { display:inline-block; padding:.28rem .7rem; border:1px solid var(--rule); border-radius:999px; background:var(--surface); color:var(--ink2); }
.meta a:hover { border-color:var(--rule-strong); color:var(--ink); text-decoration:none; }
.meta a.primary { background:var(--accent); border-color:var(--accent); color:#fff; }
code, pre { font:.82rem/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }
code { background:var(--tint); padding:.1em .35em; border-radius:4px; }
pre { background:var(--tint); border:1px solid var(--rule); border-radius:8px; padding:.9rem 1.1rem; overflow-x:auto; }
pre code { background:none; padding:0; }
blockquote { margin:1.2rem 0; padding:.2rem 0 .2rem 1.1rem; border-left:3px solid var(--rule-strong); color:var(--ink2); }
blockquote p:last-child { margin-bottom:0; }
hr { border:none; border-top:1px solid var(--rule); margin:2rem 0; }
ul, ol { padding-left:1.4rem; } li { margin:.25rem 0; }

/* ---- tables: horizontal rules only, numbers right-aligned in tabular figures ---- */
table { border-collapse:collapse; margin:1.2rem 0 1.4rem; width:100%; font-size:.88rem; display:block; overflow-x:auto;
  font-variant-numeric:tabular-nums; }
th, td { padding:.45rem .7rem; text-align:left; vertical-align:top; border-bottom:1px solid var(--rule); white-space:nowrap; }
th { font-size:.74rem; letter-spacing:.04em; text-transform:uppercase; color:var(--muted); font-weight:700;
  border-bottom:1px solid var(--rule-strong); background:var(--surface); }
td.num, th.num { text-align:right; }
tbody tr:hover td { background:var(--tint); }

details.fold { margin:1.1rem 0; border:1px solid var(--rule); border-radius:10px; background:var(--surface); }
details.fold > summary { cursor:pointer; padding:.65rem .95rem; font-weight:600; color:var(--ink); list-style:none; user-select:none; }
details.fold > summary::-webkit-details-marker { display:none; }
details.fold > summary::before { content:"▸ "; color:var(--muted); }
details.fold[open] > summary::before { content:"▾ "; }
details.fold[open] > summary { border-bottom:1px solid var(--rule); }
details.fold .fold-body { padding:.4rem .95rem .9rem; }
details.fold table { margin:.4rem 0; }
.generated { color:var(--muted); font-size:.85em; border:1px solid var(--rule); border-radius:8px; padding:.5rem .9rem; background:var(--tint); }
footer { margin-top:4rem; color:var(--muted); font-size:.85em; border-top:1px solid var(--rule); padding-top:1rem; }

/* ---- figure callout cards ---- */
figure.callout { margin:2rem 0; padding:1.1rem 1.2rem 1.2rem; background:var(--surface);
  border:1px solid var(--rule); border-radius:12px; box-shadow:0 1px 2px rgba(16,24,40,.04), 0 6px 20px rgba(16,24,40,.04); }
figure.callout .fig-title { margin:0 0 .5rem; font-size:1.02rem; color:var(--ink); font-weight:700; }
.fig-badge { display:inline-block; margin-left:.5rem; vertical-align:1px; padding:.1em .55em; font-size:.72em; font-weight:700;
  letter-spacing:.03em; text-transform:uppercase; border-radius:999px; border:1px solid; }
.fig-badge-interactive { color:#0b5cad; border-color:#9dc2e6; background:#eaf3fb; }
.fig-badge-static { color:#5b6472; border-color:#d9dee5; background:#f4f6f8; }
.fig-how { margin:.35rem auto .9rem; color:var(--muted); font-style:italic; font-size:.93em; max-width:var(--measure); }
.fig-body { margin:.4rem 0 .9rem; }
.fig-body img { width:100%; max-width:100%; height:auto; display:block; margin:0 auto; }
.plotly-fig { width:100%; height:clamp(480px, 62vh, 900px); }
.fig-controls { margin:.2rem 0 .5rem; font-size:.85em; color:var(--muted); }
.fig-controls label { cursor:pointer; user-select:none; }

/* ---- per-figure key box (model / harness / effort / CI), mirrors the dashboard's docked filter box ---- */
.fig-key { margin:.2rem 0 .6rem; }
.fig-key .key-sentinel { display:block; height:1px; }
.fig-key .key-panel { position:sticky; top:0; z-index:5; border:1px solid var(--rule); border-radius:9px; background:var(--surface);
  padding:.5rem .7rem .55rem; transition: padding .3s ease, box-shadow .3s ease, border-radius .3s ease; }
.fig-key.docked .key-panel { padding:.25rem .55rem .3rem; box-shadow:0 2px 10px rgba(16,24,40,.10); border-radius:0 0 9px 9px; }
.fig-key .key-head { font-size:.78em; font-weight:700; letter-spacing:.03em; text-transform:uppercase; color:var(--muted); margin:0 0 .2rem;
  transition:font-size .3s ease; }
.fig-key.docked .key-head { font-size:.68em; margin-bottom:.1rem; }
.fig-key .key-note { color:var(--muted); font-size:.82em; margin:.1rem 0 .35rem; }
.fig-key.docked .key-note { display:none; }
.fig-key .key-groups { display:block; }
.fig-key .key-group { display:flex; flex-wrap:wrap; align-items:baseline; gap:.1rem .85rem; margin:.1rem 0; }
.fig-key .key-title { flex:0 0 auto; min-width:6.4rem; font-size:.72em; font-weight:700; text-transform:uppercase; letter-spacing:.03em; color:var(--muted); }
.fig-key label { display:inline-flex; align-items:center; gap:.28rem; font-size:.85em; color:var(--ink); white-space:nowrap; }
.fig-key .key-title .key-all { font-weight:400; text-transform:none; letter-spacing:0; }
.fig-key input[type=checkbox] { vertical-align:-1px; margin-right:.15rem; }
.fig-key input[type=checkbox]:focus-visible { outline:2px solid var(--accent); outline-offset:1px; }
.fig-key a.key-all { color:var(--accent); }
@media (max-width: 760px) { .plotly-fig { height:460px; } }
.fig-fallback { margin-top:.6rem; }
.fig-fallback summary { cursor:pointer; color:var(--muted); font-size:.85em; }
.fig-fallback img { margin-top:.6rem; }
figcaption.fig-takeaway { margin:.4rem auto 0; padding-left:.8rem; border-left:3px solid var(--rule-strong); font-size:.95em; max-width:var(--measure); }
figcaption.fig-takeaway strong { color:var(--ink); }
@media print { figure.callout { break-inside:avoid; } .fig-fallback { display:block; } nav.toc { display:none; } .page { display:block; } }
"""

BODY_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
{plotly}
</head>
<body>
<div class="page">
{toc}
<main>
{body}
{footer}
<p class="generated">This page is a generated HTML rendering of <code>{src}</code> —
the Markdown file is the source of truth. Generated by
<code>tools/report_to_html.py</code>{tagline}. Figures are regenerated renderings;
the interactive charts carry the same data as the
<a href="analysis/figures/interactive_dashboard.html">interactive dashboard</a>.</p>
</main>
</div>
{navscript}
{boot}
</body>
</html>
"""

FOOTER = (
    "Automated code review evaluation — corrected September 2026 report. "
    'Developer edition: <a href="sdlc-report.html">sdlc-report.html</a> · '
    'Charts: <a href="analysis/figures/interactive_dashboard.html">interactive dashboard</a> · '
    'PNGs in <a href="analysis/figures/">analysis/figures/</a> · '
    '<a href="EXECUTIVE_SUMMARY.html">executive summary (HTML)</a> / '
    '<a href="REPORT.html">full report (HTML)</a>. '
    "Disclosure: the author maintains <b>metareview</b> (MRV), one of the harnesses evaluated "
    "in this report — open source, MIT licensed, available free of charge at "
    '<a href="https://github.com/dsifry/metareview">github.com/dsifry/metareview</a>.'
)

# Links shown under each document's title. The developer edition is the short, practitioner-facing cut.
HEADER_LINKS = {
    "REPORT.md": [
        ("sdlc-report.html", "Developer edition", True),
        ("EXECUTIVE_SUMMARY.html", "Executive summary", False),
        ("SLIDES.html", "Slides", False),
        ("#235-author-interest-disclosure-metareview", "Author disclosure", False),
        ("#5-reproducibility", "Reproduce it", False),
        ("https://github.com/dsifry/harnesseval", "Data and code", False),
    ],
    "EXECUTIVE_SUMMARY.md": [
        ("sdlc-report.html", "Developer edition", True),
        ("REPORT.html", "Full report", False),
        ("SLIDES.html", "Slides", False),
        ("https://github.com/dsifry/harnesseval", "Data and code", False),
    ],
}

_NUMERIC_CELL = re.compile(
    r"^\s*(?:[-−+]?\$?\d[\d,]*(?:\.\d+)?%?×?|[-−+]?\.\d+|—|–|n/?a)"
    r"(?:\s*(?:\[[^\]]*\]|\([^)]*\)|/\s*\d+|[-−–]\s*[\d.]+))?\s*[×%*†]?\s*$", re.I)


def header_links_html(links: list[tuple[str, str, bool]]) -> str:
    return '<p class="meta">' + " ".join(
        f'<a href="{href}"{" class=\"primary\"" if primary else ""}>{html.escape(label)}</a>'
        for href, label, primary in links) + "</p>"


def toc_html(tokens: list[dict], links: list[tuple[str, str, bool]], max_level: int = 3) -> str:
    """Sidebar navigation from the toc extension's heading tree (h2/h3), plus the sibling-document links."""
    def items(toks: list[dict]) -> str:
        out = []
        for tk in toks:
            if tk["level"] < 2 or tk["level"] > max_level:
                out.append(items(tk.get("children", [])))
                continue
            kids = items([c for c in tk.get("children", []) if c["level"] <= max_level])
            out.append(f'<li><a href="#{tk["id"]}">{tk["name"]}</a>{f"<ul>{kids}</ul>" if kids else ""}</li>')
        return "".join(out)
    body = items(tokens)
    if not body:
        return ""
    extra = "".join(f'<a href="{href}">{html.escape(label)}</a><br>' for href, label, _ in links if not href.startswith("#"))
    return (f'<details class="toc" open><summary>On this page</summary><nav class="toc"><div class="toc-body">'
            f'<p class="toc-head">On this page</p><ul>{body}</ul>'
            f'<div class="toc-links">{extra}</div></div></nav></details>')


def mark_numeric_cells(body: str) -> str:
    """Right-align table cells that hold a number (optionally with a CI, a fraction, or a unit)."""
    def fix(m: re.Match) -> str:
        plain = html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
        return f'<td class="num">{m.group(1)}</td>' if _NUMERIC_CELL.match(plain) else m.group(0)
    return re.sub(r"<td>(.*?)</td>", fix, body, flags=re.S)


NAV_SCRIPT = """<script>
(function () {
  var links = Array.prototype.slice.call(document.querySelectorAll('nav.toc a[href^="#"]'));
  if (!links.length) return;
  var byId = {}; links.forEach(function (a) { byId[a.getAttribute('href').slice(1)] = a; });
  var heads = Object.keys(byId).map(function (id) { return document.getElementById(id); }).filter(Boolean);
  var current = null, ticking = false;
  function activate(id) {
    if (current === id) return; current = id;
    links.forEach(function (a) { a.classList.toggle('active', a.getAttribute('href') === '#' + id); });
    var a = byId[id], box = a && a.closest('details.toc');
    if (a && box && box.scrollHeight > box.clientHeight) {
      var r = a.getBoundingClientRect(), n = box.getBoundingClientRect();
      if (r.top < n.top + 40 || r.bottom > n.bottom - 40) box.scrollTop += r.top - n.top - n.height / 2;
    }
  }
  function update() {
    ticking = false;
    var pick = null;  /* the last heading that has scrolled past the top band; else the first one */
    for (var i = 0; i < heads.length; i++) { if (heads[i].getBoundingClientRect().top <= 140) pick = heads[i]; else break; }
    activate((pick || heads[0]).id);
  }
  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  window.addEventListener('load', update);
  update();
  var mq = window.matchMedia('(max-width: 1179px)'), det = document.querySelector('details.toc');
  function fold() { if (det) det.open = !mq.matches; }
  fold(); mq.addEventListener ? mq.addEventListener('change', fold) : mq.addListener(fold);
})();
</script>"""


# Per-figure height overrides (CSS height values). Dense charts need more vertical room than the default.
FIG_HEIGHTS = {
    "fig_true_gold_pareto": "clamp(560px, 70vh, 1040px)",
    "fig_true_gold_defects_found": "clamp(520px, 64vh, 960px)",
    "fig_pareto_frontier": "clamp(560px, 68vh, 1000px)",
}

_BOOT_SCRIPT = """<script>
(function () {
  var figs = Array.prototype.slice.call(document.querySelectorAll('div.plotly-fig'));
  if (!figs.length) return;

  function fallbackFor(el) {
    var b = el.closest ? el.closest('.fig-body') : null;
    return b ? b.querySelector('details.fig-fallback') : null;
  }

  /* ---- cell extraction: mirrors report_to_html.py _point_cell / _label_cell ---- */
  var LABEL_RE = /^([^·]+)·([^·]+)·([lmh])[ ]*†?$/;
  function cellOf(cd, x) {
    if (typeof cd === 'string') {
      var p = cd.split('|');
      if (p.length >= 3) return { m: p[0], fw: p[1], e: p[2] };
    } else if (Array.isArray(cd)) {
      if (cd.length && typeof cd[0] === 'string') {
        var q = cd[0].split('|');
        if (q.length >= 3) return { m: q[0], fw: q[1], e: q[2] };
      } else if (cd.length && cd[0] && typeof cd[0] === 'object') {
        var r = cd[0], m0 = r.model || r.m, f0 = r.fw || r.fwFull, e0 = r.eff || r.e;
        if (m0 && f0 && e0) return { m: m0, fw: f0, e: e0 };
      }
    } else if (cd && typeof cd === 'object') {
      var m1 = cd.model || cd.m, f1 = cd.fw || cd.fwFull, e1 = cd.eff || cd.e;
      if (m1 && f1 && e1) return { m: m1, fw: f1, e: e1 };
    }
    if (typeof x === 'string') {
      var t = LABEL_RE.exec(x.trim());
      if (t) return { m: t[1], fw: t[2], e: t[3] };
    }
    return null;
  }

  function copy(o) { return JSON.parse(JSON.stringify(o)); }

  /* Line traces carry no cell metadata of their own: index every point that HAS a cell by its (x,y)
     coordinates, so a connecting line can be broken wherever the key hides the cell it runs through. */
  function coordKey(x, y) {
    var fx = (typeof x === 'number') ? x.toPrecision(12) : String(x);
    var fy = (typeof y === 'number') ? y.toPrecision(12) : String(y);
    return fx + '|' + fy;
  }

  function passes(c, st) {
    return st.model[c.m] !== false && st.fw[c.fw] !== false && st.eff[c.e] !== false;
  }

  function buildCoordIndex(traces) {
    var idx = {};
    traces.forEach(function (t) {
      var cd = t.customdata || [], xs = t.x || [], ys = t.y || [];
      if (!cd.length) { return; }
      for (var i = 0; i < xs.length; i++) {
        var c = cellOf(cd[i], xs[i]);
        if (!c) { continue; }
        var k = coordKey(xs[i], ys[i]);
        (idx[k] || (idx[k] = [])).push(c);
      }
    });
    return idx;
  }

  /* Hide the points the key says to hide.
     Removed points are DROPPED from the array, not nulled: a line then connects its remaining
     neighbours, so unticking "medium" leaves a low-to-high line (and if low or high goes too, the
     line simply shrinks or disappears). Traces with no cell information at all are left untouched. */
  function maskedTraces(traces, st) {
    var idx = buildCoordIndex(traces);
    return traces.map(function (t) {
      var xsrc = t.x || [], cd = t.customdata || [], ysrc = t.y || [];
      var hasCd = cd.length > 0, hasText = Array.isArray(t.text);
      var hasEx = !!(t.error_x && t.error_x.array), hasExm = !!(t.error_x && t.error_x.arrayminus);
      var hasEy = !!(t.error_y && t.error_y.array), hasEym = !!(t.error_y && t.error_y.arrayminus);
      var out = copy(t), any = false, kept = 0;
      var xs = [], ys = [], cds = [], txs = [], ex = [], exm = [], ey = [], eym = [];
      for (var i = 0; i < xsrc.length; i++) {
        var c = cellOf(hasCd ? cd[i] : null, xsrc[i]);
        var pass = true;
        if (c) {
          any = true;
          pass = passes(c, st);
        } else if (ysrc.length) {
          // no metadata on this point (e.g. a connecting line): resolve it by coordinates
          var hit = idx[coordKey(xsrc[i], ysrc[i])];
          if (hit && hit.length) { any = true; pass = hit.some(function (h) { return passes(h, st); }); }
        }
        if (!pass) { continue; }
        kept++;
        xs.push(xsrc[i]);
        if (ysrc.length) ys.push(ysrc[i]);
        if (hasCd) cds.push(cd[i]);
        if (hasText) txs.push(t.text[i]);
        if (hasEx) ex.push(t.error_x.array[i]);
        if (hasExm) exm.push(t.error_x.arrayminus[i]);
        if (hasEy) ey.push(t.error_y.array[i]);
        if (hasEym) eym.push(t.error_y.arrayminus[i]);
      }
      if (!any) { return out; }               // no cell information: leave the trace alone
      out.x = xs;
      if (ysrc.length) out.y = ys;
      if (hasCd) out.customdata = cds;
      if (hasText) out.text = txs;
      if (hasEx) out.error_x.array = ex;
      if (hasExm) out.error_x.arrayminus = exm;
      if (hasEy) out.error_y.array = ey;
      if (hasEym) out.error_y.arrayminus = eym;
      if (kept === 0) out.visible = false;
      return out;
    });
  }

  function boot() {
    var keys = Array.prototype.slice.call(document.querySelectorAll('.fig-key'));
    if (!window.Plotly) {
      // No runtime: the key box and the empty container go away; the static fallback stands alone.
      keys.forEach(function (k) { k.style.display = 'none'; });
      figs.forEach(function (el) {
        el.style.display = 'none';
        var fb = fallbackFor(el);
        if (fb) { fb.open = true; }
      });
      return;
    }

    figs.forEach(function (el) {
      var base = el.id.replace(/^fig-/, '');
      var raw = document.getElementById('data-' + base);
      if (!raw) { return; }
      try {
        var spec = JSON.parse(raw.textContent);
        var ciRaw = document.getElementById('data-' + base + '-ci');
        var ciSpec = ciRaw ? JSON.parse(ciRaw.textContent) : null;
        [spec, ciSpec].forEach(function (sp) {
          if (!sp) return;
          sp.layout = sp.layout || {};
          sp.layout.pop && sp.layout.pop('updatemenus');
          delete sp.layout.updatemenus;
          delete sp.layout.width; delete sp.layout.height;
        });
        var cfg = spec.config || {}; cfg.responsive = true; cfg.displayModeBar = false;

        // filter state: value -> checked? (absent = checked)
        var st = { model: {}, fw: {}, eff: {}, ci: false };
        Array.prototype.forEach.call(
          document.querySelectorAll('.key-filter[data-fig="' + base + '"]'),
          function (b) { st[b.getAttribute('data-kind')][b.value] = b.checked; });

        function draw() {
          var chosen = (st.ci && ciSpec) ? ciSpec : spec;
          return window.Plotly.react(el, maskedTraces(chosen.traces, st), chosen.layout || {}, cfg);
        }
        draw().then(function () {
          var fb = fallbackFor(el);
          if (fb) { fb.open = false; }
        });

        Array.prototype.forEach.call(
          document.querySelectorAll('.key-filter[data-fig="' + base + '"]'),
          function (b) {
            b.addEventListener('change', function () {
              st[b.getAttribute('data-kind')][b.value] = b.checked;
              draw();
            });
          });
        Array.prototype.forEach.call(
          document.querySelectorAll('a.key-all[data-fig="' + base + '"]'),
          function (a) {
            a.addEventListener('click', function (ev) {
              ev.preventDefault();
              var kind = a.getAttribute('data-kind'), on = a.getAttribute('data-mode') === 'all';
              Array.prototype.forEach.call(
                document.querySelectorAll('input.key-filter[data-fig="' + base + '"][data-kind="' + kind + '"]'),
                function (b) { b.checked = on; st[kind][b.value] = on; });
              draw();
            });
          });
        var ciBox = document.querySelector('input.ci-toggle[data-fig="' + base + '"]');
        if (ciBox) {
          ciBox.addEventListener('change', function () { st.ci = ciBox.checked; draw(); });
        }
      } catch (e) {
        console.error('figure render failed:', el.id, e);
        el.style.display = 'none';
        var kb = document.querySelector('.fig-key[data-fig="' + base + '"]');
        if (kb) { kb.style.display = 'none'; }
        var fb2 = fallbackFor(el);
        if (fb2) { fb2.open = true; }
      }
    });

    /* docking animation: once the key box scrolls past the top it shrinks and pins (dashboard behaviour) */
    keys.forEach(function (box) {
      var sentinel = box.querySelector('.key-sentinel');
      if (sentinel && 'IntersectionObserver' in window) {
        new IntersectionObserver(function (entries) {
          box.classList.toggle('docked', !entries[0].isIntersecting);
        }, { rootMargin: '-4px 0px 0px 0px', threshold: 0 }).observe(sentinel);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
</script>"""


# --------------------------------------------------------------------------- collapsibles

COLLAPSE_OPEN = re.compile(r"^<!--\s*collapsible:\s*(?P<summary>.*?)\s*-->\s*$")
COLLAPSE_CLOSE = re.compile(r"^<!--\s*/collapsible\s*-->\s*$")


def split_collapsibles(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Replace each <!-- collapsible: X --> … <!-- /collapsible --> block with a placeholder.

    The block renders markdown normally (so the table is visible on GitHub); in the HTML the
    wrapped content becomes a <details> closed by default, with X as its summary.
    """
    out: list[str] = []
    blocks: list[tuple[str, str]] = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = COLLAPSE_OPEN.match(lines[i])
        if not m:
            out.append(lines[i]); i += 1; continue
        summary = m.group("summary")
        inner: list[str] = []
        i += 1
        while i < len(lines) and not COLLAPSE_CLOSE.match(lines[i]):
            inner.append(lines[i]); i += 1
        i += 1  # skip the close marker
        blocks.append((summary, "\n".join(inner).strip("\n")))
        out.append("")
        out.append(f"@@COLLAPSEBLOCK_{len(blocks) - 1}@@")
        out.append("")
    return "\n".join(out), blocks


# --------------------------------------------------------------------------- callouts

def split_callouts(text: str) -> tuple[str, list[list[str]]]:
    """Replace each `> **Figure ...` blockquote with a placeholder paragraph."""
    lines = text.split("\n")
    out: list[str] = []
    blocks: list[list[str]] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("> **Figure "):
            blk: list[str] = []
            while i < len(lines):
                cur = lines[i]
                if cur.startswith(">"):
                    blk.append(cur)
                    i += 1
                elif cur.strip() == "" and i + 1 < len(lines) and lines[i + 1].startswith(">"):
                    blk.append(cur)
                    i += 1
                else:
                    break
            blocks.append(blk)
            out.append("")
            out.append(f"@@FIGCALLOUT_{len(blocks) - 1}@@")
            out.append("")
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out), blocks


def _paragraphs(blk: list[str]) -> list[str]:
    paras: list[str] = []
    cur: list[str] = []
    for raw in blk:
        body = raw[1:].lstrip() if raw.startswith(">") else raw.strip()
        if body.strip() == "":
            if cur:
                paras.append(" ".join(cur).strip())
                cur = []
        else:
            cur.append(body.strip())
    if cur:
        paras.append(" ".join(cur).strip())
    return paras


TITLE_RE = re.compile(r"^\*\*(?P<title>.+?)\*\*\s*(?:\*\((?P<marker>[^*]*)\)\*)?\s*$")
IMG_RE = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)\s*$")


def _inline(md_renderer: markdown.Markdown, text: str) -> str:
    return md_renderer.convert(text).strip()


def _strip_p(html: str) -> str:
    m = re.match(r"^<p>(?P<inner>.*)</p>$", html, flags=re.S)
    return m.group("inner") if m else html


def _data_uri(path: Path) -> str:
    mime = {"svg": "image/svg+xml", "png": "image/png"}.get(path.suffix.lstrip("."), "application/octet-stream")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _fig_asset(base: str, prefer_svg: bool = True) -> Path | None:
    order = ["svg", "png"] if prefer_svg else ["png", "svg"]
    for ext in order:
        p = FIGDIR / f"{base}.{ext}"
        if p.exists():
            return p
    return None


# --------------------------------------------------------------- per-figure key box

# readable labels (mirrors the dashboard's M_SHORT / framework names)
MODEL_SHORT = {
    "claude-fable-5-1": "fable-5.1", "gpt-6-astra": "astra", "gpt-5.6-sol": "sol",
    "claude-opus-5": "opus", "glm-5.3-vision-background": "glm-vis",
    "gpt-5.6-terra": "terra", "claude-sonnet-5": "sonnet",
    "glm-5.3-flash-background": "glm-flash",
}
FW_LABEL = {
    "vanilla-engineered": "vanilla (one-shot)", "compound-realistic": "compound (CE)",
    "metareview-realistic": "metareview (MRV)",
    "van": "vanilla (one-shot)", "CE": "compound (CE)", "MRV": "metareview (MRV)",
}
EFF_LABEL = {"low": "low", "medium": "medium", "high": "high",
             "l": "low", "m": "medium", "h": "high"}

# some figures encode the cell in the x-axis label instead of customdata: "model·fw·eff†"
LABEL_CELL_RE = re.compile(r"^([^·]+)·([^·]+)·([lmh])\s*†?$")


def _point_cell(cd):
    """Extract (model, fw, eff) from one point's customdata, in any of the shapes the fragments use.

    (a) dict  {"model":…, "fw":…, "eff":…}   (dashboard panels)
    (b) list  ["model|fw|eff", …]            (rebuilt true-gold charts)
    (c) scalar/None -> None                  (aggregate charts; also hover-label strings)
    """
    if cd is None:
        return None
    if isinstance(cd, str):
        parts = cd.split("|")
        return tuple(parts[:3]) if len(parts) >= 3 else None
    if isinstance(cd, list):
        if cd and isinstance(cd[0], str):
            parts = cd[0].split("|")
            return tuple(parts[:3]) if len(parts) >= 3 else None
        if cd and isinstance(cd[0], dict):
            return _point_cell(cd[0])
        return None
    if isinstance(cd, dict):
        m = cd.get("model") or cd.get("m")
        fw = cd.get("fw") or cd.get("fwFull")
        e = cd.get("eff") or cd.get("e")
        if m and fw and e:
            return (m, fw, e)
    return None


def _label_cell(label):
    """Fallback: charts that print the cell as an axis label ("glm-vis·CE·m")."""
    if not isinstance(label, str):
        return None
    m = LABEL_CELL_RE.match(label.strip())
    return (m.group(1), m.group(2), m.group(3)) if m else None


def scan_figure_cells(spec: dict):
    """Return ({model: label}, {fw: label}, {eff: label}) for the cells present in one fragment."""
    models: dict[str, str] = {}
    fws: dict[str, str] = {}
    effs: dict[str, str] = {}
    for t in spec.get("traces", []):
        cds = t.get("customdata") or []
        xs = t.get("x") or []
        for i in range(len(xs)):
            cd = cds[i] if i < len(cds) else None
            cell = _point_cell(cd)
            if cell is None:
                cell = _label_cell(xs[i])
            if cell is None:
                continue
            m, fw, e = cell
            mlab = model_label(cd) or MODEL_SHORT.get(m, m)
            flab = fw_label_from(cd) or FW_LABEL.get(fw, fw)
            models.setdefault(m, mlab)
            fws.setdefault(fw, flab)
            effs.setdefault(e, EFF_LABEL.get(e, e))
    return models, fws, effs


def model_label(cd):
    if isinstance(cd, dict):
        return cd.get("modelShort") or cd.get("mshort")
    if isinstance(cd, list) and cd and isinstance(cd[0], dict):
        return cd[0].get("modelShort") or cd[0].get("mshort")
    return None


def fw_label_from(cd):
    if isinstance(cd, dict):
        return FW_LABEL.get(cd.get("fwShort") or "")
    if isinstance(cd, list) and cd and isinstance(cd[0], dict):
        return FW_LABEL.get(cd[0].get("fwShort") or "")
    return None


def _key_group(base: str, kind: str, title: str, items: dict[str, str]) -> str:
    if not items:
        return ""
    boxes = "".join(
        f'<label><input type="checkbox" class="key-filter" data-fig="{base}" data-kind="{kind}" '
        f'value="{html.escape(v)}" checked> {html.escape(lab)}</label>'
        for v, lab in items.items()
    )
    return (f'<div class="key-group"><span class="key-title">{title} '
            f'<a href="#" class="key-all" data-fig="{base}" data-kind="{kind}" data-mode="all">all</a>/'
            f'<a href="#" class="key-all" data-fig="{base}" data-kind="{kind}" data-mode="none">none</a>'
            f'</span>{boxes}</div>')


def key_box_html(base: str, spec: dict, has_ci: bool) -> str:
    models, fws, effs = scan_figure_cells(spec)
    groups = (_key_group(base, "model", "Models", models)
              + _key_group(base, "fw", "Harness", fws)
              + _key_group(base, "eff", "Effort", effs))
    ci = (f'<div class="key-group key-ci"><label><input type="checkbox" class="ci-toggle" '
          f'data-fig="{base}"> show 95% CIs</label></div>') if has_ci else ""
    if not groups and not ci:
        return ""                                  # nothing to control on this chart
    note = ("Filter this chart: untick a model, harness or effort to drop its points."
            if groups else "This chart has no per-cell series; the 95% CI toggle below applies.")
    return (
        f'<div class="fig-key" data-fig="{base}">'
        f'<span class="key-sentinel"></span>'
        f'<div class="key-panel">'
        f'<p class="key-head">Key</p>'
        f'<p class="key-note">{note}</p>'
        f'<div class="key-groups">{groups}{ci}</div>'
        f'</div></div>'
    )


def render_callout(blk: list[str], inline_md: markdown.Markdown, interactive_count: list[int]) -> str:
    paras = _paragraphs(blk)
    title_para = paras[0]
    m = TITLE_RE.match(title_para)
    if not m:
        raise ValueError(f"unrecognised callout title: {title_para[:80]!r}")
    title = m.group("title").strip()
    marker = (m.group("marker") or "").strip()
    is_interactive = marker.lower().startswith("interactive")

    img = next((p for p in paras if IMG_RE.match(p)), None)
    if img is None:
        raise ValueError(f"callout {title[:40]!r} has no image reference")
    im = IMG_RE.match(img)
    alt = im.group("alt")
    img_path = Path(im.group("path"))
    base = img_path.stem

    how = next((p for p in paras if p.lower().startswith("how to read")), "")
    take = next((p for p in paras if p.startswith("**Takeaway")), "")

    spec_path = INTERACTIVE / f"{base}.json"
    live = is_interactive and spec_path.exists()
    badge_kind = "interactive" if live else "static"
    badge = f'<span class="fig-badge fig-badge-{badge_kind}">{badge_kind}</span>'

    parts = [f'<figure class="callout" data-fig="{base}">',
             f'<h4 class="fig-title">{title} {badge}</h4>']
    if how:
        parts.append(f'<p class="fig-how">{_strip_p(_inline(inline_md, how))}</p>')

    asset = _fig_asset(base)
    if asset is None:
        raise ValueError(f"no figure asset for {base}")

    if live:
        spec = json.loads(spec_path.read_text())
        spec.get("layout", {}).pop("updatemenus", None)   # floating menus overlap titles; we use checkboxes
        payload = json.dumps(spec).replace("</", "<\\/")
        ci_path = INTERACTIVE / f"{base}_ci.json"
        ci_payload = None
        if ci_path.exists():
            ci_spec = json.loads(ci_path.read_text())
            ci_spec.get("layout", {}).pop("updatemenus", None)
            ci_payload = json.dumps(ci_spec).replace("</", "<\\/")
        uri = _data_uri(asset)
        interactive_count[0] += 1
        parts.append('<div class="fig-body">')
        parts.append(key_box_html(base, spec, ci_payload is not None))
        _h = FIG_HEIGHTS.get(base)
        parts.append(f'<div class="plotly-fig" id="fig-{base}"'
                     + (f' style="height:{_h}"' if _h else '') + '></div>')
        parts.append('<details class="fig-fallback" open><summary>Static fallback '
                     '(used automatically when JavaScript is unavailable)</summary>'
                     f'<img alt="{alt}" src="{uri}"></details>')
        parts.append("</div>")
        parts.append(f'<script type="application/json" id="data-{base}">{payload}</script>')
        if ci_payload is not None:
            parts.append(f'<script type="application/json" id="data-{base}-ci">{ci_payload}</script>')
    else:
        uri = _data_uri(asset)
        parts.append(f'<div class="fig-body"><img alt="{alt}" src="{uri}"></div>')

    if take:
        parts.append(f'<figcaption class="fig-takeaway">{_strip_p(_inline(inline_md, take))}</figcaption>')
    parts.append("</figure>")
    return "\n".join(parts)


# --------------------------------------------------------------------------- render

def render(md_path: Path, html_path: Path, title: str) -> None:
    text = md_path.read_text()
    text, callouts = split_callouts(text)
    text, folds = split_collapsibles(text)

    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists", "smarty"],
        extension_configs={"toc": {"anchorlink": True, "permalink": False}},
    )
    body = md.convert(text)

    inline_md = markdown.Markdown(extensions=["sane_lists", "smarty"])
    interactive_count = [0]
    for i, blk in enumerate(callouts):
        block_html = render_callout(blk, inline_md, interactive_count)
        for token in (f"<p>@@FIGCALLOUT_{i}@@</p>", f"@@FIGCALLOUT_{i}@@"):
            if token in body:
                body = body.replace(token, block_html)
                break
        else:
            raise ValueError(f"callout placeholder {i} not found after markdown conversion")

    for i, (summary, inner_md) in enumerate(folds):
        inner_html = markdown.Markdown(
            extensions=["tables", "fenced_code", "sane_lists", "smarty"]).convert(inner_md)
        block_html = (
            f'<details class="fold"><summary>{_strip_p(_inline(inline_md, summary))}</summary>\n'
            f'<div class="fold-body">{inner_html}</div></details>'
        )
        for token in (f"<p>@@COLLAPSEBLOCK_{i}@@</p>", f"@@COLLAPSEBLOCK_{i}@@"):
            if token in body:
                body = body.replace(token, block_html)
                break
        else:
            raise ValueError(f"collapsible placeholder {i} not found after markdown conversion")

    body = mark_numeric_cells(body)
    links = HEADER_LINKS.get(md_path.name, [])
    if links and "</h1>" in body:
        body = body.replace("</h1>", "</h1>\n" + header_links_html(links), 1)
    toc = toc_html(md.toc_tokens, links)

    plotly = ""
    boot = ""
    if interactive_count[0]:
        if not PLOTLY_JS.exists():
            raise FileNotFoundError(f"interactive charts requested but {PLOTLY_JS} is missing")
        plotly = f'<script>{PLOTLY_JS.read_text()}</script>'
        boot = _BOOT_SCRIPT

    tagline = " from the checked-out Markdown and figure artifacts"
    html = BODY_TMPL.format(
        title=title, css=CSS, src=md_path.name, tagline=tagline,
        body=body, footer=FOOTER, plotly=plotly, boot=boot, toc=toc, navscript=NAV_SCRIPT if toc else "",
    )
    html_path.write_text(html)
    print(f"rendered {md_path.name} -> {html_path.name}: "
          f"{html_path.stat().st_size:,} bytes, {len(callouts)} callouts "
          f"({interactive_count[0]} interactive)")


def main(argv: list[str]) -> None:
    if len(argv) == 3:
        render(Path(argv[1]), Path(argv[2]), Path(argv[1]).stem)
        return
    render(ROOT / "REPORT.md", ROOT / "REPORT.html",
           html.escape((ROOT / "REPORT.md").read_text().splitlines()[0].removeprefix("# ")))
    render(ROOT / "EXECUTIVE_SUMMARY.md", ROOT / "EXECUTIVE_SUMMARY.html",
           "Automated code review — executive summary")


if __name__ == "__main__":
    main(sys.argv)
