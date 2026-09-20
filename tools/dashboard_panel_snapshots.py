#!/usr/bin/env python3
"""Render static snapshots (PNG) of the exported dashboard panels.

Source of truth: analysis/figures/interactive/dash_chart*.json (exported from the dashboard's own
code by tools/export_dashboard_panels.js — not rebuilt). The dashboard is Plotly-JS; plotly.py
validates more strictly, so JS-only properties are stripped iteratively (the validator names each
bad path) before kaleido writes the PNG. Used as the report's static fallback image for each panel.

Usage: .venv/bin/python tools/dashboard_panel_snapshots.py [--width 1200 --height 640 --scale 2]
"""
from __future__ import annotations

import glob
import json
import os
from pathlib import Path

import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis/figures"
FRAGS = ROOT / "analysis/figures/interactive"
def build(spec: dict) -> go.Figure:
    """JS Plotly is laxer than plotly.py (e.g. marker.line.opacity); skip_invalid drops those."""
    return go.Figure(data=spec["traces"], layout=spec.get("layout", {}), skip_invalid=True)


def main() -> int:
    width = int(os.environ.get("SNAP_W", 1200))
    height = int(os.environ.get("SNAP_H", 640))
    n = 0
    for f in sorted(glob.glob(str(FRAGS / "dash_chart*.json"))):
        base = Path(f).stem
        if base.endswith("_ci"):
            continue
        spec = json.load(open(f))
        fig = build(spec)
        out = OUT / f"{base}.png"
        fig.write_image(str(out), width=width, height=height, scale=2)
        print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size//1024} KB)")
        n += 1
    print(f"snapshots: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
