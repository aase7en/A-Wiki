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
| Multi-asset with correlation | **Copula (Gaussian/Student-t/Clayton)** | preserve correlation + tail structure |
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

### Importance Sampling (variance reduction สำหรับ tail-risk)

Oversample เหตุการณ์หายาก (tail losses) เพื่อลด variance ของ VaR/CVaR estimate.
เลือก proposal distribution `q(x)` ที่ "หนักกว่า" target `p(x)` ใน tail region
แล้ว weight ด้วย likelihood ratio `w = p(x)/q(x)`.

```python
from scipy.stats import norm  # scipy ≥ 1.7 (มีอยู่แล้วใน QMC section)
import numpy as np

def importance_sampling_var(mu: float, sigma: float, alpha: float = 0.05,
                            N: int = 10_000, shift: float = 1.5, seed: int = 42):
    """IS-VaR: sample from shifted proposal, weight back to target."""
    rng = np.random.default_rng(seed)
    # Proposal: normal shifted left (into the loss tail)
    x = rng.normal(mu - shift * sigma, sigma, N)
    # Likelihood ratio weights: p(x) / q(x)
    w = norm.pdf(x, mu, sigma) / norm.pdf(x, mu - shift * sigma, sigma)
    # Weighted VaR via cumulative weights
    sorted_idx = np.argsort(x)
    cum_w = np.cumsum(w[sorted_idx]) / w.sum()
    var_idx = np.searchsorted(cum_w, alpha)
    return x[sorted_idx[var_idx]]
```

**เลือกเมื่อ**: tail probability ต่ำมาก (เช่น VaR 99%) และ pseudo-random MC ต้องการ N ใหญ่เกินไป.
**ไม่เลือกเมื่อ**: tail ไม่ไกล (VaR 95%) — IS อาจเพิ่ม variance ถ้า proposal ไม่ match target ดีพอ.

### Copula (multivariate dependency)

