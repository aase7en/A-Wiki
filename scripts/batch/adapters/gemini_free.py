"""
gemini_free.py — Fallback Tier 0 adapter for Google Gemini free tier.

Used when OpenRouter free model is rate-limited. Uses Gemini's native
generateContent endpoint (not OpenAI-compatible).

Gemini Flash free tier limits change frequently; scout.py is the source
of truth for current model name + rate limits.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "batch"))

from drive_secrets import fetch_secret  # noqa: E402

from adapters import Adapter, IngestRequest, IngestResult  # noqa: E402
from prompt_template import SYSTEM_PROMPT, build_user_message, read_raw  # noqa: E402


class GeminiFreeAdapter(Adapter):
    name = "gemini-free"
    mode = "realtime"

    def _api_key(self) -> str:
        key = fetch_secret(self.secret_name)
        if not key:
            raise RuntimeError(f"Secret {self.secret_name} not found in drive/.secrets")
        return key

    def _call_once(self, req: IngestRequest, api_key: str) -> IngestResult:
        raw_text = read_raw(REPO_ROOT / req.raw_path)
        user_message = build_user_message(
            raw_path=req.raw_path, raw_text=raw_text, slug=req.slug,
            date_ingested=req.date_ingested, tier=req.tier, domain_hint=req.domain_hint,
        )
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": user_message}]}],
            "generationConfig": {"temperature": 0.2},
        }
        url = f"{self.endpoint.rstrip('/')}/models/{self.model}:generateContent?key={api_key}"
        request = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")
            except Exception:
                pass
            return IngestResult(
                custom_id=req.custom_id, slug=req.slug, raw_path=req.raw_path,
                tier=req.tier, success=False,
                error=f"HTTP {e.code}: {err_body[:300]}",
            )
        except urllib.error.URLError as e:
            return IngestResult(
                custom_id=req.custom_id, slug=req.slug, raw_path=req.raw_path,
                tier=req.tier, success=False, error=f"network error: {e}",
            )

        try:
            candidate = data["candidates"][0]
            parts = candidate.get("content", {}).get("parts", [])
            content = "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError):
            return IngestResult(
                custom_id=req.custom_id, slug=req.slug, raw_path=req.raw_path,
                tier=req.tier, success=False,
                error=f"unexpected response shape: {str(data)[:300]}",
            )
        usage = data.get("usageMetadata", {})
        return IngestResult(
            custom_id=req.custom_id, slug=req.slug, raw_path=req.raw_path,
            tier=req.tier, success=True, content=content,
            tokens_in=int(usage.get("promptTokenCount", 0)),
            tokens_out=int(usage.get("candidatesTokenCount", 0)),
            metadata={"finish_reason": candidate.get("finishReason", ""), "model": self.model},
        )

    def submit(self, requests: list[IngestRequest]) -> dict[str, Any]:
        api_key = self._api_key()
        results: list[IngestResult] = []
        for i, req in enumerate(requests):
            results.append(self._call_once(req, api_key))
            if i < len(requests) - 1:
                time.sleep(0.5)
        return {"mode": "realtime", "results": results}
