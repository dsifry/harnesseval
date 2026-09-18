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
.plotly-fig { width:100%; height:clamp(420px, 58vh, 820px); }
.fig-controls { margin:.2rem 0 .5rem; font-size:.85em; color:var(--muted); }
.fig-controls label { cursor:pointer; user-select:none; }
@media (max-width: 760px) { main { width: 100%; padding: 1.5rem .9rem 3rem; } .plotly-fig { height: 420px; } }
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

_BOOT_SCRIPT = """<script>
(function () {
  var figs = Array.prototype.slice.call(document.querySelectorAll('div.plotly-fig'));
  function fallbackFor(el) {
    var body = el.closest ? el.closest('.fig-body') : null;
    return body ? body.querySelector('details.fig-fallback') : null;
  }
  function boot() {
    if (!window.Plotly) {
      // No runtime: hide the empty chart containers so the static fallbacks stand alone.
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
        var useCi = false;
        var layout = spec.layout || {};
        // let the chart fill the responsive container
        delete layout.width; delete layout.height;
        if (ciSpec && ciSpec.layout) { delete ciSpec.layout.width; delete ciSpec.layout.height; }
        var cfg = spec.config || {}; cfg.responsive = true; cfg.displayModeBar = false;
        var draw = function () {
          var s2 = (useCi && ciSpec) ? ciSpec : spec;
          return window.Plotly.react(el, s2.traces, s2.layout || {}, cfg);
        };
        draw().then(function () {
          var fb = fallbackFor(el);
          if (fb) { fb.open = false; }   // chart is live; fold the static copy away
        });
        var box = document.querySelector('input.ci-toggle[data-fig="' + base + '"]');
        if (box) { box.addEventListener('change', function () { useCi = box.checked; draw(); }); }
      } catch (e) {
        console.error('figure render failed:', el.id, e);
        el.style.display = 'none';
        var fb2 = fallbackFor(el);
        if (fb2) { fb2.open = true; }
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
        payload = json.dumps(spec).replace("</", "<\\/")
        ci_path = INTERACTIVE / f"{base}_ci.json"
        ci_payload = None
        if ci_path.exists():
            ci_payload = json.dumps(json.loads(ci_path.read_text())).replace("</", "<\\/")
        uri = _data_uri(asset)
        interactive_count[0] += 1
        parts.append('<div class="fig-body">')
        if ci_payload is not None:
            parts.append('<p class="fig-controls"><label><input type="checkbox" class="ci-toggle" '
                         f'data-fig="{base}"> show 95% CIs</label></p>')
        parts.append(f'<div class="plotly-fig" id="fig-{base}"></div>')
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
