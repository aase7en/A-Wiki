---
name: monte-carlo-quant-analysis
description: "Monte Carlo simulation + synthetic data + quant risk analysis for portfolio/stock/fund/robot-trading PREDICTION (paper/simulation-only, non-advisory). Use when forecasting outcomes via repeated random sampling, generating synthetic scenarios, or computing risk metrics (VaR/CVaR/Sharpe/drawdown/RRR) as probability distributions rather than point estimates."
version: 1.0.0
domain: [trader, data]
lifecycle_phase: none
category: awiki
agents: [all]
status: canonical
invocation: manual
th_description: "จำลองผลลัพธ์ด้วย Monte Carlo และสร้างข้อมูลสังเคราะห์เพื่อประเมินความเสี่ยง/ผลตอบแทนของพอร์ต หุ้น กองทุน หรือกลยุทธ์เทรด ในรูปแบบ probability distribution (ไม่ใช่การแนะนำการลงทุน)"
when_to_use: "เมื่อต้องทำนาย/จำลองผลลัพธ์ที่มีความไม่แน่นอน — forecast portfolio, scenario analysis, project risk, robot-trading backtest, risk-metric estimation"
examples:
  - {scenario: "จำลองผลตอบแทนพอร์ตลงทุน 1 ปีข้างหน้า", how: "MC simulate return paths → P5/P50/P95 band"}
  - {scenario: "ประเมิน VaR/CVaR ของกลยุทธ์", how: "N simulations → tail percentile"}
  - {scenario: "สร้างข้อมูลราคาสังเคราะห์เพื่อทดสอบ bot", how: "sample from fitted distribution → synthetic OHLCV"}
  - {scenario: "เปรียบเทียบกองทุนด้วย Risk-Reward Ratio distribution", how: "per-path RRR → distribution comparison"}
process_steps:
  - "Define inputs (historical data / assumed distribution / parameters)"
  - "Pick distribution model (normal / lognormal / t / empirical / bootstrap)"
  - "Run N-simulation loop (vectorized with numpy)"
  - "Aggregate outputs into percentile bands (P5/P50/P95)"
  - "Compute risk metrics (VaR/CVaR/Sharpe/drawdown/RRR)"
  - "Report as distribution + CI (paper-only, non-advisory)"
---

# Monte Carlo Quant Analysis

จำลองผลลัพธ์ที่มีความไม่แน่นอน ผ่าน repeated random sampling เพื่อให้ได้ **probability distribution** ของผลลัพธ์ (ไม่ใช่ point estimate) สำหรับทำนาย portfolio/หุ้น/กองทุน/robot-trading และ project risk

> **Synthesized from**: [[firmai-financial-machine-learning]] (taxonomy) · [[akashdeepo-monte-carlo-rrr]] (implementation) · [[unpingco-python-stats-ml]] (mathematical foundations) — see References

## Guardrails (Iron Law #8 — bot-trading-iron-law)

⚠️ **skill นี้ simulation/paper-only อย่างเคร่งครัด** ปฏิบัติตาม Iron Law #8 + แนว ECC advice-boundary:

- ✅ **อนุญาต**: จำลอง, คำนวณ probability distribution, ประเมิน risk metric จาก historical/assumed data, สร้าง synthetic data, backtest ด้วย paper/simulated fills
- ❌ **ต้องปฏิเสธ**: วาง/แก้/ยกเลิกคำสั่งซื้อขายจริง, เก็บ exchange/broker API key/secret, sign request, แนะนำ buy/sell/hold/size (output = informational เท่านั้น)
- ❌ ห้าม silent fallback จาก mock ไป live data feed
- ❌ ห้ามให้ LLM output กลายเป็น executable order โดยไม่มี server-side validation

## When to Use

- ทำนายผลลัพธ์ที่มี uncertainty → อยากได้ **range + probability** ไม่ใช่ single number
- จำลอง portfolio return paths / คำนวณ risk metric (VaR, CVaR, Sharpe, max drawdown, Risk-Reward Ratio)
- สร้าง synthetic market data สำหรับทดสอบ trading bot / strategy (paper only)
- ประเมิน project risk (schedule, cost, completion) ผ่าน simulation
- backtest strategy โดย propagate uncertainty ของ parameter estimates
- เปรียบเทียบกองทุน/strategy ด้วย distribution ของ metric (ไม่ใช่ mean เดียว)

