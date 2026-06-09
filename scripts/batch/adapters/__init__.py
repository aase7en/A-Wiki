"""
adapters/ — Provider-specific clients sharing a common Adapter ABC.

Each adapter wraps prompt_template output into the provider's request shape,
handles authentication via drive_secrets, and returns results in a uniform
format consumable by collect.py.
"""
from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))


@dataclass
class IngestRequest:
    """One unit of ingestion work — one raw/ file → one wiki/sources/ entry."""
    raw_path: str
    slug: str
    custom_id: str
    date_ingested: str
    tier: int
    domain_hint: str | None = None


@dataclass
class IngestResult:
    """Adapter output for one request."""
    custom_id: str
    slug: str
    raw_path: str
    tier: int
    success: bool
    content: str = ""
    error: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class Adapter(ABC):
    """Common interface across DeepSeek (sync), OpenAI (batch), Anthropic (batch)."""

    name: str = "base"
    mode: str = "realtime"  # "realtime" or "batch"

    def __init__(self, tier_config: dict[str, Any]):
        self.config = tier_config
        self.model = tier_config["model"]
        self.endpoint = tier_config["endpoint"]
        self.secret_name = tier_config["secret_name"]

    @abstractmethod
    def submit(self, requests: list[IngestRequest]) -> dict[str, Any]:
        """Submit one batch / sync call.

        Realtime adapters perform the work here and return
            {"mode": "realtime", "results": [IngestResult, ...]}
        Batch adapters submit and return
            {"mode": "batch", "batch_id": "...", "input_path": "..."}
        """

    def poll(self, batch_id: str) -> dict[str, Any]:
        """Batch adapters only — check status. Returns {"status": ..., "raw": ...}."""
        raise NotImplementedError(f"{self.name} does not support polling (realtime adapter)")

    def collect(self, batch_id: str, requests_index: dict[str, IngestRequest]) -> list[IngestResult]:
        """Batch adapters only — download + parse results. Maps custom_id → IngestRequest."""
        raise NotImplementedError(f"{self.name} does not support collect (realtime adapter)")
