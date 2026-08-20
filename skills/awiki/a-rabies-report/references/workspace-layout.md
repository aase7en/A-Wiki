# Private workspace layout

Use this layout for the hospital's private rabies-report workspace. Replace
`<drive>` and `<site>` locally; never copy real HNs, patient names, hospital
names, or raw exports into the public repository.

```text
<drive>/hospital-<site>/RabiesVacc/
├── README.md
├── 01_source/
│   ├── annual/                  # canonical 10-year HIS exports
│   ├── quarterly/               # period fixtures and current-quarter exports
│   └── screening/               # screening history, including external providers
├── 02_templates/                # blank official forms only
├── 03_reports/
│   ├── final/                   # latest approved deliverables
│   └── pending/                 # incomplete quarters and drafts still in use
├── 04_audit/
│   ├── current/                 # latest breakdowns, mixed cases, HN audits
│   └── reproducibility_inputs/  # lookahead and date-cutoff inputs for exact reruns
└── _archive/<YYYY-MM-DD>/       # recoverable superseded material + manifests
```

## Retention rules

Keep active:

- one canonical annual HIS export per year for the full 10-year lookback;
- current quarterly exports needed to reproduce approved reports;
- the screening source and any date-cutoff copies used by approved runs;
- next-period lookahead extracts used to complete cases crossing a quarter;
- blank templates, latest final reports, current audits, and machine-readable
  outputs required for reconciliation.

Archive, do not delete:

- superseded report versions, old review spreadsheets, dashboards, handoff
  notes, and duplicate derived outputs;
- any input whose provenance is uncertain until hashes and report lineage have
  been checked.

## Safe cleanup procedure

1. Record relative path, size, modified time, and SHA-256 before moving files.
2. Identify canonical sources before judging derived files. Verify that
   quarter and lookahead extracts are exact subsets where that relationship is
   expected.
3. Move superseded material into a dated `_archive` folder. Do not overwrite
   same-name files and do not permanently delete during the first cleanup.
4. Keep every special input required for an exact approved rerun under
   `04_audit/reproducibility_inputs`.
5. Regenerate the after-inventory and rerun the regression and unit-test gates.

## Token-efficient access

- Read `README.md` and the manifests first; do not scan the archive by default.
- Let deterministic scripts read full XLS/CSV data. Give the agent only
  aggregate output and the smallest HN audit slice needed for a decision.
- Use annual exports as the history source of truth, while keeping quarterly
  fixtures only when they are required for reproducibility.
- Store real-HN examples only in the private workspace. Skill evals and repo
  documentation must use synthetic or masked identifiers.