## When NOT to Use

- ต้องการ single point forecast (ใช้ regression/time-series model ตรงๆ แทน)
- ข้อมูลน้อยมากจนไม่ fit distribution ได้ (พิจารณา scenario analysis แทน)
- ต้องการ live trading signal (skill นี้ non-advisory — ห้าม)
- งาน deterministic (ไม่มี random component — MC เป็น overkill)

## Core Framework

### §1 — Monte Carlo Loop Structure (from akashdeepo)

```
1. INPUT      historical data OR assumed distribution + parameters
2. FIT        estimate distribution params (μ, σ, df...) from data
3. SAMPLE     draw N random paths × T timesteps
              → shape (N, T) array of simulated outcomes
4. COMPUTE    per-path metric (return, drawdown, RRR, hitting time...)
5. AGGREGATE  percentile bands (P5, P50, P95), mean, std, CI
6. REPORT     distribution + confidence interval (NOT advice)
```

**Key principle**: ผลลัพธ์เป็น **distribution** ไม่ใช่ single number. P50 = median estimate, P5/P95 = uncertainty band.

#### Paper-data feed seam (Iron Law #8 compliant)

เมื่อต้องการ MC simulate บน historical-ish data โดยไม่ละเมิด Iron Law #8 ให้ใช้
`CannedMarketDataFeed` pattern (approved 2026-06-12 amendment ใน
`docs/protocols/bot-trading-iron-law.md`) — embedded historical data,
read-only `listSymbols()`/`getKlines()` interface, zero write methods.
MC output (synthetic paths) เข้ากับ `MockBotFeed` paper-settlement workflow ได้ตรงๆ
— simulated fills only, ไม่มี real order ทุก layer.

> ดู `examples/portfolio_mc_1yr.ipynb` สำหรับ runnable demo ที่ใช้ canned synthetic CSV
> (seeded `np.random.default_rng(42)`, reproducible 100%, no external download).

### §2 — Distribution Selection (synthetic data generation)

เลือก distribution ตามลักษณะข้อมูล (สังเคราะห์จาก Unpingco foundations + firmai risk taxonomy):

| Use case | Distribution | Why |
|----------|-------------|-----|
| Stock returns (daily) | **Normal** | CLT, simplest baseline |
| Asset prices (positive only) | **Lognormal** | price = exp(returns), รักษา positivity |
| Returns with fat tails (crash risk) | **Student-t** | heavier tails → realistic VaR |
| Multi-asset with correlation | **Multivariate Normal + Copula** | preserve correlation structure |
| No assumed form, have data | **Bootstrap (empirical)** | resample historical — no distributional assumption |
| Rare events / jumps | **Poisson + jump-diffusion (Merton)** | model discontinuities |

**Decision rule**: เริ่มจาก empirical/bootstrap (น้อย assumption สุด) → เปรียบเทียบกับ parametric (Normal/t) → รายงานทั้งสองเพื่อ show model risk

### §3 — Quant Risk Metrics (from akashdeepo + firmai risk wiki)

Compute แต่ละ metric บน **distribution ของ N simulations** (report as median + percentile band):

| Metric | Meaning | MC computation |
|--------|---------|----------------|
| **VaR(α)** | "loss not exceeded with prob 1-α" | α-percentile ของ P&L distribution |
| **CVaR/ES(α)** | expected loss *given* breach | mean ของ tail beyond VaR(α) |
| **Sharpe** | return per unit volatility | mean(excess return) / std, per path then aggregate |
| **Sortino** | return per unit *downside* volatility | uses only negative returns in denominator |
| **Max Drawdown** | worst peak-to-trough loss | max over path of (peak - current)/peak |
| **Risk-Reward Ratio (RRR)** | expected gain vs expected loss | E[upside] / E[downside] หรือ reward:risk จาก path |
| **Hitting probability** | P(reaching target before stop) | fraction of paths hitting target first |

### §4 — Probability Foundations (from Unpingco)

ทำความเข้าใจก่อนอ้างผล MC:

- **Law of Large Numbers (LLN)** — MC ทำงานเพราะ mean ของ N samples → true expectation เมื่อ N→∞. ใช้ N ≥ 10,000 สำหรับ stable estimate
- **Central Limit Theorem (CLT)** — ทำให้สร้าง CI ได้: `estimate ± 1.96 × SE` (SE = std/√N)
- **Convergence diagnostics** — ดูว่า N เพียงพอ: running mean ควร stabilize; double N แล้ว metric เปลี่ยน < 1%
- **Tail bounds** (Markov/Chebyshev/Hoeffding) — worst-case bound โดยไม่ต้อง run infinite sims; ใช้ระบุ "ดีสุด/แย่สุดที่เป็นไปได้"
- **Bootstrap vs MC** — bootstrap resample empirical data (assumption-light); MC sample จาก assumed distribution (parametric). เลือกตาม confidence ใน distributional assumption
- **Delta Method** — ถ้า metric เป็น function ของ random variable (เช่น Sharpe = μ/σ) ใช้ delta method propagate variance

## Workflow (step-by-step)

```
1. DEFINE     inputs (data source, time horizon, what to predict)
              ↓
2. CHOOSE     distribution model (§2) + justify choice
              ↓
3. FIT        estimate parameters from data (MLE / method of moments)
              ↓
4. SIMULATE   N paths (vectorized numpy, N ≥ 10,000)
              ↓
5. COMPUTE    per-path metric (§3)
              ↓
6. AGGREGATE  percentile bands (P5/P50/P95) + CI from CLT
              ↓
7. DIAGNOSE   convergence check (double N, compare)
              ↓
8. REPORT     distribution plot + key metrics + assumptions
              (PAPER-ONLY, NON-ADVISORY — ระบุชัด)
```

## Code Pattern (vectorized, numpy)

```python
import numpy as np

# --- §2 Fit + sample (lognormal for prices, normal for returns) ---
def simulate_returns(mu: float, sigma: float, T: int, N: int = 10_000, rng=None):
    """Vectorized MC: N paths × T timesteps."""
    rng = rng or np.random.default_rng(seed=42)  # reproducible
    # shape (N, T) — each row a path
    return rng.normal(loc=mu, sigma=sigma, size=(N, T))

# --- §3 Risk metrics on distribution ---
def var_cvar(pnl: np.ndarray, alpha: float = 0.05):
    """VaR + CVaR at confidence 1-alpha. pnl: 1D array of N P&L outcomes."""
    var = np.quantile(pnl, alpha)            # loss threshold
    cvar = pnl[pnl <= var].mean()            # expected loss given breach
    return var, cvar

def risk_reward_ratio(paths: np.ndarray, threshold: float = 0.0):
    """RRR = E[upside] / |E[downside]| per path, then aggregate."""
    finals = paths[:, -1]
    upside = finals[finals > threshold]
    downside = finals[finals <= threshold]
    rrr = (upside.mean() if len(upside) else 0) / abs(downside.mean() if len(downside) else 1)
    return rrr

# --- §4 CI from CLT ---
def ci_95(x: np.ndarray):
    """95% CI for the mean via CLT."""
    se = x.std(ddof=1) / np.sqrt(len(x))
    return x.mean() - 1.96 * se, x.mean() + 1.96 * se
```

> ทั้งหมดเป็น simulation — ไม่มี order placement, ไม่มี API key, ไม่มี live feed. สอดคล้อง Iron Law #8.

## Reporting Standards (non-advisory)

ผลลัพธ์ทุกชิ้นต้อง:

1. **Report as distribution** — percentile bands (P5/P50/P95) + histogram, ไม่ใช่ single number
2. **State assumptions** — distribution ที่ใช้, N, time horizon, data window
3. **Show convergence** — running mean plot หรือ "doubled N, Δ < 1%"
4. **Disclose model risk** — เปรียบเทียบ ≥ 2 distribution (parametric vs bootstrap)
5. **No advice** — ห้ามคำว่า "buy/sell/hold/recommend/should". Output = "under these assumptions, the simulated P5/P50/P95 of [metric] is..."
6. **Paper-only label** — ระบุชัดทุก output ว่า "simulation, not investment advice, not an order"

## Common Pitfalls

