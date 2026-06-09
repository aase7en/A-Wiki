"""
deepseek.py — Tier 1 sync adapter (DeepSeek V4-Flash-Base).

DeepSeek exposes an OpenAI-compatible Chat Completions endpoint. We use
stdlib urllib so this adapter has zero dependencies beyond the standard
library — keeping the fastest path also the leanest.

One IngestRequest = one HTTP call (sequential). 1-20 files is the sweet
spot; for >20 files, escalate to Tier 2 (OpenAI batch) which gets the
50% discount.
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


class DeepSeekAdapter(Adapter):
    name = "deepseek"
    mode = "realtime"

    def _api_key(self) -> str:
        key = fetch_secret(self.secret_name)
        if not key:
            raise RuntimeError(
                f"Secret {self.secret_name} not found in drive/.secrets — "
                "run `python scripts/lib/drive_secrets.py --check`"
            )
        return key

    def _call_once(self, req: IngestRequest, api_key: str) -> IngestResult:
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
            "model": self.model,
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
                custom_id=req.custom_id,
                slug=req.slug,
                raw_path=req.raw_path,
                tier=req.tier,
                success=False,
                error=f"HTTP {e.code}: {err_body[:300]}",
            )
        except urllib.error.URLError as e:
            return IngestResult(
                custom_id=req.custom_id,
                slug=req.slug,
                raw_path=req.raw_path,
                tier=req.tier,
                success=False,
                error=f"network error: {e}",
            )

        try:
            choice = data["choices"][0]
            content = choice["message"]["content"] or ""
        except (KeyError, IndexError):
            return IngestResult(
                custom_id=req.custom_id,
                slug=req.slug,
                raw_path=req.raw_path,
                tier=req.tier,
                success=False,
                error=f"unexpected response shape: {str(data)[:300]}",
            )

        usage = data.get("usage", {})
        return IngestResult(
            custom_id=req.custom_id,
            slug=req.slug,
            raw_path=req.raw_path,
            tier=req.tier,
            success=True,
            content=content,
            tokens_in=int(usage.get("prompt_tokens", 0)),
            tokens_out=int(usage.get("completion_tokens", 0)),
            metadata={"finish_reason": choice.get("finish_reason", "")},
        )

    def submit(self, requests: list[IngestRequest]) -> dict[str, Any]:
        api_key = self._api_key()
        results: list[IngestResult] = []
        for i, req in enumerate(requests):
            results.append(self._call_once(req, api_key))
            if i < len(requests) - 1:
                time.sleep(0.2)
        return {"mode": "realtime", "results": results}
