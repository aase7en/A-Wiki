---
type: source
title: "Swarm Optimization + Case Studies — rohitg00/ai-engineering-from-scratch Phase 16 (subtopics 14-25)"
slug: ai-engineering-swarm-optimization
date_ingested: 2026-06-08
original_file: raw/ai-engineering-swarm-optimization.md
tags: [swarm, bft, consensus, pso, aco, marl, maddpg, qmix, mappo, failure-modes, mast, case-studies]
domain: ai-tools
---

# Swarm Optimization + Case Studies — Phase 16 (Subtopics 14-25)

**ประเภท**: curriculum / theory  
**วันที่**: 2026  
**ผู้เขียน**: Rohit Ghumare (MIT License)

## ประเด็นหลัก

1. **BFT สำหรับ LLM**: 3 attack patterns ใหม่ (Byzantine lie, sycophantic conformity, monoculture); CP-WBFT/DecentLLMs/WBFT แก้ได้แต่ละ attack
2. **Voting Topology**: graph best for research, coordination tax >4 agents; self-consistency = cheap baseline ก่อนลอง MAD
3. **PSO/ACO**: gradient-free optimization สำหรับ LLM outputs + agent routing; AMRO-S 4.7x speedup
4. **MARL**: CTDE pattern (design global, deploy local); MAPPO = 2026 default baseline
5. **MAST Taxonomy**: 41-86.7% failure rate; Spec 41.77%, Coordination 36.94%, Verification 21.30%
6. **Groupthink family**: 5 failure patterns รวม monoculture + cascading + retry storms
7. **STRATUS**: Detection+Diagnosis+Validation agents = SRE for MAS (+1.5x mitigation success)
8. **Case Studies**: Anthropic Research (+90.2%, 15x tokens), MetaGPT SOP, OpenClaw/Moltbook population scale

## ข้อมูลที่น่าสนใจ

- MAST (Cemri 2025): 41-86.7% failure rate บน 7 production MAS จาก 1642 traces
- CP-WBFT: +85.71% BFT improvement บน complete graphs จาก confidence weighting
- AMRO-S: 4.7x speedup จาก ACO-based agent routing (pheromone trails)
- Model Swarms: +13.3% avg gain via PSO on model parameter subspace (200 instances only)
- MAPPO: "Surprisingly effective" — matches or beats all MARL baselines on 5 benchmarks
- Anthropic Research: 80% of BrowseComp variance explained by token usage alone
- Moltbook: 2.3M agent accounts ใน days; acquired by Meta March 2026

## หน้า Wiki ที่ได้รับการอัปเดต / สร้างใหม่

- [[concepts/ai-tools/swarm-optimization]] — สร้างใหม่ (chunk P2b)
