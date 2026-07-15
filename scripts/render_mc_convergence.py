#!/usr/bin/env python3
"""Render MC convergence diagnostic JSON → static SVG/HTML widget.

K7: per AGENTS.md rule 7 (render, don't dump), emit compact JSON → render to
gitignored leaf HTML in exports/html/. The widget is fully static (no JS, no
external CDN) — pure SVG embedded in HTML, so it works offline and can be
embedded anywhere.

Schema (mc_convergence_data.json):
    {
      "title": str, "subtitle": str, "non_advisory_banner": str,
      "threshold_pct": float,
      "series": [{"n": int, "mean": float, "se": float,
                  "doubling_delta_pct": float, "converged": bool}, ...]
    }

Usage:
    python scripts/render_mc_convergence.py \\
        --json skills/awiki/monte-carlo-quant-analysis/examples/mc_convergence_data.json \\
        --out exports/html/mc-convergence-widget.html

[verified 2026-07-15]
"""
from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path


def render_widget(data: dict) -> str:
    """Render convergence-data dict → complete HTML string with embedded SVG.

    Two-panel layout:
      - Left: doubling-N delta% (log scale) vs threshold line
      - Right: mean ± SE band over N levels
    Iron Law #8 banner at top.
    """
    if not data or "series" not in data or not data["series"]:
        return _empty_fallback(data)

    series = data["series"]
    title = escape(data.get("title", "MC Convergence"))
    subtitle = escape(data.get("subtitle", ""))
    banner = escape(data.get("non_advisory_banner", "PAPER-ONLY · NON-ADVISORY"))
    threshold = float(data.get("threshold_pct", 1.0))

    # Chart geometry
    W, H = 900, 380
    margin = 60
    plot_w = (W - 2 * margin) // 2 - 20
    plot_h = H - 2 * margin - 40

    ns = [s["n"] for s in series]
    deltas = [s["doubling_delta_pct"] for s in series]
    means = [s["mean"] for s in series]
    ses = [s["se"] for s in series]

    # Left panel: delta% on log scale
    max_delta = max(max(deltas), threshold * 2)
    min_delta = min(min(d for d in deltas if d > 0), 0.001)
    import math
    log_min = math.log10(max(min_delta, 0.0001))
    log_max = math.log10(max_delta * 1.2)

    def x_left(i):
        return margin + (plot_w * i / max(len(ns) - 1, 1))

    def y_left(delta):
        if delta <= 0:
            delta = min_delta
        return margin + plot_h * (1 - (math.log10(delta) - log_min) / (log_max - log_min))

    # Right panel: mean ± SE
    mean_lo = min(m - s for m, s in zip(means, ses))
    mean_hi = max(m + s for m, s in zip(means, ses))
    mean_range = mean_hi - mean_lo or 1.0

    def x_right(i):
        return margin + plot_w + 40 + (plot_w * i / max(len(ns) - 1, 1))

    def y_mean(v):
        return margin + plot_h * (1 - (v - mean_lo) / mean_range)

    # Build SVG path strings
    delta_path = "M " + " L ".join(f"{x_left(i):.1f} {y_left(d):.1f}" for i, d in enumerate(deltas))
    mean_path = "M " + " L ".join(f"{x_right(i):.1f} {y_mean(m):.1f}" for i, m in enumerate(means))

    # SE band (polygon: upper then lower reversed)
    upper = [(x_right(i), y_mean(m + s)) for i, (m, s) in enumerate(zip(means, ses))]
    lower = [(x_right(i), y_mean(m - s)) for i, (m, s) in enumerate(zip(means, ses))]
    band_pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in upper + lower[::-1])

    # Threshold line on left panel
    y_thresh = y_left(threshold)

    # Markers: green if converged, red if not
    markers_left = ""
    for i, s in enumerate(series):
        color = "#22c55e" if s["converged"] else "#ef4444"
        markers_left += f'<circle cx="{x_left(i):.1f}" cy="{y_left(s["doubling_delta_pct"]):.1f}" r="4" fill="{color}"/>'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="sans-serif" font-size="11">
  <rect width="{W}" height="{H}" fill="#fafafa"/>
  <!-- Iron Law #8 banner -->
  <rect x="0" y="0" width="{W}" height="22" fill="#fef3c7"/>
  <text x="{W//2}" y="15" text-anchor="middle" font-size="11" font-weight="bold" fill="#92400e">{banner}</text>

  <text x="{margin}" y="40" font-size="14" font-weight="bold">{title}</text>
  <text x="{margin}" y="56" font-size="10" fill="#666">{subtitle}</text>

  <!-- Left panel: doubling-N delta% -->
  <text x="{margin}" y="{margin-8}" font-size="11" font-weight="bold">Doubling-N Δ% (log scale)</text>
  <rect x="{margin}" y="{margin}" width="{plot_w}" height="{plot_h}" fill="white" stroke="#ddd"/>
  <path d="{delta_path}" fill="none" stroke="#3b82f6" stroke-width="2"/>
  {markers_left}
  <line x1="{margin}" y1="{y_thresh:.1f}" x2="{margin+plot_w}" y2="{y_thresh:.1f}" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4 2"/>
  <text x="{margin+plot_w-4}" y="{y_thresh-4:.1f}" text-anchor="end" font-size="9" fill="#ef4444">{threshold}% threshold</text>

  <!-- Right panel: mean ± SE -->
  <text x="{margin+plot_w+40}" y="{margin-8}" font-size="11" font-weight="bold">Estimate ± SE</text>
  <rect x="{margin+plot_w+40}" y="{margin}" width="{plot_w}" height="{plot_h}" fill="white" stroke="#ddd"/>
  <polygon points="{band_pts}" fill="#3b82f6" fill-opacity="0.2"/>
  <path d="{mean_path}" fill="none" stroke="#3b82f6" stroke-width="2"/>
  {''.join(f'<circle cx="{x_right(i):.1f}" cy="{y_mean(m):.1f}" r="3" fill="#3b82f6"/>' for i, m in enumerate(means))}

  <!-- X-axis labels (N values) -->
  {''.join(f'<text x="{x_left(i):.1f}" y="{margin+plot_h+15}" text-anchor="middle" font-size="9">{n//1000}k</text>' for i, n in enumerate(ns))}
  {''.join(f'<text x="{x_right(i):.1f}" y="{margin+plot_h+15}" text-anchor="middle" font-size="9">{n//1000}k</text>' for i, n in enumerate(ns))}
  <text x="{margin+plot_w//2}" y="{margin+plot_h+32}" text-anchor="middle" font-size="10">N (samples)</text>
  <text x="{margin+plot_w+40+plot_w//2}" y="{margin+plot_h+32}" text-anchor="middle" font-size="10">N (samples)</text>

  <!-- Legend -->
  <circle cx="{W-180}" cy="{H-18}" r="4" fill="#22c55e"/><text x="{W-170}" y="{H-14}" font-size="9">converged</text>
  <circle cx="{W-100}" cy="{H-18}" r="4" fill="#ef4444"/><text x="{W-90}" y="{H-14}" font-size="9">not converged</text>
</svg>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>body{{margin:0;padding:20px;background:#fafafa;font-family:sans-serif}}</style>
</head>
<body>
{svg}
</body>
</html>'''
    return html


def _empty_fallback(data: dict) -> str:
    """Graceful fallback when data is empty or malformed."""
    banner = escape(data.get("non_advisory_banner", "PAPER-ONLY · NON-ADVISORY")) if data else ""
    return f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>MC Convergence (empty)</title></head>
<body>
<div style="background:#fef3c7;padding:8px;font-weight:bold;color:#92400e">{banner}</div>
<p>No convergence data available.</p>
</body></html>'''


def main():
    p = argparse.ArgumentParser(description="Render MC convergence JSON → static HTML widget")
    p.add_argument("--json", required=True, help="Path to convergence_data.json")
    p.add_argument("--out", required=True, help="Output HTML path")
    args = p.parse_args()

    data = json.loads(Path(args.json).read_text(encoding="utf-8"))
    html = render_widget(data)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