แยก marginals จาก dependence structure (Sklar's theorem: F(x,y) = C(F_X(x), F_Y(y))).
ใช้เมื่อ assets มี **asymmetric tail dependence** ที่ Multivariate Normal จับไม่ได้
(correlation ฝั่ง downside ≠ upside ในตลาดจริง — flight-to-quality regime). ดูรายละเอียด
ทฤษฎี + vine copulas ได้ที่ [[copula-multivariate-finance]].

```python
from scipy.stats import norm  # scipy ≥ 1.7 (มีอยู่แล้วใน QMC/IS section)
import numpy as np

def gaussian_copula(rho: float, n: int, rng: np.random.Generator) -> np.ndarray:
    """Gaussian copula → (n, 2) uniforms ที่ preserve rank correlation rho.

    คืน uniform [0,1] แล้ว transform ด้วย inverse marginal ทีหลัง (norm.ppf หรือ
    empirical) เพื่อให้ correlated samples ที่ preserve tail structure.
    """
    z = rng.normal(size=(n, 2))
    z[:, 1] = rho * z[:, 0] + np.sqrt(1.0 - rho * rho) * z[:, 1]  # Cholesky
    return norm.cdf(z)  # → uniforms, Spearman ≈ rho

# ใช้: u = gaussian_copula(0.7, 10_000, rng); x = norm.ppf(u)  # correlated normals
```

| Family | tail dependence | เลือกเมื่อ |
|--------|-----------------|-----------|
| **Gaussian** | ไม่มี (λ=0 ทุก rho<1) | baseline, correlation พอเพียง |
| **Student-t** | symmetric heavy (df เล็ก→หนัก) | risk-sensitive, วิกฤต |
| **Clayton** | lower-tail strong | downside risk, flight-to-quality |
| **Gumbel** | upper-tail strong | stress gain scenarios |

**Math invariant (test แล้วใน `tests/test_monte_carlo_copula.py`):**
เมื่อ correlation เพิ่มขึ้น (rho: 0→0.5→0.95) VaR(5%) ต้อง monotonically แย่ลง (ค่าเป็นลบมากขึ้น).
Clayton @ theta=5 (τ≈0.71) ต้องมี VaR(5%) ต่ำกว่า Gaussian @ rho=0.9 (τ≈0.71) — lower-tail dependence
ทำให้ joint extreme loss รุนแรงกว่า.

**เลือกเมื่อ**: ≥2 assets + tail dependence สำคัญกว่า correlation เฉลย (regime shift, crisis).
**ไม่เลือกเมื่อ**: single asset, dependence อ่อน (rho ≈ 0), หรือ dimension สูงมาก (>5) → ใช้ vine copulas.

### Stochastic volatility (Heston/SABR)

เมื่อ vol ไม่คงที่แต่เป็น stochastic process ที่ mean-revert — จับ **volatility clustering**
(Mandelbrot: "large changes → large changes") ที่ GBM พลาด → fat tails (kurtosis > 3)
แม้ marginal เป็น normal. ดูทฤษฎี + SDE + comparison table ได้ที่
[[stochastic-vol-heston-sabr]].

**Heston (equity, mean-reverting)** — Euler-Maruyama discretization ของ CIR variance process:

```python
import numpy as np

def heston_paths(v0, kappa, theta, xi, rho, mu, dt, n_steps, n_paths, rng):
    """Heston MC: variance (CIR) + correlated asset. คืน (log_return_sum, final_var).

    v0=initial var, theta=long-run var, kappa=mean-reversion speed,
    xi=vol-of-vol, rho=leverage corr (equity: ρ<0 — price down → vol up).
    Absorption (max(v,0)) รับมือ Feller violation (2κθ ≤ ξ²) อย่างปลอดภัย.
    """
    v = np.full(n_paths, v0, dtype=float)
    log_s = np.zeros(n_paths)
    sqrt_dt = np.sqrt(dt)
    sqrt_1mr2 = np.sqrt(1.0 - rho * rho)
    for _ in range(n_steps):
        zv = rng.standard_normal(n_paths)
        zs = rho * zv + sqrt_1mr2 * rng.standard_normal(n_paths)  # Cholesky
        v = v + kappa * (theta - v) * dt + xi * np.sqrt(np.maximum(v, 0.0)) * sqrt_dt * zv
        v = np.maximum(v, 0.0)  # absorption — กัน negative variance
        log_s += (mu - 0.5 * v) * dt + np.sqrt(np.maximum(v, 0.0)) * sqrt_dt * zs
    return log_s, v

# ใช้: lr, v = heston_paths(0.09, 2.0, 0.09, 0.4, -0.8, 0.05, 1/252, 252, 10_000, rng)
#       var_5pct = np.quantile(lr, 0.05)  # portfolio VaR(5%)
```

**SABR (rates/FX/forward — Hagan 2002)** — β exponent กำหนด backbone, α = vol-of-vol:

| β | backbone | ใช้เมื่อ |
|---|----------|---------|
| 1 | lognormal (Black) | ATM vol flat, positive rates |
| 0 | normal (Bachelier) | negative rates (shifted SABR) |
| 1/2 | CEV | equity-like skew |
| 0<β<1 | intermediate | calibration-driven |

Hagan 2002 asymptotic implied vol (closed-form, ใช้แทน MC สำหรับ European options):

```python
def sabr_implied_vol(F, K, T, alpha, beta, rho, sigma0):
    """Hagan 2002 lognormal implied vol approximation."""
    if abs(F - K) < 1e-10:  # ATM — use limit
        return sigma0 * (1 + ((2 - 3*rho*rho)/24) * alpha*alpha * T)
    z = alpha / sigma0 * (F**(1-beta) - K**(1-beta)) / (1 - beta)
    D = np.log((np.sqrt(1 - 2*rho*z + z*z) + z - rho) / (1 - rho))
    Fmid = np.sqrt(F * K)
    g1 = beta / Fmid
    g2 = -beta * (1 - beta) / Fmid**2
    corr = ((2*g2 - g1*g1)/24 * (sigma0 * Fmid**beta / alpha)**2
            + rho*g1/4 * sigma0 * Fmid**beta / alpha
            + (2 - 3*rho*rho)/24) * alpha*alpha * T
    return alpha * (np.log(F/K) / D) * (1 + corr)
```

**Math invariant (test แล้วใน `tests/test_monte_carlo_stochastic_vol.py`):**
1. Long-run mean v_t → θ (mean reversion, 5% tolerance)
2. Feller condition `2κθ > ξ²` + absorption → v_t ≥ 0 เสมอ
3. SV-sampled returns มี excess kurtosis > GBM ที่ long-run variance เดียวกัน (fat tails)

| โมเดล | Domain | Vol process | Closed-form option |
|-------|--------|-------------|-------------------|
| **Heston** | equity, index | CIR (mean-reverting) | Heston 1993 (Fourier) |
| **SABR** | rates, FX, forward | lognormal | Hagan 2002 (asymptotic) |
| **GARCH(p,q)** | time-series | discrete ARMA-GARCH | simulation-only |
| **Bates** | equity+jumps | Heston + Merton | affine-jump-diffusion |

**เลือกเมื่อ**: vol clustering / vol smile significant (deep-tail risk, option pricing, skew-sensitive metrics).
**ไม่เลือกเมื่อ**: constant-vol GBM พอ (short horizon, low precision ต้องการ), หรือ jumps dominate (ใช้ Merton — ดู subsection ถัดไป).

### Jump-diffusion (Merton)

เมื่อ path มี discontinuities (crashes, gaps, earnings shocks) — GBM และ Heston
เป็น continuous process ทั้งคู่ จับ tail ไม่ได้. **Merton (1976)** = GBM + compound
Poisson jump component. ดูทฤษฎี + closed-form + variant table ได้ที่
[[merton-jump-diffusion]].

```python
import numpy as np

def merton_log_returns(mu, sigma, lam, mu_j, sigma_j, T, n_paths, rng):
    """Merton jump-diffusion log-returns over [0,T] — exact (no time-step).

    lam=jump intensity, mu_j/sigma_j=log-jump-size N(mu_j, sigma_j^2).
    Drift compensated by λk (k=exp(mu_j+sigma_j^2/2)-1) so total E[return]=μ.

    Exact simulation (draw N_T ~ Poisson(λT) jumps directly) ดีกว่า Euler-Maruyama
    เพราะ discretize ด้วย dt ใหญ่จะ undercount jumps.
    """
    n_jumps = rng.poisson(lam * T, size=n_paths)
    jump_sums = np.zeros(n_paths)
    max_j = int(n_jumps.max())
    if max_j > 0:
        all_jumps = rng.normal(mu_j, sigma_j, size=(n_paths, max_j))
        mask = np.arange(max_j)[None, :] < n_jumps[:, None]
        jump_sums = (all_jumps * mask).sum(axis=1)
    k = np.exp(mu_j + sigma_j * sigma_j / 2.0) - 1.0
    drift = (mu - sigma * sigma / 2.0 - lam * k) * T
    diffusion = sigma * np.sqrt(T) * rng.standard_normal(n_paths)
    return drift + diffusion + jump_sums

# ใช้: lr = merton_log_returns(0.05, 0.2, 5.0, -0.05, 0.2, 1.0, 10_000, rng)
#       var_5pct = np.quantile(lr, 0.05)  # portfolio VaR(5%) — แย่กว่า GBM
```

**Math invariant (test แล้วใน `tests/test_monte_carlo_jump_diffusion.py`):**
1. Returns excess kurtosis > 0 (jump-induced fat tails)
2. λ=0 recovers pure GBM (mean/variance within 2% — sanity)
3. Merton VaR(5%) < GBM VaR(5%) ที่ σ เดียวกัน (downside jumps ทำให้ tail แย่ลง)

| โมเดล | λ | Jump size | ใช้เมื่อ |
|-------|---|-----------|---------|
| **Merton (1976)** | constant | Gaussian (lognormal) | baseline, closed-form Euro option |
| **Kou (2002)** | constant | double-exponential | leptokurtosis + skew น้อย params |
| **Hawkes** | stochastic (self-exciting) | (any) | clustered jumps (crises cascade) |
| **Bates (1996)** | constant | Gaussian | Heston SV + Merton jumps (most general) |

**เลือกเมื่อ**: discontinuities/crashes สำคัญ (earnings, macro shocks, gap risk), deep-tail VaR (99%+).
**ไม่เลือกเมื่อ**: continuous-path พอ (short horizon, ไม่มี jump evidence), หรือ λ calibrate ไม่ได้จาก data ที่มี.

### Jump-diffusion variants (Bates/Kou/Hawkes)

3 extensions ของ Merton ที่ relax หนึ่งในสอง assumption (Gaussian jump size /
constant intensity). ดูทฤษฎี + SDE + variant table ได้ที่
[[jump-diffusion-variants]].

**Bates (1996) — Heston SV + Merton jumps (most general equity model)**:

```python
# Compose J1 heston_paths() + J2 merton_jump_sum() — drift compensated by λk
def bates_log_returns(mu, kappa, theta, xi, rho, v0, lam, mu_j, sigma_j,
                      dt, n_steps, n_paths, rng):
    """Bates = Heston CIR variance + per-path Merton jumps."""
    T = n_steps * dt
    k = np.exp(mu_j + sigma_j * sigma_j / 2.0) - 1.0
    # Heston path with drift (μ - λk) so total E[return] = μ once jumps added
    lr_sv = heston_paths_v2(v0, kappa, theta, xi, rho, mu - lam * k,
                            dt, n_steps, n_paths, rng)  # returns log_s only
    n_jumps = rng.poisson(lam * T, size=n_paths)
    jump_sums = np.zeros(n_paths)
    max_j = int(n_jumps.max())
    if max_j > 0:
        all_j = rng.normal(mu_j, sigma_j, size=(n_paths, max_j))
        mask = np.arange(max_j)[None, :] < n_jumps[:, None]
        jump_sums = (all_j * mask).sum(axis=1)
    return lr_sv + jump_sums

# ใช้: lr = bates_log_returns(0.05, 2.0, 0.09, 0.4, -0.8, 0.09, 5.0, -0.05, 0.2,
#                              1/252, 252, 10_000, rng)
#       var_5pct = np.quantile(lr, 0.05)  # worse than Heston OR Merton alone
```

**Math invariant (test แล้วใน `tests/test_monte_carlo_bates.py`):**
1. Bates VaR(5%) < Heston VaR(5%) ที่ same SV params (jumps worsen tail)
2. Bates VaR(5%) < Merton VaR(5%) (SV worsens tail beyond pure jumps)
3. Bates excess kurtosis > Merton excess kurtosis (SV adds fat tails)
   **⚠️ direction subtlety (H6 lesson)**: Bates kurt (≈0.4) < Heston kurt (≈1.5)
   เพราะ adding near-Gaussian Merton diffusion dilutes per-variance kurtosis
   ของ Heston. Assert ที่ถูกคือ Bates > **Merton** ไม่ใช่ Bates > Heston.
4. λ=0 recovers Heston (mean/var match within 5% — composition sanity)

**เลือกเมื่อ**: ทั้ง vol clustering AND discontinuous crashes สำคัญ (crash-sensitive
equity options, deep-OTM long-dated puts, early-exercise Americans). เป็น standard
model เมื่อทั้งสอง effect มี.
**ไม่เลือกเมื่อ**: SV หรือ jumps อย่างเดียวพอ — Bates มี 8+ params (κ, θ, ξ, ρ, v₀,
λ, μ_J, σ_J) calibration ill-conditioned. Fix λ จาก historical jump-count estimates
ก่อนแล้วค่อย calibrate ที่เหลือกับ option prices.

(Kou double-exponential + Hawkes self-exciting variants — ดู L2/L3 subsections
ด้านล่างเมื่อ implemented.)

### Multi-level MC (nested expectation)

สำหรับ **nested expectation** `E[g(X)] = E[E[h(X,Y) | X]]` (เช่น option pricing ที่
inner expectation เป็น payoff average) — ใช้ telescoping sum ลด variance:
แทน sample g_fine ที่แพง ใช้ `E[g_coarse] + Σ E[g_fine − g_coarse]` บน shared
randomness (paired X เดียวกัน) → diff variance < single-sample variance.

```python
import numpy as np

def mlmc_telescoping(g_fine, g_coarse, n_levels, n_per_level, rng):
    """MLMC estimator via telescoping sum (shared-randomness interface).

    g_fine(x), g_coarse(x): callables taking scalar x, returning scalar.
    ต้องใช้ x ตัวเดียวกัน (shared randomness) มิฉะนั้น diff variance ไม่ลด.

    Level 0: E[g_coarse(X)], Level l>0: E[g_fine(X) - g_coarse(X)].
    คืน (estimate, estimator_variance).
    """
    x0 = rng.standard_normal(n_per_level)
    samples0 = np.array([g_coarse(xi) for xi in x0])
    est = float(samples0.mean())
    var = float(samples0.var(ddof=1) / n_per_level)
    for _ in range(1, n_levels):
        x = rng.standard_normal(n_per_level)
        diffs = np.array([g_fine(xi) - g_coarse(xi) for xi in x])
        est += float(diffs.mean())
        var += float(diffs.var(ddof=1) / n_per_level)
    return est, var

# ใช้: def g_fine(x): return np.exp(x)          # "ละเอียด" — exact
#      def g_coarse(x): return np.exp(0.5 * x)   # "หยาบ" — fewer inner samples
#      est, var = mlmc_telescoping(g_fine, g_coarse, n_levels=3, n_per_level=5000, rng=rng)
```

**Math invariant (test แล้วใน `tests/test_monte_carlo_multilevel.py`):**
1. Identical fine/coarse → diff = 0 ทุก level > 0 (shared-randomness contract)
2. Telescoping converge สู่ E[g_fine] ไม่ใช่ E[g_coarse] (unbiased)
3. Var(diff) < Var(g_fine) เมื่อ paired บน x เดียวกัน (variance reduction แหล่งที่มาของ MLMC efficiency)

**เลือกเมื่อ**: nested expectation (option pricing, Bermudan exercise, nested risk), ค่าใช้จ่ายของ g_fine >> g_coarse.
**ไม่เลือกเมื่อ**: ไม่มี nested structure, หรือ variance reduction ไม่คุ้ม overhead (simple payoff, single-level MC พอ).

### Bootstrap historical simulation

เมื่อไม่อยาก assume distribution (Normal/Student-t) เลย — resample จาก empirical
data โดยตรง. **iid bootstrap** สำหรับ stationary independent; **block bootstrap**
สำหรับ time series ที่มี autocorrelation (preserve temporal structure).

```python
import numpy as np

def bootstrap_returns(historical, n, rng, block_size=None):
    """Resample n returns จาก historical.

    block_size=None → iid bootstrap (ทำลาย serial correlation — เหมาะ independent data)
    block_size=int  → circular block bootstrap (preserves autocorrelation ใน block —
                      จำเป็นสำหรับ AR/GARCH/vol-clustering time series)
    """
    N = len(historical)
    if block_size is None:
        idx = rng.integers(0, N, size=n)
        return historical[idx]
    n_blocks = (n + block_size - 1) // block_size
    starts = rng.integers(0, N, size=n_blocks)
    idx = np.concatenate([np.arange(s, s + block_size) % N for s in starts])[:n]
    return historical[idx]

# ใช้: boot = bootstrap_returns(hist_returns, 10_000, rng, block_size=20)  # block สำหรับ AR(1)
#       var_5pct = np.quantile(boot, 0.05)  # VaR — guaranteed อยู่ใน [min, max] ของ historical
```

**Math invariant (test แล้วใน `tests/test_monte_carlo_bootstrap.py`):**
1. Block bootstrap preserves AR(1) autocorrelation; iid destroys it (lag-1 AC: block > 0.5·original, iid < 0.1)
2. VaR(5%) ∈ [min, max] ของ historical เสมอ (empirical resampling ไม่ extrapolate)
3. iid bootstrap ทำให้ autocorr → 0 (sanity — ใช้ผิด context บน time series = regression)

| Mode | ใช้เมื่อ | Preserves |
|------|---------|-----------|
| **iid** | cross-sectional, independent observations | marginal distribution เท่านั้น |
| **block** (circular) | time series, AR/GARCH, vol-clustering | marginal + short-range autocorrelation |
| **stationary** (Politis-Romano) | time series ที่ unknown dependence length | marginal + auto-adaptive block size |

**เลือกเมื่อ**: ไม่ assume distribution (empirical), tails within historical range, parameter uncertainty (double bootstrap).
**ไม่เลือกเมื่อ**: tail เกิน historical max (ใช้ EVT/parametric), หรือ regime shift ทำให้ history non-representative.

### Convergence diagnostic (reusable)

แทนที่จะเช็ค convergence แบบ ad-hoc ทุกครั้ง — ใช้ helper กลางที่รวม doubling-N
check + CI + flag ว่า converged. SKILL.md เอ่ยถึง convergence ใน 3 ที่ (§4 foundations,
workflow step 7, reporting standard #3) แต่ไม่มี code ก่อน K6.

```python
import numpy as np
from scipy.stats import norm

def convergence_diagnostic(samples, alpha=0.05, threshold_pct=1.0):
    """MC convergence diagnostic. Doubling-N delta < threshold_pct => converged.

    คืน dict: mean, std, se, ci_low, ci_high, doubling_delta_pct, converged, n.
    สำหรับ near-zero mean (|mean_half| < 0.1*std) ใช้ fallback: converged if
    |mean_full - mean_half| < 0.1*std (กัน divide-by-near-zero).
    """
    samples = np.asarray(samples, dtype=float)
    n = len(samples)
    mean = float(samples.mean())
    std = float(samples.std(ddof=1))
    se = std / np.sqrt(n)
    z = norm.ppf(1 - alpha / 2)
    ci_low = mean - z * se
    ci_high = mean + z * se
    half = n // 2
    mean_half = float(samples[:half].mean())
    delta_abs = abs(mean - mean_half)
    if abs(mean_half) > 0.1 * std:
        doubling_delta_pct = delta_abs / abs(mean_half) * 100
        converged = doubling_delta_pct < threshold_pct
    else:
        doubling_delta_pct = delta_abs / std * 100 if std > 0 else 0.0
        converged = delta_abs < 0.1 * std
    return {"mean": mean, "std": std, "se": se, "ci_low": ci_low,
            "ci_high": ci_high, "doubling_delta_pct": doubling_delta_pct,
            "converged": converged, "n": n}

# ใช้: d = convergence_diagnostic(mc_samples)
#      if not d["converged"]: warnings.warn(f"MC not converged (Δ={d['doubling_delta_pct']:.2f}%) — increase N")
#      print(f"E[X] = {d['mean']:.4f} ± {d['se']:.4f}  (95% CI: [{d['ci_low']:.4f}, {d['ci_high']:.4f}])")
```

**Math invariant (test แล้วใน `tests/test_monte_carlo_convergence.py`):**
1. N=100k standard-normal → converged=True (doubling delta < 1%)
2. N=50 standard-normal → converged=False (delta > 1%, under-sampled)
3. 95% CI สำหรับ N(0,1) ต้อง bracket true mean 0
4. Near-zero mean ใช้ fallback (กัน delta% explode เมื่อหารด้วย ≈0)

**เลือกเมื่อ**: ทุก MC run — convergence check เป็น mandatory reporting standard.
**ไม่เลือกเมื่อ**: deterministic calculation (ไม่ใช่ MC) หรือ N fix โดย constraint (ใช้ CI เฉยๆ).

### อื่นๆ

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
