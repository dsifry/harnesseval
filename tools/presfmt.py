#!/usr/bin/env python3
"""Presentation float formatting — artifact-free, arbitrary N decimal places.

The classic fixed-places ``f`` format does exact decimal rounding of the binary
float, which kills binary-tail artifacts (0.5847899999999999 -> 0.58479); we then
strip trailing zeros so small values read $0.00035, not $0.00035000. ``places`` is
arbitrary; the campaign standard is 5. Used by tools/final_report_tables.py and
(as a JS twin, ``fmt``) by tools/final_report_html.py.
"""

def fnum(x, places=5):
    """float -> string with at most `places` decimal places, artifact-free."""
    if x is None:
        return "—"
    try:
        x = float(x)
    except (TypeError, ValueError):
        return str(x)
    if x != x or x in (float("inf"), float("-inf")):
        return "—"
    v = f"{x:.{places}f}".rstrip("0").rstrip(".")
    return v if v else "0"


def money(x, places=5):
    """$ + fnum."""
    return f"${fnum(x, places)}"


def money_adaptive(x, places=5):
    """Dollar value as an adaptive string: < $0.01 -> cents (e.g. $0.00029 -> '0.029¢'),
    else $ + fnum. Kills leading-zero drowning without losing precision."""
    if x is None:
        return "—"
    try:
        x = float(x)
    except (TypeError, ValueError):
        return str(x)
    if x != x or x in (float("inf"), float("-inf")):
        return "—"
    if 0 < abs(x) < 0.01:
        return f"{fnum(x * 100, places)}¢"
    return f"${fnum(x, places)}"
