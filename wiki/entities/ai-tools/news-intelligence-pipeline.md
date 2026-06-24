# News Intelligence Pipeline

> **System:** News collection → filtering → light analysis → deep prediction
> **Cost:** ~$0.50/เดือน (97% ประหยัดกว่าสมาชิกรายเดือน)
> **Status:** ✅ Live on Hermes cron (Pi5)
> **Last updated:** 2026-06-24

## Architecture

```
Layer 1: DATA COLLECTION  🆓 Cron (no_agent, ทุก 4h)
         RSS + free APIs → raw/news-*.json

Layer 2: FILTERING        🆓 Python Script (no LLM)
         Dedup + keywords + TextBlob sentiment → structured/filtered-*.json

Layer 3: LIGHT ANALYSIS   🆓 Gemini 3.5 Flash (06:30 + 18:30)
         สรุปข่าว + sentiment แยกตลาด → Telegram report

Layer 4: DEEP PREDICTION  💲 GLM x.x (manual/PRO mode)
         เฉพาะข่าวแรง ≥ 7/10 หรือ user สั่ง "พยากรณ์ [asset]"

Layer 5: DELIVERY         Telegram + /opt/data/news/archive/
```

## Sources (10 sources, no API key needed)

| Source | Type | Items |
|--------|------|-------|
| Cointelegraph | RSS | 20 |
| CoinDesk | RSS | 20 |
| Decrypt | RSS | 20 |
| CryptoSlate | RSS | 10 |
| Reuters Finance | RSS | varies |
| BNN Bloomberg | RSS | varies |
| Prachachat (ไทย) | RSS | 20 |
| Thairath Biz (ไทย) | RSS | varies |
| Polymarket API | JSON | 20 markets |
| CoinGecko API | JSON | 20 coins |

## Cron Jobs (Hermes)

| Job | Schedule | Type | Model | Cost |
|-----|----------|------|-------|------|
| `news-collector` | ทุก 4 ชม. | no_agent (script only) | — | 🆓 |
| `news-analysis-morning` | 06:30 | Agent + script context | Gemini 3.5 Flash | 🆓 |
| `news-analysis-evening` | 18:30 | Agent + script context | Gemini 3.5 Flash | 🆓 |

## Data Flow

```
/opt/data/news/raw/           ← JSON ดิบ (Layer 1)
/opt/data/news/structured/    ← JSON กรอง + sentiment (Layer 2)
/opt/data/news/analysis/      ← JSON วิเคราะห์แล้ว (Layer 3)
/opt/data/news/prediction/    ← JSON พยากรณ์ (Layer 4)
```

## Scripts

| Script | Path | ภาษา | Libs |
|--------|------|------|------|
| fetch-news.py | `scripts/news/fetch-news.py` | Python 3 | feedparser |
| filter-news.py | `scripts/news/filter-news.py` | Python 3 | textblob |
| news-pipeline.sh | `/opt/data/scripts/news-pipeline.sh` | Bash | (wrapper) |
| news-analysis-context.sh | `/opt/data/scripts/news-analysis-context.sh` | Bash | (wrapper) |

## Deep Prediction (Layer 4)

เมื่อต้องการพยากรณ์ลึก:
1. User พูด `"พยากรณ์ [asset]"` หรือสัญญาณข่าวแรง ≥ 7
2. Hermes อ่าน analysis JSON + data ล่าสุด
3. ใช้ GLM x.x (Z.AI pay-as-you-go) วิเคราะห์
4. ส่งรายงานพยากรณ์ไป Telegram

## Cost Breakdown

| Layer | ต้นทุน/วัน | ต่อเดือน |
|-------|-----------|---------|
| 1-2 (no LLM) | $0 | $0 |
| 3 (Gemini 3.5 Flash) | ~$0.00002 | ~$0.0006 |
| 4 (GLM x.x, ~30 ครั้ง) | ~$0.01 | ~$0.50 |
| **รวม** | **~$0.01** | **~$0.50** |
