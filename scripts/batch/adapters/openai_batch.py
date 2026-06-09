"""
openai_batch.py — Tier 2 batch adapter (OpenAI Batch API, e.g. gpt-4o-mini).

Flow: build JSONL → upload → batches.create → poll → download output file.
Batch SLA is 24h; user reruns poll.py / collect.py until status=completed.

Input JSONL stored in drive/batch-state/in/<batch_id>.jsonl (private),
output similarly under drive/batch-state/out/.
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


class OpenAIBatchAdapter(Adapter):
    name = "openai"
    mode = "batch"

    def _client(self):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError(
                "openai package required for Tier 2 — pip install openai"
            ) from e
        api_key = fetch_secret(self.secret_name)
        if not api_key:
            raise RuntimeError(f"Secret {self.secret_name} not found in drive/.secrets")
        return OpenAI(api_key=api_key, base_url=self.endpoint)

    def _build_jsonl(self, requests: list[IngestRequest]) -> Path:
        in_dir = state_dir() / "in"
        in_dir.mkdir(parents=True, exist_ok=True)
        path = in_dir / f"openai-{requests[0].custom_id}-{len(requests)}.jsonl"
        with path.open("w", encoding="utf-8") as fp:
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
                body = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.2,
                }
                fp.write(
                    json.dumps(
                        {
                            "custom_id": req.custom_id,
                            "method": "POST",
                            "url": "/v1/chat/completions",
                            "body": body,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        return path

    def submit(self, requests: list[IngestRequest]) -> dict[str, Any]:
        client = self._client()
        jsonl_path = self._build_jsonl(requests)
        with jsonl_path.open("rb") as fp:
            file_obj = client.files.create(file=fp, purpose="batch")
        batch = client.batches.create(
            input_file_id=file_obj.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"harness": "a-wiki", "n_files": str(len(requests))},
        )
        return {
            "mode": "batch",
            "batch_id": batch.id,
            "input_file_id": file_obj.id,
            "input_path": str(jsonl_path),
            "status": batch.status,
        }

    def poll(self, batch_id: str) -> dict[str, Any]:
        client = self._client()
        batch = client.batches.retrieve(batch_id)
        return {
            "status": batch.status,
            "request_counts": getattr(batch, "request_counts", None).__dict__ if getattr(batch, "request_counts", None) else {},
            "output_file_id": getattr(batch, "output_file_id", None),
            "error_file_id": getattr(batch, "error_file_id", None),
        }

    def collect(
        self,
        batch_id: str,
        requests_index: dict[str, IngestRequest],
    ) -> list[IngestResult]:
        client = self._client()
        batch = client.batches.retrieve(batch_id)
        if not batch.output_file_id:
            raise RuntimeError(
                f"Batch {batch_id} status={batch.status} — no output_file_id yet"
            )
        out_dir = state_dir() / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"openai-{batch_id}.jsonl"
        file_resp = client.files.content(batch.output_file_id)
        out_path.write_bytes(file_resp.read())

        results: list[IngestResult] = []
        with out_path.open("r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                custom_id = rec.get("custom_id", "")
                req = requests_index.get(custom_id)
                if req is None:
                    continue
                if rec.get("error"):
                    results.append(
                        IngestResult(
                            custom_id=custom_id,
                            slug=req.slug,
                            raw_path=req.raw_path,
                            tier=req.tier,
                            success=False,
                            error=json.dumps(rec["error"])[:300],
                        )
                    )
                    continue
                try:
                    body = rec["response"]["body"]
                    choice = body["choices"][0]
                    content = choice["message"]["content"] or ""
                    usage = body.get("usage", {})
                    results.append(
                        IngestResult(
                            custom_id=custom_id,
                            slug=req.slug,
                            raw_path=req.raw_path,
                            tier=req.tier,
                            success=True,
                            content=content,
                            tokens_in=int(usage.get("prompt_tokens", 0)),
                            tokens_out=int(usage.get("completion_tokens", 0)),
                            metadata={"finish_reason": choice.get("finish_reason", "")},
                        )
                    )
                except (KeyError, IndexError) as e:
                    results.append(
                        IngestResult(
                            custom_id=custom_id,
                            slug=req.slug,
                            raw_path=req.raw_path,
                            tier=req.tier,
                            success=False,
                            error=f"parse error: {e}",
                        )
                    )
        return results