- ❌ **N น้อยเกินไป** (เช่น 100) → noise dominates. ใช้ N ≥ 10,000 สำหรับ stable tail metrics
- ❌ **Assume Normal ทุกที่** → under-estimate tail risk. Returns ส่วนใหญ่ fat-tailed → ใช้ t หรือ empirical
- ❌ **Ignore parameter uncertainty** — μ, σ ที่ fit จาก data มี uncertainty เอง → ใช้ bootstrap บน parameters ด้วย (double bootstrap)
- ❌ **Confuse path metric vs final metric** — max drawdown เป็น path-dependent (ดูทุก timestep), ไม่ใช่แค่ final value
- ❌ **Report mean only** — ซ่อน risk. Median + percentile band เป็นมาตรฐาน
- ❌ **ภาษา advice** — "ควรซื้อ", "น่าลงทุน" → ละเมิด advice boundary. ใช้ "ภายใต้สมมติฐานนี้ distribution ของผลคือ..."

## Extensions (advanced, out of scope สำหรับ v1)

### Quasi-Monte Carlo (variance reduction)

Pseudo-random MC converge ที่ O(1/√N). Quasi-MC ใช้ low-discrepancy sequences
(Sobol, Halton) ที่กระจาย "สม่ำเสมอกว่าสุ่ม" → converge ที่ O(1/N) — เร็วขึ้น ~10-100×
สำหรับ tail-risk accuracy เดียวกัน. เหมาะกับ VaR/CVaR ที่ต้องการ tail precision.

```python
from scipy.stats import qmc, norm  # scipy ≥ 1.7

def sobol_paths(mu: float, sigma: float, T: int, N: int = 4096, seed: int = 42):
    """QMC paths via Sobol — N ควรเป็น power of 2 สำหรับ balance property."""
    sampler = qmc.Sobol(d=T, scramble=True, seed=seed)
    u = sampler.random(N)                    # shape (N, T) uniform [0,1)
    z = norm.ppf(u)                           # → standard normal via inverse CDF
    return mu + sigma * z                     # shape (N, T) simulated returns
```

**เลือกเมื่อ**: tail-risk metric (VaR/CVaR) ต้องการ precision สูง + N ใหญ่.
**ไม่เลือกเมื่อ**: path-dependent metric (max drawdown) ที่ sequential structure สำคัญ —
QMC อาจไม่ preserve path structure ได้ดีเท่า pseudo-random.

### อื่นๆ

- **Importance sampling** — oversample rare events สำหรับ tail-risk accuracy
- **Stochastic processes ที่ซับซ้อน** — Heston (stochastic vol), SABR, jump-diffusion
- **Multi-level MC** — variance reduction hierarchy
- **ML-augmented MC** (akashdeepo's ensemble approach) — ML forecast distribution params → MC propagate

## References

### Source pages (provenance: raw/ first)
- [[firmai-financial-machine-learning]] — taxonomy of ML-in-finance techniques (portfolio/risk/derivatives wiki) · `raw/firmai-financial-ml-readme.md`
- [[akashdeepo-monte-carlo-rrr]] — MC + ensemble ML implementation for RRR · `raw/akashdeepo-mc-rrr-main.ipynb`
- [[unpingco-python-stats-ml]] — Springer book probability/statistics/ML foundations · `raw/unpingco-sampling-monte-carlo.ipynb`

### Skill-authoring references (read-only, not ingested as source)
- `raw/muratcankoyyan-context-eng-ref.md` — context-engineering skill structure patterns
- `raw/prat011-llm-skills-ref.md` — LLM skill format conventions (.md + YAML)

### Related A-Wiki skills (advice-boundary siblings)
- `prediction-market-risk-review` — review trading workflows for compliance/safety
- `ito-trade-planner` — non-executing trade planning worksheet
- `defi-amm-security` — DeFi/smart-contract security (different domain, same advice boundary)

### Subagent routing
- `finance-analyst` (`agents/subagents/finance-analyst.md`) — เรียก skill นี้เมื่อต้องการ distribution-based risk analysis (VaR/CVaR/RRR ผ่าน MC simulation)

### Approved paper-data feed pattern
- `CannedMarketDataFeed` — see `docs/protocols/bot-trading-iron-law.md` §Amendment 2026-06-12 (read-only `listSymbols()`/`getKlines()`, zero write methods, flag-gated `RemoteMarketDataFeed` fallback)

### Protocols
- `docs/protocols/bot-trading-iron-law.md` — Iron Law #8 (MOCK-only, no secrets, no execution)
- `docs/protocols/brain-improvement-gate.md` — gate this skill passed before creation
