"""
openrouter_free.py — Tier 0 free-model adapter (OpenRouter free tier).

OpenRouter exposes an OpenAI-compatible Chat Completions endpoint. We use
stdlib urllib (same shape as deepseek.py) — zero extra deps. Model name
comes from cost-routing.conf (seed) or scout.py refreshed roster.

Pricing: $0 input / $0 output for any model with `pricing.prompt == "0"`
on /api/v1/models. The scout job validates the roster periodically.
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


class OpenRouterFreeAdapter(Adapter):
    name = "free"
    mode = "realtime"

    def _api_key(self) -> str:
        key = fetch_secret(self.secret_name)
        if not key:
            raise RuntimeError(
                f"Secret {self.secret_name} not found in drive/.secrets — "
                "needed for Tier 0 (OpenRouter free)"
            )
        return key

    def _resolve_model(self) -> str:
        """Honor 'openrouter:<id>' prefix; default to raw model string."""
        m = self.model
        if m.startswith("openrouter:"):
            return m.split(":", 1)[1]
        return m

    def _call_once(self, req: IngestRequest, api_key: str, model: str) -> IngestResult:
        raw_text = read_raw(REPO_ROOT / req.raw_path)
        user_message = build_user_message(
            raw_path=req.raw_path,
            raw_text=raw_text,
            slug=req.slug,
            date_ingested=req.date_ingested,
            tier=req.tier,
            domain_hint=req.domain_hint,
        )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.2,
            "stream": False,
        }
        url = self.endpoint.rstrip("/") + "/chat/completions"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/aase7en/A-Wiki",
                "X-Title": "A-Wiki Universal Ingest Harness",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body)
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
            choice = data["choices"][0]
            content = choice["message"]["content"] or ""
        except (KeyError, IndexError):
            return IngestResult(
                custom_id=req.custom_id, slug=req.slug, raw_path=req.raw_path,
                tier=req.tier, success=False,
                error=f"unexpected response shape: {str(data)[:300]}",
            )
        usage = data.get("usage", {})
        return IngestResult(
            custom_id=req.custom_id, slug=req.slug, raw_path=req.raw_path,
            tier=req.tier, success=True, content=content,
            tokens_in=int(usage.get("prompt_tokens", 0)),
            tokens_out=int(usage.get("completion_tokens", 0)),
            metadata={"finish_reason": choice.get("finish_reason", ""), "model": model},
        )

    def submit(self, requests: list[IngestRequest]) -> dict[str, Any]:
        api_key = self._api_key()
        model = self._resolve_model()
        results: list[IngestResult] = []
        for i, req in enumerate(requests):
            results.append(self._call_once(req, api_key, model))
            if i < len(requests) - 1:
                time.sleep(0.5)  # free tier rate limit margin
        return {"mode": "realtime", "results": results}
