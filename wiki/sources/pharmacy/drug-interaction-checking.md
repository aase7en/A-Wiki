---
type: source
title: "Drug Interaction Checking Systems"
slug: drug-interaction-checking
date_ingested: 2026-05-25
original_file: raw/legacy/drug-interaction-checking.md
tags: [drug-interactions, clinical-decision-support, medication-safety, pharmacy]
provenance: legacy-import
---

# Drug Interaction Checking Systems

> **Type:** article
> **Domain:** Pharmacy
> **Ref:** https://www.fda.gov/drugs/drug-interactions-labeling
> **Ingested:** 2026-05-25
> **Quality:** curated
> **Tags:** drug-interactions, clinical-decision-support, medication-safety, pharmacy

## Abstract

Drug-drug interaction (DDI) checking is a core clinical decision support function in pharmacy information systems. DDIs are classified by mechanism (pharmacokinetic — absorption, distribution, metabolism, excretion; pharmacodynamic — additive, synergistic, antagonistic effects) and severity (contraindicated, major, moderate, minor). The cytochrome P450 enzyme system (CYP3A4, CYP2D6, CYP2C9) mediates most clinically significant interactions. Commercial DDI databases (DrugBank, Micromedex, Lexicomp, UpToDate) differ in coverage, severity classification, and evidence grading. Clinical decision support systems face alert fatigue — up to 90% of DDI alerts are overridden. AI approaches (NLP on literature, graph neural networks on drug-target networks) are emerging for DDI prediction.

## Key Concepts

- **Pharmacokinetic DDI** — Interaction affecting drug ADME (e.g., CYP450 inhibition/induction)
- **Pharmacodynamic DDI** — Interaction at the receptor or physiological effect level
- **Alert Fatigue** — Clinician desensitization from excessive drug interaction alerts
- **CYP450** — Cytochrome P450 enzyme family responsible for ~75% of drug metabolism
- **DDI Database** — Curated knowledge base with drug pairs, mechanism, severity, and evidence

## Related Links

- https://go.drugbank.com/drug-interactions
- https://www.fda.gov/drugs/drug-interactions-labeling

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/pharmacy/drug-validation]] — DDI checking as a drug-validation / decision-support function
- [[entities/pharmacy/drug-database]] — the drug knowledge base DDI checks run against

---
*Legacy sister-wiki import — provenance reconstructed 2026-06-18 (raw stub: `raw/legacy/drug-interaction-checking.md`).*