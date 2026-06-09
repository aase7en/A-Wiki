"""
anthropic_batch.py — Tier 3 batch adapter (Anthropic Message Batches).

Use only as quality escalation when Tier 1/2 output fails quality_gate.py.
Cost: $0.50 input / $2.50 output per 1M tokens (Haiku 4.5 batch).

Flow: client.messages.batches.create(requests=[...]) → poll →
      client.messages.batches.results(batch_id) yields JSONL.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "batch"))

from drive_secrets import fetch_secret  # noqa: E402

from adapters import Adapter, IngestRequest, IngestResult  # noqa: E402
from prompt_template import SYSTEM_PROMPT, build_user_message, read_raw  # noqa: E402
from state import state_dir  # noqa: E402


class AnthropicBatchAdapter(Adapter):
    name = "anthropic"
    mode = "batch"

    def _client(self):
        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise RuntimeError(
                "anthropic package required for Tier 3 — pip install anthropic"
            ) from e
        api_key = fetch_secret(self.secret_name)
        if not api_key:
            raise RuntimeError(f"Secret {self.secret_name} not found in drive/.secrets")
        return Anthropic(api_key=api_key)

    def _build_requests(self, requests: list[IngestRequest]) -> list[dict]:
        out = []
        for req in requests:
            raw_text = read_raw(REPO_ROOT / req.raw_path)
            user_message = build_user_message(
                raw_path=req.raw_path,
                raw_text=raw_text,
                slug=req.slug,
                date_ingested=req.date_ingested,
                tier=req.tier,
                domain_hint=req.domain_hint,
            )
            out.append({
                "custom_id": req.custom_id,
                "params": {
                    "model": self.model,
                    "max_tokens": 4096,
                    "system": SYSTEM_PROMPT,
                    "messages": [
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.2,
                },
            })
        return out

    def submit(self, requests: list[IngestRequest]) -> dict[str, Any]:
        client = self._client()
        body = self._build_requests(requests)

        # Mirror input to drive/batch-state/in/ for auditability (cost reports rely on this).
        in_dir = state_dir() / "in"
        in_dir.mkdir(parents=True, exist_ok=True)
        in_path = in_dir / f"anthropic-{requests[0].custom_id}-{len(requests)}.jsonl"
        with in_path.open("w", encoding="utf-8") as fp:
            for entry in body:
                fp.write(json.dumps(entry, ensure_ascii=False) + "\n")

        batch = client.messages.batches.create(requests=body)
        return {
            "mode": "batch",
            "batch_id": batch.id,
            "input_path": str(in_path),
            "status": batch.processing_status,
        }

    def poll(self, batch_id: str) -> dict[str, Any]:
        client = self._client()
        batch = client.messages.batches.retrieve(batch_id)
        counts = getattr(batch, "request_counts", None)
        return {
            "status": batch.processing_status,
            "request_counts": counts.__dict__ if counts else {},
            "results_url": getattr(batch, "results_url", None),
        }

    def collect(
        self,
        batch_id: str,
        requests_index: dict[str, IngestRequest],
    ) -> list[IngestResult]:
        client = self._client()
        results: list[IngestResult] = []
        out_dir = state_dir() / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"anthropic-{batch_id}.jsonl"

        with out_path.open("w", encoding="utf-8") as fp:
            for entry in client.messages.batches.results(batch_id):
                # Persist raw for audit
                fp.write(json.dumps(_serialize(entry), ensure_ascii=False) + "\n")

                custom_id = getattr(entry, "custom_id", "")
                req = requests_index.get(custom_id)
                if req is None:
                    continue
                result_obj = getattr(entry, "result", None)
                rtype = getattr(result_obj, "type", "") if result_obj else ""

                if rtype != "succeeded":
                    err_text = ""
                    if result_obj is not None:
                        err_text = str(getattr(result_obj, "error", "") or rtype)
                    results.append(
                        IngestResult(
                            custom_id=custom_id,
                            slug=req.slug,
                            raw_path=req.raw_path,
                            tier=req.tier,
                            success=False,
                            error=f"{rtype}: {err_text[:300]}",
                        )
                    )
                    continue

                message = result_obj.message
                content_text = "".join(
                    block.text for block in message.content if getattr(block, "type", "") == "text"
                )
                usage = getattr(message, "usage", None)
                results.append(
                    IngestResult(
                        custom_id=custom_id,
                        slug=req.slug,
                        raw_path=req.raw_path,
                        tier=req.tier,
                        success=True,
                        content=content_text,
                        tokens_in=int(getattr(usage, "input_tokens", 0)) if usage else 0,
                        tokens_out=int(getattr(usage, "output_tokens", 0)) if usage else 0,
                        metadata={"stop_reason": getattr(message, "stop_reason", "")},
                    )
                )
        return results


def _serialize(obj: Any) -> Any:
    """Best-effort JSON serialization of Anthropic SDK objects (for audit logs)."""
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return {k: _serialize(v) for k, v in vars(obj).items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj
