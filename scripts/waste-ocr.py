#!/usr/bin/env python3
"""
Waste Form OCR — Python CLI edition (v1.0.0)
============================================
ทางเลือกแทน Tampermonkey userscript — รันใน terminal ไม่ต้องเปิดเบราว์เซอร์
หลีกเลี่ยงปัญหา ESET business policy ที่ block Tampermonkey/extension

Usage:
    python scripts/waste-ocr.py ใบขยะ.jpg
    python scripts/waste-ocr.py รายงาน.png --provider cascade
    python scripts/waste-ocr.py *.jpg --date 2026-08-05
    python scripts/waste-ocr.py ใบขยะ.jpg --json          # output JSON only
    python scripts/waste-ocr.py --stats                    # ดู correlation stats
    python scripts/waste-ocr.py --reset-correlation        # ล้าง correlation

Features (พอร์ตจาก userscript v1.5.1):
    • 3 providers: gemini (single-shot) | typhoon (2-call) | cascade (Typhoon OCR → Gemini)
    • Dynamic model selection (auto-detect deprecated, list models live)
    • Correlation engine (recorder × location จากทุกครั้งที่ run)
    • Teaching history (correction log สำหรับ auto-prompt)
    • File-based storage (ไม่ใช่ Tampermonkey storage)
    • Custom OCR hints + staff-location rules (dynamic)

Storage:
    drive/.secrets                          ← API keys (gitignored)
    drive/personal-tools/waste-ocr/         ← state files (gitignored)
        ├── settings.json                   ← custom hints + provider
        ├── correlation.json                ← recorder×location counts
        ├── teaching_history.json           ← corrections log
        └── model_selection.json            ← model per slot

Requirements: pip install httpx
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    print("❌ ติดตั้ง httpx ก่อน: pip install httpx", file=sys.stderr)
    sys.exit(1)


# ============================================================================
# CONFIG — paths + defaults
# ============================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
DRIVE = REPO_ROOT / "drive"
STATE_DIR = DRIVE / "personal-tools" / "waste-ocr"
SECRETS_FILE = DRIVE / ".secrets"

# Providers
PROVIDERS = {
    "gemini": {
        "label": "🔬 Gemini 2.5 Flash (single-shot)",
        "pipeline": "single-shot",
        "env_key": "GEMINI_API_KEY",
    },
    "typhoon": {
        "label": "🌊 Typhoon OCR + LLM (2-call)",
        "pipeline": "two-shot",
        "env_key": "TYPHOON_API_KEY",
    },
    "cascade": {
        "label": "🌊🔬 Cascade (Typhoon OCR → Gemini Reasoning)",
        "pipeline": "cascade",
        "env_key": "__cascade__",  # ใช้ key ทั้งสองตัว
    },
}
DEFAULT_PROVIDER = "cascade"

# Endpoints
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
TYPHOON_BASE = "https://api.opentyphoon.ai/v1/chat/completions"

# Seed model defaults (dynamic — auto-detect deprecated)
MODEL_DEFAULTS = {
    "gemini": "gemini-flash-latest",   # 2026-08: gemini-2.5-flash deprecated สำหรับ new users
    "typhoonLlm": "typhoon-v2.1-12b-instruct",
    "typhoonOcr": "typhoon-ocr",
}
DEPRECATED_MODELS = {
    "gemini-2.5-flash": "gemini-flash-latest",
    "gemini-2.5-flash-001": "gemini-flash-latest",
}

# v1.5 OCR prompt — copied from typhoon_ocr SDK ocr_utils.py PROMPTS_SYS['v1.5']
TYPHOON_OCR_PROMPT = """Extract all text from the image.

Instructions:
- Only return the clean Markdown.
- Do not include any explanation or extra text.
- You must include all information on the page.

Formatting Rules:
- Tables: Render tables using Markdown table syntax.
- Equations: Render equations using LaTeX syntax with inline ($...$) and block ($$...$$).
- Page Numbers: Wrap page numbers in <page_number>...</page_number>.
- Checkboxes: Use ☐ for unchecked and ☑ for checked boxes."""

# System prompt — port จาก userscript SYSTEM_PROMPT
SYSTEM_PROMPT = """You extract data from Thai hospital waste-report forms (handwritten).
Return ONLY a JSON array. One object per row. No markdown fences.

Schema per row:
  row_number   integer
  date         "YYYY-MM-DD" (convert Thai Buddhist Era: subtract 543; if cell is '"', '-', 'น', 'ง', or dash, copy from row above)
  time         string as written, e.g. "15:00" or "07:35น."  (null if blank)
  weight_kg    number; if cell is "5+5" return the SUM (10). Double check digits 2↔9, 6↔5, 1↔4, 8↔9, 4↔3, 2↔1 in tens place. OPD weight is usually 10-39, rarely 40+. null if blank.
  weight_expr  optional string; if handwritten weight is addition expression like "5+5", keep it here while weight_kg is computed sum.
  location     normalize to one of: OPD | Ward | ER | OPD+ER | โรงครัว | เวช | ฝังเข็ม | แผนไทย+ฝังเข็ม | แผนไทย | บ่อบำบัด
  secondary_location optional; null unless one row combines exactly two departments under one weight.
  recorder     staff name(s) as written (multiple joined with "+"), null if blank

Known confusions to avoid:
  วอร์ด ≠ จอดรถ      (it's Ward)
  เวช  ≠ ลาว        (it's เวชกรรม)
  แผนไทย+ฝังเข็ม ≠ แผนไทย+ฝ่ายแม่

Staff-location patterns are learned dynamically (see STAFF-LOCATION CORRELATION section).
When correlation says recorder "usually at X (high%)", use as strong prior but respect weight/time context.

Add a final object {"_meta": {"confidence": 0..1, "unclear": [...]}} if quality is low.
Return ONLY the JSON array."""


# ============================================================================
# STORAGE — file-based JSON state
# ============================================================================

def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_settings() -> dict:
    return _read_json(STATE_DIR / "settings.json", {
        "provider": DEFAULT_PROVIDER,
        "custom_hints": "",
        "models": dict(MODEL_DEFAULTS),
    })


def save_settings(s: dict) -> None:
    _write_json(STATE_DIR / "settings.json", s)


def load_correlation() -> dict:
    return _read_json(STATE_DIR / "correlation.json", {"recorder_location": {}})


def save_correlation(c: dict) -> None:
    _write_json(STATE_DIR / "correlation.json", c)


def load_teaching_history() -> list:
    h = _read_json(STATE_DIR / "teaching_history.json", [])
    return h if isinstance(h, list) else []


def save_teaching_history(h: list) -> None:
    # cap at 120 entries (เหมือน userscript)
    _write_json(STATE_DIR / "teaching_history.json", h[:120])


# ============================================================================
# SECRETS — read from drive/.secrets (gitignored)
# ============================================================================

def get_secret(key_name: str, fallback_env: str | None = None) -> str | None:
    """อ่าน key จาก drive/.secrets ก่อน → fallback ที่ env var"""
    # 1. จาก drive/.secrets
    if SECRETS_FILE.exists():
        for line in SECRETS_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == key_name:
                return v.strip() or None
    # 2. env var fallback
    if fallback_env:
        v = os.environ.get(fallback_env)
        if v:
            return v
    return None


def get_keys_for_provider(provider: str) -> dict[str, str]:
    """Return dict ของ keys ที่จำเป็นสำหรับ provider นั้น"""
    keys = {}
    if provider in ("gemini", "cascade"):
        keys["gemini"] = get_secret("GEMINI_API_KEY", "GEMINI_API_KEY")
    if provider in ("typhoon", "cascade"):
        keys["typhoon"] = get_secret("TYPHOON_API_KEY", "TYPHOON_API_KEY")
    return keys


# ============================================================================
# MODEL — dynamic selection + auto-migrate deprecated
# ============================================================================

def get_active_model(slot: str) -> str:
    settings = load_settings()
    model = settings.get("models", {}).get(slot, MODEL_DEFAULTS.get(slot))
    # auto-migrate deprecated
    if model in DEPRECATED_MODELS:
        migrated = DEPRECATED_MODELS[model]
        _update_model_slot(slot, migrated)
        return migrated
    return model or MODEL_DEFAULTS.get(slot, "")


def _update_model_slot(slot: str, model: str) -> None:
    s = load_settings()
    s.setdefault("models", {})[slot] = model
    save_settings(s)


def list_gemini_models(api_key: str) -> list[str]:
    """List models live จาก Gemini API"""
    try:
        r = httpx.get(
            f"{GEMINI_BASE}/models?key={api_key}",
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        models = []
        for m in data.get("models", []):
            methods = m.get("supportedGenerationMethods", [])
            if "generateContent" not in methods:
                continue
            name = m.get("name", "").replace("models/", "")
            if not name:
                continue
            # กรอง embedding/tts/image ออก
            if re.search(r"embedding|text-to-speech|tts|aqua|imagen|veo", name, re.IGNORECASE):
                continue
            models.append(name)
        return sorted(models) if models else [MODEL_DEFAULTS["gemini"]]
    except Exception as e:
        print(f"⚠ list Gemini models failed: {e}", file=sys.stderr)
        return [MODEL_DEFAULTS["gemini"]]


def list_typhoon_models(api_key: str) -> list[str]:
    """List models live จาก Typhoon API"""
    try:
        r = httpx.get(
            f"https://api.opentyphoon.ai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        # Typhoon API return shape: อาจเป็น {data: [{id:...}]} หรือ list[{id:...}] ตรงๆ
        if isinstance(data, dict):
            items = data.get("data", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []
        ids = [m.get("id") for m in items if isinstance(m, dict) and m.get("id")]
        return sorted(ids) if ids else [MODEL_DEFAULTS["typhoonLlm"]]
    except Exception as e:
        print(f"⚠ list Typhoon models failed: {e}", file=sys.stderr)
        return [MODEL_DEFAULTS["typhoonLlm"]]


# ============================================================================
# CORRELATION ENGINE — recorder × location
# ============================================================================

def record_correlation(rows: list[dict]) -> int:
    """อัปเดต counter จาก rows ที่ user ยืนยัน (output จาก OCR)"""
    counts = load_correlation()
    if "recorder_location" not in counts:
        counts["recorder_location"] = {}
    added = 0
    for r in rows:
        if not r or not r.get("recorder") or not r.get("location"):
            continue
        names = [n.strip() for n in str(r["recorder"]).split("+") if n.strip()]
        for name in names:
            if name not in counts["recorder_location"]:
                counts["recorder_location"][name] = {}
            loc = r["location"]
            counts["recorder_location"][name][loc] = counts["recorder_location"][name].get(loc, 0) + 1
            added += 1
    if added:
        save_correlation(counts)
    return added


def build_staff_location_rules(top_n: int = 8) -> list[dict]:
    """สร้าง prompt rules: 'อ้อย usually at OPD (47/50 = 94%); sometimes Ward (3)'"""
    counts = load_correlation()
    rl = counts.get("recorder_location", {})
    rules = []
    for name, locs in rl.items():
        total = sum(locs.values())
        if total < 2:
            continue
        sorted_locs = sorted(locs.items(), key=lambda x: -x[1])
        top_loc, top_count = sorted_locs[0]
        top_pct = round((top_count / total) * 100)
        others = [(l, n) for l, n in sorted_locs[1:] if n >= 1]
        primary = f"{top_loc} ({top_count}/{total} = {top_pct}%)"
        secondary = "; sometimes " + ", ".join(f"{l} ({n})" for l, n in others) if others else ""
        rules.append({
            "name": name,
            "total": total,
            "top_loc": top_loc,
            "top_pct": top_pct,
            "text": f'- Recorder "{name}" usually at {primary}{secondary}',
        })
    rules.sort(key=lambda r: -r["total"])
    return rules[:top_n]


# ============================================================================
# PROMPT BUILDER — port จาก userscript buildSystemPrompt
# ============================================================================

def build_system_prompt() -> str:
    s = load_settings()
    prompt = SYSTEM_PROMPT

    # Staff-location correlation (dynamic)
    rules = build_staff_location_rules()
    if rules:
        total_evidence = sum(r["total"] for r in rules)
        prompt += f"\n\nSTAFF-LOCATION CORRELATION (learned from {total_evidence} past confirmed rows — use as strong prior when reading location for a known recorder, but respect weight/time context):\n" + "\n".join(r["text"] for r in rules)

    # Year hint
    now = datetime.now()
    ce_year = now.year
    be_year = ce_year + 543
    ce2 = str(ce_year)[-2:]
    be2 = str(be_year)[-2:]
    prompt += f"\n\nDATE YEAR RULE: Current CE year is {ce_year}; current Thai Buddhist Era year is {be_year}. If handwritten year is \"{be2}\", interpret as BE {be_year} → CE {ce_year}."

    # Date validation
    today_iso = now.strftime("%Y-%m-%d")
    prev_month = (now.year, now.month - 1) if now.month > 1 else (now.year - 1, 12)
    prev_month_str = f"{prev_month[0]}-{prev_month[1]:02d}"
    prompt += f"\n\nDATE VALIDATION RULES:\n1. SEQUENCE: row dates must be non-decreasing as row_number increases.\n2. FUTURE DATE IS WRONG: Today is {today_iso}. If any date > today, subtract 1 from month; common cause: form shows dates in {prev_month_str} (previous month).\n3. NEVER output a future date."

    # Custom hints
    hints = (s.get("custom_hints") or "").strip()
    if hints:
        prompt += f"\n\nADDITIONAL USER CORRECTIONS (override defaults):\n{hints}"

    # Teaching history (last 15)
    history = load_teaching_history()[:15]
    if history:
        lines = []
        for h in history:
            bits = []
            if h.get("date"):
                bits.append(f"date {h['date']}")
            if h.get("row_number"):
                bits.append(f"raw row {h['row_number']}")
            if h.get("location"):
                bits.append(f"location {h['location']}")
            ctx = ", ".join(bits) if bits else ""
            computed = f" (computed {h['computed']})" if h.get("computed") is not None else ""
            note = f" Note: {h['note']}" if h.get("note") else ""
            lines.append(f"- {h['field']}: read \"{h['original']}\" but corrected to \"{h['corrected']}\"{computed}{' (' + ctx + ')' if ctx else ''}.{note}")
        prompt += "\n\nWASTE OCR TEACHING HISTORY (domain corrections from past edits; apply these patterns):\n" + "\n".join(lines)

    return prompt


# ============================================================================
# OCR PROVIDERS
# ============================================================================

@dataclass
class OCRResult:
    rows: list[dict]
    raw: Any = None
    provider: str = ""
    markdown_intermediate: str | None = None  # cascade/typhoon เท่านั้น


def file_to_base64(path: Path) -> tuple[str, str]:
    """Return (base64_data, mime_type)"""
    ext = path.suffix.lower()
    mime = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".gif": "image/gif", ".bmp": "image/bmp",
    }.get(ext, "image/jpeg")
    return base64.b64encode(path.read_bytes()).decode("ascii"), mime


def gemini_call(api_key: str, b64: str, mime: str, model: str) -> list[dict]:
    """Single-shot: image → JSON array"""
    body = {
        "system_instruction": {"parts": [{"text": build_system_prompt()}]},
        "contents": [{
            "role": "user",
            "parts": [
                {"inline_data": {"mime_type": mime, "data": b64}},
                {"text": "Extract all rows from this hospital waste report."},
            ],
        }],
        "generationConfig": {"temperature": 0.1, "response_mime_type": "application/json"},
    }
    r = httpx.post(
        f"{GEMINI_BASE}/models/{model}:generateContent?key={api_key}",
        json=body, timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"].get("message", "Gemini error"))
    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.MULTILINE).strip()
    if not text:
        raise RuntimeError("Empty Gemini response")
    parsed = json.loads(text)
    return parsed if isinstance(parsed, list) else parsed.get("rows", [parsed])


def typhoon_ocr_call(api_key: str, b64: str, mime: str, model: str) -> str:
    """Stage 1: image → Markdown"""
    body = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": TYPHOON_OCR_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ],
        }],
        "max_tokens": 16384,
        "temperature": 0.1,
        "top_p": 0.6,
        "repetition_penalty": 1.1,
    }
    r = httpx.post(
        TYPHOON_BASE,
        json=body,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=90,
    )
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"].get("message", "Typhoon OCR error"))
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not text:
        raise RuntimeError("Empty Typhoon OCR Markdown")
    return text


def typhoon_llm_call(api_key: str, markdown: str, model: str) -> list[dict]:
    """Stage 2: Markdown → JSON array"""
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": f"Below is OCR Markdown from a Thai hospital waste report.\nExtract all rows into JSON schema from system prompt.\n\n--- OCR Markdown ---\n{markdown}\n--- end ---"},
        ],
        "temperature": 0.1,
        "top_p": 0.6,
        "response_format": {"type": "json_object"},
    }
    r = httpx.post(
        TYPHOON_BASE,
        json=body,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"].get("message", "Typhoon LLM error"))
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    if not text:
        raise RuntimeError("Empty Typhoon LLM response")
    parsed = json.loads(text)
    return parsed if isinstance(parsed, list) else parsed.get("rows", parsed.get("data", [parsed]))


def gemini_reasoning_call(api_key: str, markdown: str, model: str) -> list[dict]:
    """Cascade stage 2: Markdown → JSON array via Gemini"""
    body = {
        "system_instruction": {"parts": [{"text": build_system_prompt()}]},
        "contents": [{
            "role": "user",
            "parts": [{
                "text": f"Below is OCR Markdown from a Thai hospital waste report (extracted by Typhoon OCR).\nApply ALL schema rules from system prompt (BE→CE, weight sum, location normalization, date validation, staff hints, teaching history).\nReturn JSON array.\n\n--- OCR Markdown ---\n{markdown}\n--- end ---"
            }],
        }],
        "generationConfig": {"temperature": 0.1, "response_mime_type": "application/json"},
    }
    r = httpx.post(
        f"{GEMINI_BASE}/models/{model}:generateContent?key={api_key}",
        json=body, timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"].get("message", "Gemini reasoning error"))
    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.MULTILINE).strip()
    if not text:
        raise RuntimeError("Empty Gemini reasoning response")
    parsed = json.loads(text)
    return parsed if isinstance(parsed, list) else parsed.get("rows", [parsed])


def run_ocr(image_path: Path, provider: str, verbose: bool = False) -> OCRResult:
    """Run OCR ตาม provider"""
    keys = get_keys_for_provider(provider)
    missing = [k for k, v in keys.items() if not v]
    if missing:
        raise RuntimeError(f"ไม่มี API key สำหรับ: {', '.join(missing)} — เช็ค drive/.secrets หรือ env var")

    b64, mime = file_to_base64(image_path)

    if provider == "gemini":
        model = get_active_model("gemini")
        if verbose:
            print(f"🔬 Gemini ({model}) single-shot...", file=sys.stderr)
        rows = gemini_call(keys["gemini"], b64, mime, model)
        return OCRResult(rows=rows, provider=provider)

    if provider == "typhoon":
        ocr_model = get_active_model("typhoonOcr")
        llm_model = get_active_model("typhoonLlm")
        if verbose:
            print(f"🌊 Typhoon OCR ({ocr_model}) → Markdown...", file=sys.stderr)
        md = typhoon_ocr_call(keys["typhoon"], b64, mime, ocr_model)
        if verbose:
            preview = md[:600] + ("…" if len(md) > 600 else "")
            print(f"[typhoon] Markdown preview:\n{preview}", file=sys.stderr)
            print(f"🌊 Typhoon LLM ({llm_model}) → JSON...", file=sys.stderr)
        rows = typhoon_llm_call(keys["typhoon"], md, llm_model)
        return OCRResult(rows=rows, provider=provider, markdown_intermediate=md)

    if provider == "cascade":
        ocr_model = get_active_model("typhoonOcr")
        gem_model = get_active_model("gemini")
        if verbose:
            print(f"🌊 Typhoon OCR ({ocr_model}) → Markdown...", file=sys.stderr)
        md = typhoon_ocr_call(keys["typhoon"], b64, mime, ocr_model)
        if verbose:
            preview = md[:600] + ("…" if len(md) > 600 else "")
            print(f"[cascade] Markdown preview:\n{preview}", file=sys.stderr)
            print(f"🔬 Gemini Reasoning ({gem_model}) → JSON...", file=sys.stderr)
        rows = gemini_reasoning_call(keys["gemini"], md, gem_model)
        return OCRResult(rows=rows, provider=provider, markdown_intermediate=md)

    raise RuntimeError(f"Unknown provider: {provider}")


# ============================================================================
# OUTPUT — terminal table + JSON
# ============================================================================

def render_table(rows: list[dict]) -> str:
    """Render rows เป็น ASCII table"""
    data_rows = [r for r in rows if r and r.get("row_number") is not None and not r.get("_meta")]
    if not data_rows:
        return "_(ไม่มี rows)_"

    lines = []
    lines.append("┌──────┬────────┬─────────┬─────────────────┬─────────────────┐")
    lines.append("│ Row  │ Time   │ Weight  │ Location        │ Recorder        │")
    lines.append("├──────┼────────┼─────────┼─────────────────┼─────────────────┤")
    for r in data_rows:
        rn = str(r.get("row_number", "?"))[:4].ljust(4)
        t = (r.get("time") or "-")[:8].ljust(8)
        kg = r.get("weight_kg")
        expr = r.get("weight_expr")
        kg_str = (f"{expr}={kg}" if expr else str(kg)) if kg is not None else "-"
        kg_str = kg_str[:9].ljust(9)
        loc = (r.get("location") or "-")[:15].ljust(15)
        sec = r.get("secondary_location")
        if sec:
            loc = loc[:12].ljust(12) + "+s "
        rec = (r.get("recorder") or "-")[:15].ljust(15)
        lines.append(f"│ {rn} │ {t} │ {kg_str} │ {loc} │ {rec} │")
    lines.append("└──────┴────────┴─────────┴─────────────────┴─────────────────┘")
    return "\n".join(lines)


def render_summary(rows: list[dict]) -> str:
    """สรุปรวม kg ต่อ location"""
    data_rows = [r for r in rows if r and r.get("row_number") is not None and not r.get("_meta")]
    by_loc = {}
    for r in data_rows:
        loc = r.get("location")
        kg = r.get("weight_kg")
        if loc and kg is not None:
            by_loc[loc] = by_loc.get(loc, 0) + float(kg)
    if not by_loc:
        return ""
    lines = ["📊 สรุปรวมต่อแผนก:"]
    for loc, total in sorted(by_loc.items()):
        lines.append(f"   {loc}: {total:.1f} kg")
    return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================

def cmd_ocr(args: argparse.Namespace) -> int:
    settings = load_settings()
    provider = args.provider or settings.get("provider", DEFAULT_PROVIDER)

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"❌ ไม่พบไฟล์: {image_path}", file=sys.stderr)
        return 1

    print(f"📷 OCR: {image_path.name} ({image_path.stat().st_size / 1024:.0f} KB)", file=sys.stderr)
    print(f"🔌 Provider: {PROVIDERS[provider]['label']}", file=sys.stderr)
    print("", file=sys.stderr)

    try:
        result = run_ocr(image_path, provider, verbose=True)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1

    rows = result.rows if isinstance(result.rows, list) else result.rows.get("rows", [])

    # อัปเดต correlation engine
    added = record_correlation(rows)
    if added:
        print(f"\n🧠 อัปเดต correlation engine: {added} entries", file=sys.stderr)

    # แยก meta
    data_rows = [r for r in rows if r and not r.get("_meta")]
    meta = next((r.get("_meta") for r in rows if r and r.get("_meta")), None)

    if args.json:
        # JSON only — สำหรับ copy หรือ pipe
        print(json.dumps(data_rows, ensure_ascii=False, indent=2))
    else:
        print("\n" + render_table(rows), file=sys.stderr)
        summary = render_summary(rows)
        if summary:
            print("\n" + summary, file=sys.stderr)
        if meta:
            conf = meta.get("confidence", "?")
            unclear = meta.get("unclear", [])
            print(f"\n⚠️  Confidence: {conf}", file=sys.stderr)
            if unclear:
                print(f"   Unclear: {', '.join(unclear)}", file=sys.stderr)
        print(f"\n📋 JSON สำหรับ copy:", file=sys.stderr)
        print(json.dumps({r.get("location", "?"): r.get("weight_kg", 0) for r in data_rows}, ensure_ascii=False))

    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """แสดง correlation stats"""
    counts = load_correlation()
    rl = counts.get("recorder_location", {})
    if not rl:
        print("_(ยังไม่มีข้อมูล correlation — รัน OCR บ่อยๆ แล้วจะสะสม)_")
        return 0

    print(f"🧠 Staff-Location Correlation ({len(rl)} staff)")
    print()

    # รวบ locations ทั้งหมด
    all_locs = set()
    for locs in rl.values():
        all_locs.update(locs.keys())
    locations = sorted(all_locs)

    # หา max count
    max_count = max((n for locs in rl.values() for n in locs.values()), default=1)

    # Header
    header = "Staff".ljust(12) + " | " + " | ".join(l[:8].ljust(8) for l in locations) + " | รวม"
    print(header)
    print("-" * len(header))

    # Rows (sorted by total desc)
    sorted_names = sorted(rl.keys(), key=lambda n: -sum(rl[n].values()))
    for name in sorted_names:
        locs = rl[name]
        total = sum(locs.values())
        cells = []
        for l in locations:
            n = locs.get(l, 0)
            if n == 0:
                cells.append("·".ljust(8))
            else:
                pct = round(n / total * 100)
                # intensity bar
                intensity = n / max_count
                bar = "█" * int(intensity * 4)
                cells.append(f"{n}{bar}{pct}%".ljust(8))
        print(f"{name[:12].ljust(12)} | " + " | ".join(cells) + f" | {total}")

    return 0


def cmd_reset_correlation(args: argparse.Namespace) -> int:
    """ล้าง correlation"""
    if not args.yes and input("ล้าง correlation ทั้งหมด? (y/N) ").lower() != "y":
        print("ยกเลิก")
        return 0
    save_correlation({"recorder_location": {}})
    print("✓ ล้าง correlation แล้ว")
    return 0


def cmd_list_models(args: argparse.Namespace) -> int:
    """List models live จาก provider APIs"""
    provider = args.list_models or "all"
    if provider not in ("gemini", "typhoon", "all"):
        print(f"❌ unknown provider: {provider} (gemini | typhoon | all)")
        return 1
    if provider in ("gemini", "all"):
        key = get_secret("GEMINI_API_KEY")
        if key:
            print(f"🔬 Gemini models (current: {get_active_model('gemini')}):")
            for m in list_gemini_models(key):
                marker = " ← active" if m == get_active_model("gemini") else ""
                print(f"   {m}{marker}")
        else:
            print("⚠ ไม่มี GEMINI_API_KEY")
    if provider in ("typhoon", "all"):
        key = get_secret("TYPHOON_API_KEY")
        if key:
            typhoon_models = list_typhoon_models(key)
            print(f"\n🌊 Typhoon models:")
            print(f"   OCR (current: {get_active_model('typhoonOcr')}):")
            for m in typhoon_models:
                marker = " ← active" if m == get_active_model("typhoonOcr") else ""
                print(f"     {m}{marker}")
            print(f"   LLM (current: {get_active_model('typhoonLlm')}):")
            for m in typhoon_models:
                marker = " ← active" if m == get_active_model("typhoonLlm") else ""
                print(f"     {m}{marker}")
        else:
            print("⚠ ไม่มี TYPHOON_API_KEY")
    return 0


def cmd_set_model(args: argparse.Namespace) -> int:
    """ตั้ง model สำหรับ slot"""
    _update_model_slot(args.slot, args.model)
    print(f"✓ model {args.slot} = {args.model}")
    return 0


def cmd_set_provider(args: argparse.Namespace) -> int:
    """ตั้ง default provider"""
    if args.provider not in PROVIDERS:
        print(f"❌ unknown provider: {args.provider} (choices: {', '.join(PROVIDERS.keys())})")
        return 1
    s = load_settings()
    s["provider"] = args.provider
    save_settings(s)
    print(f"✓ default provider = {args.provider} ({PROVIDERS[args.provider]['label']})")
    return 0


def cmd_set_hints(args: argparse.Namespace) -> int:
    """ตั้ง custom OCR hints"""
    s = load_settings()
    if args.hints == "-":
        # อ่านจาก stdin
        s["custom_hints"] = sys.stdin.read().strip()
    elif args.hints:
        s["custom_hints"] = args.hints
    else:
        # แสดงค่าปัจจุบัน
        print(s.get("custom_hints", "") or "(empty)")
        return 0
    save_settings(s)
    print("✓ บันทึก custom hints แล้ว")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Waste Form OCR — Python CLI edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ใบขยะ.jpg                    # OCR รูปเดียว
  %(prog)s รายงาน.png --provider gemini # สลับ provider
  %(prog)s img.jpg --json               # output JSON only (pipe)
  %(prog)s --stats                      # ดู correlation heatmap
  %(prog)s --list-models                # ดู model ที่ใช้ได้
  %(prog)s --set-model gemini gemini-3-flash-preview
  %(prog)s --reset-correlation          # ล้าง correlation
""",
    )
    parser.add_argument("image", nargs="?", help="path รูปใบรายงานขยะ (.jpg/.png)")
    parser.add_argument("--provider", choices=list(PROVIDERS.keys()), help="provider (default: cascade)")
    parser.add_argument("--json", action="store_true", help="output JSON only (สำหรับ pipe/copy)")
    parser.add_argument("--stats", action="store_true", help="แสดง correlation stats")
    parser.add_argument("--reset-correlation", action="store_true", help="ล้าง correlation data")
    parser.add_argument("--list-models", nargs="?", const="all", metavar="PROVIDER", help="list models live จาก API")
    parser.add_argument("--set-model", nargs=2, metavar=("SLOT", "MODEL"), help="ตั้ง model (slot: gemini|typhoonOcr|typhoonLlm)")
    parser.add_argument("--set-provider", metavar="PROVIDER", help="ตั้ง default provider")
    parser.add_argument("--set-hints", nargs="?", const="__show__", metavar="TEXT", help="ตั้ง custom OCR hints ('-' = stdin)")
    parser.add_argument("-y", "--yes", action="store_true", help="confirm อัตโนมัติ")
    parser.add_argument("-v", "--version", action="version", version="waste-ocr.py v1.0.0")

    args = parser.parse_args()

    # Subcommands
    if args.stats:
        return cmd_stats(args)
    if args.reset_correlation:
        return cmd_reset_correlation(args)
    if args.list_models:
        return cmd_list_models(args)
    if args.set_model:
        args.slot, args.model = args.set_model
        return cmd_set_model(args)
    if args.set_provider:
        args.provider = args.set_provider
        return cmd_set_provider(args)
    if args.set_hints and args.set_hints != "__show__":
        return cmd_set_hints(args)
    elif args.set_hints == "__show__":
        args.hints = None
        return cmd_set_hints(args)

    # Default: OCR
    if not args.image:
        parser.print_help()
        return 1
    return cmd_ocr(args)


if __name__ == "__main__":
    sys.exit(main())
