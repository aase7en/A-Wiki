# Standalone rabies-report blueprint

## Goal

Build a deterministic, local-first application that imports HIS and screening
exports, produces the nine report cells, preserves an auditable case trail,
and fills the official document without sending patient data to a cloud LLM.
AI is optional for prose and troubleshooting; it must never calculate the
official numbers.

## Data model

Use SQLite as the initial store. Preserve source lineage on every row.

- `imports`: file hash, source type, import time, coverage dates, row counts.
- `dose_events`: normalized HN, service date, vaccine/IG type, route, source.
  Deduplicate on the canonical event key `(hn, service_date, product)` while
  retaining the import relationship.
- `screening_history`: HN, assessment date/effective date, status enum
  (`prior_near`, `prior_far`, `none_or_lt3`), raw value, source.
- `cases`: anchored 33-day cluster, refinement reason, start/end date.
- `case_prior`: selected prior evidence, evidence source, effective date, and
  near/far interpretation.
- `report_runs`: rules version, period, input hashes, warnings, approval state.
- `report_cells` and `audit_findings`: official counts plus traceable case IDs.
- `templates`: template hash and field mapping; do not store patient data in a
  document template.

## Critical temporal rule

Screening is a history table, not one timeless value per HN. Select only the
latest screening record effective on or before the case start date. Never
apply a later answer to an earlier quarter. Exact dated HIS evidence wins over
screening evidence when it proves a completed prior series.

The current Python engine collapses screening to one HN-level value. Until it
supports dated screening history, retrospective runs must use the saved
quarter-specific screening cutoff input from
`04_audit/reproducibility_inputs`.

The screening value `none_or_lt3` is ambiguous. It means "never vaccinated or
fewer than three doses" and must not be reported as definitely never
vaccinated.

## Deterministic pipeline

1. Import and validate schema, coverage dates, hashes, and row counts.
2. Normalize identifiers and product/route labels; deduplicate events.
3. Cluster doses with the anchored 33-day rule, then run cross-window
   refinement for abandoned-dose plus clean-restart patterns.
4. Attach prior evidence from the 10-year HIS history and date-valid screening
   history. Reject future leakage.
5. Classify each case, reconcile all doses, and enforce the nine-cell
   invariants.
6. Save a versioned report run, audit workbook/CSV, and filled DOCX/PDF.

## MVP

- Windows-friendly local CLI first; optional local web UI after the engine and
  import contracts are stable.
- Import XLS/XLSX/CSV into one encrypted-at-rest or access-controlled SQLite
  database on the hospital machine.
- Select a quarter, automatically require 10-year history, screening coverage,
  and next-month lookahead, then show blocking warnings for missing inputs.
- Export nine cells, case-level audit, incomplete-series review, and official
  DOCX/PDF.
- Package an offline installer only after reproducible builds and local backup
  and restore are tested.

## Acceptance gates

- Five pinned regression cases pass.
- The focused rabies test suite passes with its current expected count.
- Approved Q1-Q3 aggregate vectors reproduce from hashed inputs.
- A no-screening test demonstrates the known HIS-only classification gap rather
  than silently claiming equivalence.
- Temporal tests prove that a later screening answer cannot change an earlier
  report.
- No raw HN, name, hospital, or province is written to the public repository or
  sent to an external model.

## Delivery stages

1. Freeze import contracts and temporal screening behavior around the existing
   Python engine.
2. Add SQLite ingestion, lineage, deterministic report runs, and backup/restore.
3. Add document filling and a small local UI for non-technical staff.
4. Pilot offline inside one unit with side-by-side reconciliation.
5. Consider multi-site or hosted deployment only after privacy, ownership,
   support, and security requirements are separately approved.

