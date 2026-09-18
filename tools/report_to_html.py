#!/usr/bin/env python3
"""Render REPORT_FINAL.md (and the executive summary) as standalone HTML.

One input -> one output, no template files, no network: the CSS is embedded so each
HTML file is self-contained (viewable from a file:// URL or any static server).
Markdown flavor: python-markdown with the tables / fenced_code / toc / sane_lists
extensions, matching what the reports actually use (GFM-style tables, fenced code
blocks, heading anchors).

Usage: .venv/bin/python tools/report_to_html.py            # both documents
       .venv/bin/python tools/report_to_html.py REPORT.md [OUT.html]

The generated HTML is a *rendering* of the committed Markdown: the Markdown files
remain the source of truth (see REPORT_FINAL.md §11; the chain regenerates the
numbers, this renders them). Not part of the byte-identical checksum set.
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]

CSS = """
:root { color-scheme: light; --ink:#1b1f24; --muted:#5b6472; --accent:#0b5cad; --rule:#d9dee5; --bg:#fcfcfd; }
* { box-sizing: border-box; }
body { margin:0; padding:0 0 6rem; background:var(--bg); color:var(--ink);
       font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
main { max-width: 60rem; margin: 0 auto; padding: 2.5rem 1.5rem; }
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
"""

BODY_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<main>
<p class="generated">This page is a generated HTML rendering of <code>{src}</code> —
the Markdown file is the source of truth. Generated {date} by
<code>tools/report_to_html.py</code>{tagline}.</p>
{body}
<footer>Automated code review evaluation — report revision <code>report-2026-09-18</code>.
Charts: <a href="analysis/figures/interactive_dashboard.html">interactive dashboard</a> ·
PNGs in <a href="analysis/figures/">analysis/figures/</a> ·
<a href="EXECUTIVE_SUMMARY_FINAL.html">executive summary (HTML)</a> /
<a href="REPORT_FINAL.html">full report (HTML)</a></footer>
</main>
</body>
</html>
"""


def render(md_path: Path, html_path: Path, title: str) -> None:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists", "smarty"],
        extension_configs={"toc": {"anchorlink": True, "permalink": False}},
    )
    body = md.convert(md_path.read_text())
    today = datetime.date.today().isoformat()
    tagline = " at repo tag <code>report-2026-09-18</code>" if md_path.name.startswith("REPORT") else ""
    html = BODY_TMPL.format(
        title=title, css=CSS, src=md_path.name, date=today,
        tagline=tagline, body=body,
    )
    html_path.write_text(html)
    print(f"rendered {md_path} -> {html_path} ({html_path.stat().st_size:,} bytes, "
          f"{len(md.toc_tokens)} top-level sections)")


def main(argv: list[str]) -> None:
    if len(argv) == 3:
        render(Path(argv[1]), Path(argv[2]), Path(argv[1]).stem)
        return
    render(ROOT / "REPORT_FINAL.md", ROOT / "REPORT_FINAL.html",
           "Automated code review: harness vs one-shot — final report")
    render(ROOT / "EXECUTIVE_SUMMARY_FINAL.md", ROOT / "EXECUTIVE_SUMMARY_FINAL.html",
           "Automated code review — executive summary")


if __name__ == "__main__":
    main(sys.argv)
