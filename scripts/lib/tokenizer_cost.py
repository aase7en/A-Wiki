"""tokenizer_cost — shared token-counting backend resolver.

Extracted verbatim from scripts/format-cost.py `_build_counter`
(WO-AWIKI-SKILLECO-14) so format-cost.py and token-ab-measure.py share one
resolver: tiktoken -> anthropic (key-gated) -> char/4 proxy. Never raises;
always falls back to the deterministic proxy.
"""
from __future__ import annotations

import os
from typing import Callable, Tuple


def build_counter(requested: str) -> Tuple[Callable[[str], int], str]:
    """Return (count_fn, backend_name). Never raises — always falls back to proxy."""
    proxy = (lambda text: max(1, round(len(text) / 4)), "char/4 proxy")

    if requested == "proxy":
        return proxy

    if requested in ("auto", "tiktoken"):
        try:
            import tiktoken  # type: ignore
            enc = tiktoken.get_encoding("cl100k_base")
            return (lambda text: len(enc.encode(text)), "tiktoken cl100k_base")
        except Exception:
            pass
        if requested == "tiktoken":
            return proxy

    if requested in ("auto", "anthropic"):
        try:
            # The SDK constructs fine without a key and only raises when the
            # API is called — by then output is mid-flight. Never select this
            # backend without a usable key (CI has the package but no key).
            if not os.environ.get("ANTHROPIC_API_KEY"):
                raise RuntimeError("anthropic installed but ANTHROPIC_API_KEY unset")
            import anthropic  # type: ignore
            client = anthropic.Anthropic()

            def _count(text: str) -> int:
                r = client.beta.messages.count_tokens(
                    model="claude-opus-4-8",
                    messages=[{"role": "user", "content": text}],
                    betas=["token-counting-2024-11-01"],
                )
                return r.input_tokens
            return (_count, "anthropic token-counting API")
        except Exception:
            pass

    return proxy
