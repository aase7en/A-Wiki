---
type: concept
tags: [swarm, bft, consensus, pso, aco, marl, maddpg, qmix, mappo, failure-modes, mast, groupthink, voting-topology, case-studies]
sources: [ai-engineering-swarm-optimization]
domain: ai-tools
created: 2026-06-08
updated: 2026-06-08
last_verified: 2026-06-08
verify_tool: WebFetch
---

# Swarm Optimization, BFT, MARL & Failure Modes

BFT consensus, voting topology, bio-inspired optimization (PSO/ACO), MARL algorithms, และ failure mode taxonomy สำหรับ multi-agent systems
[verified 2026-06-08] จาก `rohitg00/ai-engineering-from-scratch` Phase 16 (MIT)

---

## 1. Byzantine Fault Tolerance สำหรับ LLM Agents

### 3 LLM-Specific Attacks (ที่ Classical BFT ไม่รับมือ)
1. **Byzantine lie**: agent โกงตั้งใจ — classical BFT รับมือได้ถ้า f < n/3
2. **Sycophantic conformity**: agent อ่าน answer ของคนอื่นก่อน vote → align กับ loudest → ผ่าน signature check แต่ corrupt consensus
3. **Correlated-error monoculture**: 3 agents ใช้ same model → share hallucination → false majority (classical BFT ไม่ help)

### 3 Modern BFT Variants
| Algorithm | Key Idea | Best Against |
|---|---|---|
| **CP-WBFT** (arXiv:2511.10400) | Vote weight = confidence probe; +85.71% BFT improvement | Sycophancy (conformers = low confidence) |
| **DecentLLMs** (arXiv:2507.14928) | Leaderless; geometric-median aggregation; f < n/2 | Byzantine lies + monoculture |
| **WBFT** (arXiv:2505.05103) | Weighted votes + Core/Edge hierarchical clustering | Scalability |

### Minimal BFT Round
1. Each agent: answer a_i + confidence c_i → aggregator
2. Semantic cluster answers (not string-equal)
3. Cluster weight = sum(c_i)
4. Winner = max weight cluster if above threshold
5. Minority logged with provenance (early warning for correlated errors)

**"Can AI Agents Agree?" (arXiv:2603.01213)**: single deceptive agent shifts consensus 40+ points; disagree rate >30% even without adversaries.

---

## 2. Voting Topology และ Debate

### Self-Consistency (Wang 2022) — Baseline ราคาถูก
Same model × N samples at temperature>0 → majority vote. GSM8K gains at N=40.
**ลอง self-consistency ก่อนเสมอ** ก่อนลอง multi-agent debate.

### 4 Topologies (MARBLE/MultiAgentBench, ACL 2025, arXiv:2503.01935)
| Topology | Best for | Notes |
|---|---|---|
| **Star** | Fast factual, consolidation | Hub filters all |
| **Chain** | Sequential pipeline, staged refinement | Pipeline-like |
| **Tree** | Hierarchical tasks (legal/finance/engineering) | Depth-2 ceiling applies |
| **Graph** | Research, complex multi-step | Best overall but coordination tax |

### Coordination Tax
Graph topology: coordination tax starts past **~4 agents** — cost grows faster than quality.
Cause: each agent's context fills with peers' outputs, marginal value drops.

### AgentVerse Emergent Patterns (ICLR 2024)
- **Volunteer**: agent offers help unprompted → positive (allocates to capable agent)
- **Conformity**: agent aligns with critic even when wrong → negative (= debate-sycophancy)

### Rule of Thumb
- Same-budget comparison: self-consistency often beats MAD (Wang et al. finding)
- Heterogeneity > numerosity: 3 different models > 5 copies of 1 model on most tasks with ground truth

---

## 3. PSO / ACO สำหรับ LLM

### PSO (Particle Swarm Optimization, Kennedy 1995)
Population-based gradient-free optimizer. Particles move toward personal best + global best.
**ทำไมใช้กับ LLM**: LLM outputs ไม่ differentiable → ต้องใช้ gradient-free method

### LMPSO (arXiv:2504.09247)
PSO on LLM-generated structured outputs. Velocity = prompt describing how to modify toward best.
ใช้ดีกับ: structured output (programs, math), automatic fitness, population ≤30.

### Model Swarms (arXiv:2410.11163)
PSO on **model parameters** (LoRA deltas). Gradient-free update บน low-dimensional expert manifold.
Results: **+13.3% avg gain** over 12 baselines, 9 datasets, 200 instances only.

### ACO (Ant Colony Optimization, Dorigo 1992)
Path optimization via pheromone trails. Stronger trail = higher probability chosen.
Pheromone decays over time (prevents locking on early routes).

### AMRO-S (arXiv:2603.12933) — ACO for Agent Routing
Pheromone matrix over task-type × agent.
- Quality-gated update: pheromone only after quality check passes
- **4.7x speedup** on multi-agent routing benchmark
- Interpretable: pheromone strength = human-readable routing evidence

### Selection Guide
| Use | When |
|---|---|
| PSO | Continuous search, automatic fitness, small population |
| ACO | Routing/path selection, decisions reinforce over time, need interpretability |
| Neither | Human-review fitness, real-time strict latency |

---

## 4. MARL: MADDPG / QMIX / MAPPO

