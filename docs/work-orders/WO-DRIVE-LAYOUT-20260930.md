# WO-DRIVE-LAYOUT-20260930 — Private Drive layout cleanup

## Goal
Make the private `drive/` data layer easier to understand and search without breaking A-Wiki junction/symlink contracts or creating a second source of truth.

## Scope
- `drive/LAYOUT.md`
- `drive/personal-tools/userscripts/**`
- `drive/backups/waste-ocr/**`
- `drive/<HOSPITAL>/waste-ocr/**`
- `drive/<HOSPITAL>/ocr-feedback/**`
- legacy `drive/ocr-feedback/**` compatibility surface
- `scripts/drive_path.py`
- `scripts/setup-cloud-link.sh`
- `scripts/setup-local.sh`
- `scripts/agent-preflight.py`
- `scripts/health_external_data.py`
- `scripts/hooks/check_drive_link.py`
- `.github/workflows/ci-core.yml`
- `wiki/context/ocr-learning-log.md`
- `wiki/synthesis/waste-form-automation.md`
- focused tests for path/layout behavior

## Guardrails
- Do not rename or move top-level Drive roles that are already binding.
- Do not touch `raw/`, `_archive/`, `secrets/`, or unrelated business/project data.
- Do not expose private paths, workplace names, keys, tokens, or secret-bearing backup content.
- Preserve `scripts/userscripts -> drive/personal-tools/userscripts` compatibility.
- Preserve existing current userscript install path.
- External Drive changes must be reversible and verified before cleanup.
- If a repo reference changes, update A-Wiki in this isolated worktree and verify tests.

## Current evidence
- `personal-tools/userscripts` is a bound personal-tool role.
- The current stable userscript filename exists but is older than the latest versioned release.
- Hospital-specific Waste OCR runtime/config already has a dedicated data role under the hospital directory.
- Legacy/root OCR-feedback path still has code references and must not be moved blindly.
- Main A-Wiki checkout is dirty; implementation is isolated on branch `chore/drive-layout-cleanup-20260930`.

## Plan
1. Inventory userscript files and exact repo references.
2. Define one human-readable current entrypoint and one release-history location.
3. Reorganize old userscript versions without changing the stable install path.
4. Align Waste OCR runtime/feedback path ownership only where dependency analysis proves it safe.
5. Update `LAYOUT.md` and README/index documentation.
6. Update A-Wiki resolver/setup code only for confirmed path changes.
7. Run targeted tests, privacy scan, diff review, and verify Drive state.

## Acceptance
- Latest Waste OCR remains directly installable from the stable userscript path.
- Old releases are easy to find but clearly non-current.
- No broken junction/symlink/path references.
- No duplicate canonical role for OCR feedback/runtime state.
- Relevant A-Wiki tests and privacy checks pass.
- Main checkout remains untouched.
