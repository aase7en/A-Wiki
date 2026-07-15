---
type: entity
category: concept
tags: [monte-carlo, simulation, quant, risk, statistics, variance-reduction, synthetic-data, copula]
sources: [akashdeepo-monte-carlo-rrr, firmai-financial-machine-learning, unpingco-python-stats-ml, copula-multivariate-finance, stochastic-vol-heston-sabr]
created: 2026-07-14
updated: 2026-07-14
last_verified: 2026-07-14
verify_tool: python scripts/wiki/search-wiki.py "monte carlo"
---

# Monte Carlo Simulation (Quant Risk Analysis)

## ภาพรวม

**Monte Carlo (MC) simulation** = เทคนิคจำลองผลลัพธ์ที่มีความไม่แน่นอน ผ่าน repeated
random sampling (N รอบ) เพื่อให้ได้ **probability distribution** ของผลลัพธ์ (ไม่ใช่ point
estimate). ใช้ใน quant finance สำหรับ portfolio forecasting, risk-metric estimation
(VaR/CVaR/Sharpe/drawdown), synthetic data generation, และ project risk estimation.

> [verified 2026-07-14] A-Wiki รับเทคนิคนี้เข้ามาเป็น skill `monte-carlo-quant-analysis`
> (domain `[trader, data]`) — **simulation/paper-only, non-advisory** ตาม Iron Law #8.

## เมื่อใช้

- ทำนายผลลัพธ์ที่มี uncertainty → อยากได้ **range + probability** ไม่ใช่ single number
- จำลอง portfolio return paths / คำนวณ risk metric (VaR, CVaR, Sharpe, max drawdown, RRR)
- สร้าง synthetic market data สำหรับทดสอบ trading bot / strategy (paper only)
- ประเมิน project risk (schedule, cost, completion) ผ่าน simulation
- เปรียบเทียบกองทุน/strategy ด้วย distribution ของ metric (ไม่ใช่ mean เดียว)

## วิธีการ (core framework)

| ขั้น | ทำอะไร | หลักการ |
|-----|--------|---------|
| **1. Define** | inputs (data source, time horizon, target metric) | ระบุ assumptions ชัด |
| **2. Choose** | distribution model (Normal/Lognormal/Student-t/Multivariate+Copula/Bootstrap) | เลือกตามลักษณะข้อมูล — fat tails → Student-t หรือ empirical |
| **3. Fit** | estimate parameters (μ, σ, df...) from data (MLE / method of moments) | |
| **4. Simulate** | N paths × T timesteps (vectorized numpy, N ≥ 10,000) | LLN: mean ของ N samples → true expectation เมื่อ N→∞ |
| **5. Compute** | per-path metric (return, drawdown, RRR, hitting time) | path-dependent vs final metric ต่างกัน |
| **6. Aggregate** | percentile bands (P5/P50/P95) + CI from CLT | CLT: `estimate ± 1.96 × SE` |
| **7. Diagnose** | convergence check (double N, compare Δ < 1%) | |
| **8. Report** | distribution plot + key metrics + assumptions (**PAPER-ONLY, NON-ADVISORY**) | ห้ามคำว่า buy/sell/hold/recommend |

## Risk metrics computed

| Metric | ความหมาย | MC computation |
|--------|---------|----------------|
| **VaR(α)** | loss not exceeded with prob 1-α | α-percentile ของ P&L distribution |
| **CVaR/ES(α)** | expected loss *given* breach | mean ของ tail beyond VaR(α) |
| **Sharpe** | return per unit volatility | mean(excess return) / std |
| **Sortino** | return per unit *downside* volatility | uses only negative returns |
| **Max Drawdown** | worst peak-to-trough loss | max over path (path-dependent) |
| **RRR** | expected gain vs expected loss | E[upside] / \|E[downside]\| |

## Variance reduction (advanced)

| เทคนิค | converge rate | ใช้เมื่อ |
|--------|---------------|---------|
| **Quasi-MC** (Sobol/Halton) | O(1/N) vs O(1/√N) | tail-risk precision สูง, N ใหญ่ |
| **Importance Sampling** | ลด variance ของ tail estimate | deep tails (VaR 99%) |
| **Multi-level MC** | hierarchy | nested / nested expectations |

## เชื่อมโยง

- **Skill**: `monte-carlo-quant-analysis` (`skills/awiki/monte-carlo-quant-analysis/SKILL.md`) — canonical implementation + runnable notebook `examples/portfolio_mc_1yr.ipynb`
- **Subagent routing**: `finance-analyst` (`agents/subagents/finance-analyst.md`) — เรียก skill เมื่อต้องการ distribution-based risk analysis
- **Source pages (provenance raw/ first)**:
  - [[akashdeepo-monte-carlo-rrr]] — MC + ensemble ML implementation for RRR · `raw/akashdeepo-mc-rrr-main.ipynb`
  - [[firmai-financial-machine-learning]] — ML-in-finance taxonomy (portfolio/risk/derivatives) · `raw/firmai-financial-ml-readme.md`
  - [[unpingco-python-stats-ml]] — Springer book probability/statistics/ML foundations · `raw/unpingco-sampling-monte-carlo.ipynb`
- **Protocol**: `docs/protocols/bot-trading-iron-law.md` — Iron Law #8 (MOCK-only); `CannedMarketDataFeed` amendment 2026-06-12 = approved paper-data feed seam
- **Related concepts**: copula ([[copula-multivariate-finance]] — multivariate dependency modeling, includes vine copulas for high-dim portfolios), stochastic volatility ([[stochastic-vol-heston-sabr]] — Heston/SABR, vol clustering, fat tails), law of large numbers, central limit theorem, bootstrap