### CTDE Pattern (Centralized Training, Decentralized Execution)
**Design**: assume full team visibility. **Deploy**: each agent sees only own observation o_i.
ป้องกัน non-stationarity (each agent's env changes as others learn).

### 3 Algorithms
| Algorithm | Year | Key Idea | Best for |
|---|---|---|---|
| **MADDPG** (arXiv:1706.02275) | NeurIPS 2017 | Per-agent actor (local obs) + per-agent critic (global info) | Cooperative, competitive, mixed |
| **QMIX** (arXiv:1803.11485) | ICML 2018 | Monotone value decomposition: Q_tot = f(Q_1..Q_n) | Cooperative + homogeneous (SMAC) |
| **MAPPO** (arXiv:2103.01955) | NeurIPS 2022 | PPO + centralized value function; "surprisingly effective" | **2026 default baseline** |

### MAPPO ก่อนเสมอ
MAPPO matches or beats MADDPG, QMIX on 5 benchmarks. Minimal tuning, stable training.
ใช้ MAPPO ก่อน — ถ้า MAPPO ไม่พอแล้วค่อยลอง method ซับซ้อนกว่า.

### LLM-Agent Uses
- Router training: meta-agent chooses which sub-agent → MAPPO fits
- Role emergence: agents adopt complementary roles → QMIX value decomposition forces complementarity
- Multi-agent tool sharing with budget constraints → CTDE local policies

---

## 5. Failure Modes: MAST Taxonomy

### MAST (Cemri 2025, arXiv:2503.13657)
1642 traces, 7 production MAS. **41-86.7% failure rate.**

| Category | % | Root Cause | Mitigation |
|---|---|---|---|
| **Specification Problems** | 41.77% | Role ambiguity, unclear task, implicit success criteria | Explicit role contracts, acceptance tests, pre-flight spec check |
| **Coordination Failures** | 36.94% | State desync, lost messages, missing sync | Versioned state, explicit acks, periodic checkpoints |
| **Verification Gaps** | 21.30% | Answer shipped with no independent check | Independent verifier, handoff contracts, outcome logging |

Verification gaps = most expensive per-failure (silent correctness → not detectable by exception logs).

### Groupthink Family (arXiv:2508.05687)
| Failure | Description |
|---|---|
| Monoculture collapse | Same base model → correlated errors |
| Conformity bias | Agents align with loudest/most-confident peer |
| Deficient ToM | Agents fail to model each other's beliefs |
| Mixed-motive dynamics | Partially aligned incentives → compromise-middle |
| Cascading reliability failures | One component's error → downstream errors |

### Cascading Failure: Retry Storm
payment fails 10% → order retries → each retry = inventory check → inventory 2x load → inventory timeouts → inventory 10x load → cluster down.
**Fix**: Circuit breakers (open when error rate > threshold) + capped retry budgets.

### Memory Poisoning
One hallucination → shared memory fact → accuracy decays gradually → hard to root-cause.
Mitigation: append-only log + provenance + unwritable verifier.

### STRATUS (NeurIPS 2025)
Detection agent + Diagnosis agent + Validation agent.
SRE-style incident response for MAS. **+1.5x mitigation success.**

---

## 6. Case Studies 2026

### Anthropic Research (Supervisor Reference)
- Lead: Opus 4; Workers: Sonnet 4 (parallel, fresh context)
- **+90.2%** vs single-agent Opus 4
- **15x tokens** per query; **80% variance** explained by token usage alone
- Rainbow deployment: old runtime versions stay alive for in-flight agents

### MetaGPT / ChatDev (Role Decomposition Reference)
- `Code = SOP(Team)`: Product Manager → Architect → PM → Engineer → QA
- Structured artifacts (PRD, architecture docs) between roles
- ChatDev: communicative dehallucination — ask specifics before answering
- MacNet (arXiv:2406.07155): extends to 1000+ agents via DAG routing

### OpenClaw / Moltbook (Population Scale Reference)
- Nov 2025: Clawdbot ships (local ReAct-loop agents)
- Feb 2026: Moltbook = agent-only social network; 2.3M accounts in days
- Mar 2026: Meta acquires Moltbook; China restricts; 247k GitHub stars
- Lessons: prompt injection = new XSS; regulation faster than design cycles; emergent economy

### Framework Landscape April 2026
| Framework | Status | Best for |
|---|---|---|
| **LangGraph** | Production leader | Structured graph + checkpointing + HITL |
| **CrewAI** | Production leader | Role-based crews |
| **OpenAI Agents SDK** | Production | Handoff pattern (Swarm successor) |
| **Google ADK** | Production | A2A-native |
| **AG2** | Community | AutoGen v0.2 continuation |

Every framework: MCP + A2A table stakes. Handoff semantics = remaining differentiator.

---

## ความสัมพันธ์

- [[concepts/ai-tools/multi-agent-theory]] — P2a: patterns, architectures, protocols
- [[concepts/ai-tools/ai-myths]] — myth: "agents are autonomous"; verification anti-pattern
- [[concepts/ai-tools/ai-glossary]] — คำศัพท์: PSO, ACO, MARL, BFT, CTDE
- [[agent-skills/swarm-intelligence/agile-swarm]] — A-Wiki swarm = Supervisor pattern + Role Specialization

## แหล่งข้อมูล
- [[sources/ai-engineering-swarm-optimization]] — Phase 16 subtopics 14-25
- [[sources/ai-engineering-multi-agent]] — Phase 16 subtopics 01-13 (P2a)
