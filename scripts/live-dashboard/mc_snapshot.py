"""MC Snapshot — paper-only risk metric payload for the Live Dashboard (P1).

Read-only wrapper that turns `scripts/mc_quant.py::_demo()` into the JSON
payload served at:

  GET /api/mc-snapshot  → {banner, data, var_5pct, cvar_5pct,
                            sharpe_distribution, rr_distribution}

PAPER-ONLY · NON-ADVISORY · simulation output, not advice (Iron Law #8).
ใช้ synthetic N(0,1) seed=42 data เท่านั้น — ไม่มี real market data, ไม่มี I/O,
ไม่มี network call. Pure wrapper: mc_quant.py stays the single source of truth
for the four risk metrics (VaR / CVaR / Sharpe / RRR).

Contract pinned by tests/test_mc_snapshot.py. Mirrors the service-module
pattern of cost_history.py / eval_history.py / pipeline_graph.py — pure
functions, one `build_payload()` entry point, never crashes the dashboard.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Load mc_quant.py from the repo-root scripts/ dir via importlib — same
# guarded pattern cost_history.py uses to import cost-router.py (a hyphenated
# filename that isn't a valid Python module name). If mc_quant ever moves or
# its deps (numpy) are missing, the endpoint degrades to an error envelope
# instead of 500-ing the whole dashboard.
_MC_QUANT_PATH = REPO_ROOT / "scripts" / "mc_quant.py"
_MC_QUANT_OK = False
_mc = None
try:
    _spec = importlib.util.spec_from_file_location("mc_quant", str(_MC_QUANT_PATH))
    if _spec and _spec.loader:
        _mc = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mc)
        _MC_QUANT_OK = True
except Exception:
    # Don't log here — the dashboard SSE log is for events, not module load.
    # The error envelope returned by build_payload() is enough for diagnostics.
    _MC_QUANT_OK = False


def build_payload() -> dict[str, Any]:
    """Build the MC risk snapshot payload for `/api/mc-snapshot`.

    Returns `mc_quant._demo()` (synthetic N(0,1) seed=42, paper-only) when
    mc_quant loads cleanly; otherwise an explicit error envelope that still
    carries the Iron Law #8 banner so the dashboard can render the disclaimer
    even when the metrics are unavailable.

    Returns:
      dict — always JSON-serializable; always carries a `banner` key.
    """
    if not _MC_QUANT_OK or _mc is None:
        return {
            "error": "mc_quant.py unavailable (numpy missing or file moved)",
            "banner": "PAPER-ONLY · NON-ADVISORY · simulation output, not advice",
            "data": "unavailable",
        }
    return _mc._demo()
