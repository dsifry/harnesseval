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
import datetime
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
:root { color-scheme: light; --ink:#1b1f24; --muted:#5b6472; --accent:#0b5cad; --rule:#d9dee5; --bg:#fcfcfd; }
* { box-sizing: border-box; }
/* Type scales with the viewport (on html, so rem-based headings/measures scale too). */
html { font-size: clamp(16px, 0.40vw + 11.5px, 21px); }
body { margin:0; padding:0 0 6rem; background:var(--bg); color:var(--ink);
       font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
       font-size:1rem; line-height:1.65; }
/* The container and the text measure BOTH track the viewport, so text and charts scale together:
   charts/tables fill the container, prose fills ~92% of it. */
main { width: min(96vw, 2840px); margin: 0 auto; padding: 2.5rem clamp(.75rem, 2.5vw, 3rem) 4rem; }
:root { --measure: min(100%, 92vw, 2600px); }
@media (max-width: 760px) { main { width: 100%; padding: 1.5rem .9rem 3rem; } }
main > p, main > ul, main > ol, main > blockquote, main > h1, main > h2, main > h3, main > h4,
main > table, main > details, main > hr { max-width: var(--measure); margin-left: auto; margin-right: auto; }
figure.callout .fig-how, figure.callout figcaption.fig-takeaway, figure.callout .fig-controls {
  max-width: var(--measure); }
h1,h2,h3,h4 { line-height:1.25; font-weight:700; scroll-margin-top:1rem; }
h1 { font-size:1.9rem; margin:2.5rem 0 1rem; border-bottom:3px solid var(--accent); padding-bottom:.4rem; }
h2 { font-size:1.45rem; margin:2.4rem 0 .8rem; border-bottom:1px solid var(--rule); padding-bottom:.3rem; }
h3 { font-size:1.18rem; margin:1.8rem 0 .6rem; }
h4 { font-size:1.02rem; margin:1.4rem 0 .5rem; color:var(--muted); }
a { color:var(--accent); text-decoration:none; }
a:hover { text-decoration:underline; }
code, pre { font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }
code { background:#eef1f4; padding:.1em .35em; border-radius:4px; }
pre { background:#f4f6f8; border:1px solid var(--rule); border-radius:8px;
      padding:.9rem 1.1rem; overflow-x:auto; }
pre code { background:none; padding:0; }
table { border-collapse:collapse; margin:1.1rem 0; width:100%; font-size:.92em; display:block;
        overflow-x:auto; }
th,td { border:1px solid var(--rule); padding:.4rem .6rem; text-align:left; vertical-align:top; }
th { background:#eef2f6; font-weight:700; }
tr:nth-child(even) td { background:#f7f9fb; }
blockquote { margin:1rem 0; padding:.6rem 1rem; border-left:4px solid var(--accent);
             color:var(--muted); background:#f2f6fa; border-radius:0 6px 6px 0; }
hr { border:none; border-top:1px solid var(--rule); margin:2rem 0; }
details.fold { margin:1rem 0; border:1px solid var(--rule); border-radius:10px; background:#fff; }
details.fold > summary { cursor:pointer; padding:.6rem .9rem; font-weight:600; color:var(--accent);
  list-style:none; user-select:none; }
details.fold > summary::-webkit-details-marker { display:none; }
details.fold > summary::before { content:"▸ "; color:var(--muted); }
details.fold[open] > summary::before { content:"▾ "; }
details.fold[open] > summary { border-bottom:1px solid var(--rule); }
details.fold .fold-body { padding:.4rem .9rem .9rem; }
details.fold table { margin:.4rem 0; }
.generated { color:var(--muted); font-size:.85em; border:1px solid var(--rule);
             border-radius:8px; padding:.5rem .9rem; background:#f4f6f8; }
.toc a { color:var(--ink); }
footer { margin-top:4rem; color:var(--muted); font-size:.85em; border-top:1px solid var(--rule); padding-top:1rem; }

/* ---- figure callout cards ---- */
figure.callout { margin:2rem 0; padding:1.1rem 1.2rem 1.2rem; background:#fff;
  border:1px solid var(--rule); border-left:5px solid var(--accent); border-radius:10px;
  box-shadow:0 1px 2px rgba(16,24,40,.04); }
figure.callout .fig-title { margin:0 0 .5rem; font-size:1.02rem; color:var(--ink); font-weight:700; }
.fig-badge { display:inline-block; margin-left:.5rem; vertical-align:1px; padding:.1em .55em;
  font-size:.72em; font-weight:700; letter-spacing:.03em; text-transform:uppercase;
  border-radius:999px; border:1px solid; }
.fig-badge-interactive { color:#0b5cad; border-color:#9dc2e6; background:#eaf3fb; }
.fig-badge-static { color:#5b6472; border-color:#d9dee5; background:#f4f6f8; }
.fig-how { margin:.35rem 0 .9rem; color:var(--muted); font-style:italic; font-size:.93em; }
.fig-body { margin:.4rem 0 .9rem; }
.fig-body img { width:100%; max-width:100%; height:auto; display:block; margin:0 auto; }
.plotly-fig { width:100%; height:clamp(480px, 62vh, 900px); }
.fig-controls { margin:.2rem 0 .5rem; font-size:.85em; color:var(--muted); }
.fig-controls label { cursor:pointer; user-select:none; }

/* ---- per-figure key box (model / harness / effort / CI), mirrors the dashboard's docked filter box ---- */
.fig-key { margin:.2rem 0 .6rem; }
.fig-key .key-sentinel { display:block; height:1px; }
.fig-key .key-panel { position:sticky; top:0; z-index:5;
  border:1px solid var(--rule); border-radius:9px; background:#fff; padding:.5rem .7rem .55rem;
  transition: padding .3s ease, box-shadow .3s ease, border-radius .3s ease; }
.fig-key.docked .key-panel { padding:.25rem .55rem .3rem; box-shadow:0 2px 10px rgba(16,24,40,.10);
  border-radius:0 0 9px 9px; }
.fig-key .key-head { font-size:.78em; font-weight:700; letter-spacing:.03em; text-transform:uppercase;
  color:var(--muted); margin:0 0 .2rem; transition:font-size .3s ease; }
.fig-key.docked .key-head { font-size:.68em; margin-bottom:.1rem; }
.fig-key .key-note { color:var(--muted); font-size:.82em; margin:.1rem 0 .35rem; }
.fig-key.docked .key-note { display:none; }
/* one row per group: Models on its own line, then Harness, then Effort (wrapping only when narrow) */
.fig-key .key-groups { display:block; }
.fig-key .key-group { display:flex; flex-wrap:wrap; align-items:baseline; gap:.1rem .85rem; margin:.1rem 0; }
.fig-key .key-title { flex:0 0 auto; min-width:6.4rem; font-size:.72em; font-weight:700;
  text-transform:uppercase; letter-spacing:.03em; color:var(--muted); }
.fig-key label { display:inline-flex; align-items:center; gap:.28rem; }
.fig-key .key-title .key-all { font-weight:400; text-transform:none; letter-spacing:0; }
.fig-key label { font-size:.85em; color:var(--ink); white-space:nowrap; }
.fig-key input[type=checkbox] { vertical-align:-1px; margin-right:.15rem; }
.fig-key input[type=checkbox]:focus-visible { outline:2px solid var(--accent); outline-offset:1px; }
.fig-key a.key-all { color:var(--accent); }
@media (max-width: 760px) { main { width: 100%; padding: 1.5rem .9rem 3rem; } .plotly-fig { height: 460px; } }
.fig-fallback { margin-top:.6rem; }
.fig-fallback summary { cursor:pointer; color:var(--muted); font-size:.85em; }
.fig-fallback img { margin-top:.6rem; }figcaption.fig-takeaway { margin-top:.4rem; padding-left:.8rem; border-left:3px solid var(--rule);
  font-size:.95em; }
figcaption.fig-takeaway strong { color:var(--ink); }
@media print { figure.callout { break-inside:avoid; } .fig-fallback { display:block; } }
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
<main>
{body}
{footer}
<p class="generated">This page is a generated HTML rendering of <code>{src}</code> —
the Markdown file is the source of truth. Generated {date} by
<code>tools/report_to_html.py</code>{tagline}. Figures are regenerated renderings;
the interactive charts carry the same data as the
<a href="analysis/figures/interactive_dashboard.html">interactive dashboard</a>.</p>
</main>
{boot}
</body>
</html>
"""

FOOTER = (
    "Automated code review evaluation — report revision <code>report-2026-09-18</code>. "
    'Charts: <a href="analysis/figures/interactive_dashboard.html">interactive dashboard</a> · '
    'PNGs in <a href="analysis/figures/">analysis/figures/</a> · '
    '<a href="EXECUTIVE_SUMMARY.html">executive summary (HTML)</a> / '
    '<a href="REPORT.html">full report (HTML)</a>'
)


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

  /* Hide the points the key says to hide: null them out (keeps the legend and the rest of the trace). */
  function maskedTraces(traces, st) {
    var idx = buildCoordIndex(traces);
    return traces.map(function (t) {
      var xsrc = t.x || [], cd = t.customdata || [];
      var out = copy(t), any = false, kept = 0;
      var xs = [], ys = (t.y || []).slice();
      var ex = t.error_x && t.error_x.array ? t.error_x.array.slice() : null;
      var exm = t.error_x && t.error_x.arrayminus ? t.error_x.arrayminus.slice() : null;
      var ey = t.error_y && t.error_y.array ? t.error_y.array.slice() : null;
      var eym = t.error_y && t.error_y.arrayminus ? t.error_y.arrayminus.slice() : null;
      for (var i = 0; i < xsrc.length; i++) {
        var c = cellOf(cd.length ? cd[i] : null, xsrc[i]);
        var pass = true;
        if (c) {
          any = true;
          pass = passes(c, st);
        } else if (t.x && t.y) {
          // no metadata on this point (e.g. a connecting line): resolve it by coordinates
          var hit = idx[coordKey(xsrc[i], ys[i])];
          if (hit && hit.length) { any = true; pass = hit.some(function (h) { return passes(h, st); }); }
        }
        if (pass) { kept++; xs.push(xsrc[i]); }
        else {
          xs.push(null);
          if (ys.length) ys[i] = null;
          if (ex) ex[i] = null; if (exm) exm[i] = null;
          if (ey) ey[i] = null; if (eym) eym[i] = null;
        }
      }
      out.x = xs;
      if (t.y) out.y = ys;
      if (ex) out.error_x.array = ex;
      if (exm) out.error_x.arrayminus = exm;
      if (ey) out.error_y.array = ey;
      if (eym) out.error_y.arrayminus = eym;
      if (any && kept === 0) out.visible = false;
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

    plotly = ""
    boot = ""
    if interactive_count[0]:
        if not PLOTLY_JS.exists():
            raise FileNotFoundError(f"interactive charts requested but {PLOTLY_JS} is missing")
        plotly = f'<script>{PLOTLY_JS.read_text()}</script>'
        boot = _BOOT_SCRIPT

    today = datetime.date.today().isoformat()
    tagline = (" at repo tag <code>report-2026-09-18</code>"
               if md_path.name.startswith("REPORT") else "")
    html = BODY_TMPL.format(
        title=title, css=CSS, src=md_path.name, date=today, tagline=tagline,
        body=body, footer=FOOTER, plotly=plotly, boot=boot,
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
           "September 2026: Open-weight code-review harnesses match Opus and Sol in quality at a fraction of the cost")
    render(ROOT / "EXECUTIVE_SUMMARY.md", ROOT / "EXECUTIVE_SUMMARY.html",
           "Automated code review — executive summary")


if __name__ == "__main__":
    main(sys.argv)
