#!/bin/bash
# Serve the report's charts on the LAN so other people can look at them.
#
#   tools/serve_report.sh [port] [root]
#
# Defaults: port 8765, root = the repo (so the existing
# /analysis/figures/interactive_dashboard.html URL keeps working).
# Binds 0.0.0.0 (all interfaces) — 127.0.0.1 would only be visible on this machine,
# which is the trap that made an earlier attempt invisible to everyone else.
#
# NOTE: python -m http.server is a dev server (no TLS, no auth) and this process dies
# on reboot/sleep. For viewers outside the LAN, tunnel it, e.g.
#   brew install cloudflared && cloudflared tunnel --url http://localhost:8765
# and prefer serving only the charts (second arg) so the tunnel does not expose the whole repo.
set -u
PORT="${1:-8765}"
ROOT="${2:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT" || exit 1
LAN=$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}')
echo "serving $ROOT on 0.0.0.0:$PORT"
echo "  this machine : http://127.0.0.1:$PORT/analysis/figures/interactive_dashboard.html"
echo "  report (html) : http://127.0.0.1:$PORT/REPORT.html"
echo "  exec summary  : http://127.0.0.1:$PORT/EXECUTIVE_SUMMARY.html"
[ -n "$LAN" ] && echo "  share this   : http://$LAN:$PORT/analysis/figures/interactive_dashboard.html"
echo "  (viewers need internet for the dashboard's Plotly CDN; the PNGs in analysis/figures/ need nothing)"
exec python3 -m http.server "$PORT" --bind 0.0.0.0
