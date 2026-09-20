#!/bin/bash
# Assemble the GitHub Pages site: only the rendered reports, never the whole repo.
#
#   tools/publish_site.sh [outdir]      (default: _site)
#
# sdlc-report.html is the index page. REPORT.html, EXECUTIVE_SUMMARY.html and SLIDES.html sit
# beside it so the developer edition's relative links resolve, and analysis/figures/ is included
# because the reports link to the interactive dashboard and the link-preview image lives there.
# Everything else in the repo (runs/, evidence archives, tools) stays unpublished.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/_site}"
rm -rf "$OUT"
mkdir -p "$OUT/analysis"
cp "$ROOT/sdlc-report.html" "$OUT/index.html"
cp "$ROOT/sdlc-report.html" "$ROOT/REPORT.html" "$ROOT/EXECUTIVE_SUMMARY.html" "$ROOT/SLIDES.html" "$OUT/"
cp -R "$ROOT/analysis/figures" "$OUT/analysis/figures"
touch "$OUT/.nojekyll"   # keep GitHub from running Jekyll over the output
echo "site assembled in $OUT:"
find "$OUT" -maxdepth 1 -type f | sort | sed "s|$OUT/|  |"
du -sh "$OUT" | cut -f1 | sed 's/^/  total: /'
