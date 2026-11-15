---
type: source
title: "public-apis/public-apis — community API and MCP directory"
slug: public-apis-catalog
date_ingested: 2026-11-16
original_file: raw/public-apis-readme-2026-11-15.md
tags: [api, api-discovery, mcp, cross-domain, ai-tools]
---
# public-apis/public-apis — API Discovery Source

**ประเภท**: GitHub community catalog / curated README (not executable SDK)
**วันที่ต้นทาง**: upstream pinned commit 2026-11-13T17:59:59Z
**ผู้จัดทำ**: public-apis community / contributors
**Source URL**: https://github.com/public-apis/public-apis
**Pinned commit**: `51bc64abb499c7c532619d89c3f3a083899d3c61`
**Observed README blob**: `43147f989e06bf2e445a95c0e81ed034c9196e9a`
**Captured source**: `raw/public-apis-readme-2026-11-15.md`
**Raw snapshot SHA-256**: `22d154c962fd65f78ff71104db8f21ab135c56b9f9d9eca7371cc79840e681ba`
**Evidence class**: VERIFIED catalog existence; provider health/auth/pricing/licensing remains UNVERIFIED.

## ประเด็นหลัก
1. README catalogs third-party HTTP APIs by domain, descriptions, authentication, HTTPS and CORS; it also has a separate MCP Servers section with transport and installation pointers.
2. Catalog entry != active API, verified correctness, right to redistribute data, free commercial usage or authorized ChatGPT plugin.
3. Use this list for **discovery only**. Validate candidates against each provider's primary documentation, current terms, Thailand coverage, data period, freshness and provenance before integration.
4. A-Wiki owns reference and search, A-Wiki-Conductor owns admission/governance, SunDayRemoteMCP owns bounded execution; never build a shadow registry or unrestricted HTTP proxy.
## ตัวอย่างการใช้งานที่ยังต้อง Verify ผู้ให้บริการ
| Project | Candidate family | Critical check |
|---|---|---|
| ENV Digital Twin / IoT | weather, air-quality, solar, remote sensing | Thailand coverage, observation-vs-forecast, timestamps, units, license |
| Sunday Estate | geocoding, mapping, local context | Thai address quality, privacy, tiles/data terms |
| Hospital / pharmacy | health, government, drug metadata | official source and clinical review; NEVER submit patient data to candidate APIs |
| Investment / BTC | market/economic data | delay, exchange source, licensing, cost |
| SundayFamily / A-Conductor | read-only capabilities/health projection | governance approval, no direct browser execution |
| Content Factory | metadata/media data | media rights, platform usage terms |

## วิธีใช้กับ Agent
- Search **existing A-Wiki FTS5 / wiki source pages** first; `public-apis-catalog` is a pointer, not an authorization policy.
- Record per candidate: provider official docs, data/license, auth, cost, rate limits, schema, location, current check date, failure modes.
- Only implement fixed-allowlist HTTPS read-only proof-of-concept in a separately claimed work order; API keys and secrets never enter wiki or logs.
- Candidate status remains `UNVERIFIED` until provider evidence and live read-only tests pass. No blanket installation of third-party MCP servers.

## ข้อโต้แย้ง / ข้อจำกัด
- Community entries and marketing-sponsored APILayer material are mixed; independently verify each provider.
- The repository's MIT license covers its contents, not providers' API terms or third-party data licensing.
- The README snapshot is a **historical pinned snapshot**; newer provider changes require fresh retrieval.

## หน้า Wiki ที่ได้รับการอัปเดต
- This canonical source page: `wiki/sources/public-apis-catalog.md`
- Related existing source-ingestion skill: `skills/wiki/ingest-source/SKILL.md`
- Task/acceptance reference: `docs/work-orders/WO-AWIKI-91-PUBLIC-APIS.md` and GitHub Issue #91.
