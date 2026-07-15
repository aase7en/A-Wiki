#!/usr/bin/env python3
"""Reusable quant-risk metrics — the API backing SKILL.md §3 Quant Risk Metrics.

O-A: before this module, the metrics in the §3 table (VaR/CVaR/Sharpe/RRR)
existed only as inline computations scattered across test files. External
agents (e.g. the `finance-analyst` subagent) had no importable API to call.
This module is that API — each function maps one row of the §3 table.

**Iron Law #8 (bot-trading-iron-law): PAPER-ONLY · NON-ADVISORY.**
All inputs are synthetic / simulation outputs. The functions compute risk
metrics on a given P&L distribution; they do NOT recommend trades, sizes, or
positions. Outputs are descriptive statistics for analysis only.

Contract (pinned by `tests/test_mc_quant.py`):
  - var_estimate(log_returns, alpha) -> float          (α-percentile of P&L)
  - cvar_estimate(log_returns, alpha) -> float         (E[loss | loss ≤ VaR])
  - sharpe_distribution(log_returns_paths, rf) -> dict (per-path → {p5,median,p95,...})
  - rr_distribution(log_returns_paths) -> dict         (per-path → percentiles)

Shape conventions:
  - log_returns: 1-D array of per-scenario P&L (e.g. horizon-total returns).
  - log_returns_paths: 2-D (N_paths, T) array of per-step log-returns; the
    Sharpe/RR functions aggregate *per path* then report the distribution.

Usage:
    python scripts/mc_quant.py --demo

[verified 2026-07-16]
"""
from __future__ import annotations

import argparse

import numpy as np

NON_ADVISORY_BANNER = "PAPER-ONLY · NON-ADVISORY · simulation output, not advice"

# Annualization factor assumption: input paths are daily log-returns.
_TRADING_DAYS_PER_YEAR = 252


def var_estimate(log_returns: np.ndarray, alpha: float = 0.05) -> float:
    """VaR(α) = α-percentile of the P&L distribution (SKILL.md §3).

    Returns the loss level not exceeded with probability 1-α. For α=0.05 on
    N(0,1) this is ≈ -1.645. More negative = worse tail.

    `log_returns` is a 1-D array of per-scenario P&L (horizon-total returns,
    daily returns, or any other per-scenario scalar). `alpha` is the tail
    probability in [0, 1] (default 5%).
    """
    log_returns = np.asarray(log_returns, dtype=float).ravel()
    if log_returns.size == 0:
        raise ValueError("var_estimate: empty input")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0,1), got {alpha}")
    return float(np.percentile(log_returns, alpha * 100.0))


def cvar_estimate(log_returns: np.ndarray, alpha: float = 0.05) -> float:
    """CVaR/ES(α) = E[loss | loss ≤ VaR(α)] (SKILL.md §3).

    The expected loss *given* a breach — i.e. the mean of the tail beyond
    VaR(α). Always ≤ VaR(α) on continuous distributions (tail mean is worse
    than the percentile that gates it).
    """
    log_returns = np.asarray(log_returns, dtype=float).ravel()
    if log_returns.size == 0:
        raise ValueError("cvar_estimate: empty input")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0,1), got {alpha}")
    threshold = np.percentile(log_returns, alpha * 100.0)
    tail = log_returns[log_returns <= threshold]
    if tail.size == 0:
        # Degenerate: no sample at or below threshold; fall back to VaR itself.
        return float(threshold)
    return float(tail.mean())


def _summarize(values: np.ndarray) -> dict:
    """Aggregate a 1-D array into the §3 distribution summary."""
    return {
        "median": float(np.median(values)),
        "p5": float(np.percentile(values, 5)),
        "p95": float(np.percentile(values, 95)),
        "mean": float(np.mean(values)),
        "std": float(np.std(values, ddof=1)) if values.size > 1 else 0.0,
    }


def sharpe_distribution(log_returns_paths: np.ndarray,
                        rf: float = 0.0,
                        periods_per_year: int = _TRADING_DAYS_PER_YEAR) -> dict:
    """Per-path Sharpe ratio → distribution summary (SKILL.md §3).

    `log_returns_paths` shape (N_paths, T). For each path, Sharpe is
    mean(excess return) / std(excess return), annualized by
    sqrt(periods_per_year). Returns {median, p5, p95, mean, std} of the
    per-path Sharpe values — i.e. Sharpe *as a distribution*, not a point
    estimate (CLT-based uncertainty band).
    """
    paths = np.asarray(log_returns_paths, dtype=float)
    if paths.ndim != 2:
        raise ValueError(f"expected 2-D (N_paths, T), got shape {paths.shape}")
    excess = paths - rf
    per_path_mean = excess.mean(axis=1)
    per_path_std = paths.std(axis=1, ddof=1)
    # Guard against zero-variance paths (would divide by zero).
    safe_std = np.where(per_path_std == 0.0, np.nan, per_path_std)
    sharpe = per_path_mean / safe_std * np.sqrt(periods_per_year)
    sharpe = sharpe[~np.isnan(sharpe)]
    if sharpe.size == 0:
        raise ValueError("sharpe_distribution: all paths had zero variance")
    return _summarize(sharpe)


def rr_distribution(log_returns_paths: np.ndarray) -> dict:
    """Per-path Risk-Reward Ratio (RRR) → distribution summary (SKILL.md §3).

    RRR per path = E[upside] / E[downside], where upside = positive returns
    and downside = magnitude of negative returns (both averaged per path).
    Returns {median, p5, p95, mean, std} of the per-path ratios.
    """
    paths = np.asarray(log_returns_paths, dtype=float)
    if paths.ndim != 2:
        raise ValueError(f"expected 2-D (N_paths, T), got shape {paths.shape}")
    upside = np.where(paths > 0, paths, 0.0).mean(axis=1)
    downside = np.where(paths < 0, -paths, 0.0).mean(axis=1)
    # Guard against zero-downside paths.
    safe_down = np.where(downside == 0.0, np.nan, downside)
    rr = upside / safe_down
    rr = rr[~np.isnan(rr)]
    if rr.size == 0:
        raise ValueError("rr_distribution: all paths had zero downside")
    return _summarize(rr)


def _demo() -> dict:
    """Run all four metrics on synthetic N(0,1)-ish data (fixed seed)."""
    rng = np.random.default_rng(42)
    # 1-D P&L for VaR/CVaR
    pnl = rng.standard_normal(100_000)
    var = var_estimate(pnl, alpha=0.05)
    cvar = cvar_estimate(pnl, alpha=0.05)
    # 2-D paths for Sharpe/RRR (N_paths, T)
    paths = rng.standard_normal((5_000, 252)) * 0.01
    sharpe = sharpe_distribution(paths)
    rr = rr_distribution(paths)
    return {
        "banner": NON_ADVISORY_BANNER,
        "data": "synthetic N(0,1), seed=42 (PAPER-ONLY)",
        "var_5pct": var,
        "cvar_5pct": cvar,
        "sharpe_distribution": sharpe,
        "rr_distribution": rr,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--demo", action="store_true",
                   help="run all four metrics on synthetic data and print")
    args = p.parse_args()
    if not args.demo:
        p.print_help()
        return
    import json
    result = _demo()
    print(NON_ADVISORY_BANNER)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
