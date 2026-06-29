# Plan — GAS Personnel Check-in & Grouping Web App (รพ.ประจำอำเภอ)

## Context
Build a container-bound Google Apps Script web app for personnel check-in and grouping at Uthai Hospital (รพ.ประจำอำเภอ). Optimized for tablet/kiosk use at live events. The live master Google Sheet replaces `รายชื่อเจ้าหน้าที่ รพ.ประจำอำเภอ.xlsx`. Personnel names live in the user's Sheet only — the repo holds public-safe code (no PII).

## Resolved Decisions
- **CSS framework**: Bootstrap 5 via CDN (sandbox-safe; no eval/JIT). Touch-friendly components.
- **Location**: new repo folder `apps/personnel-checkin-grouping/`.
- **Spreadsheet**: container-bound script; reads `SpreadsheetApp.getActiveSpreadsheet()`.
- **Name column**: auto-detect by header text (matches `ชื่อ-นามสกุล`, `ชื่อ นามสกุล`, `ชื่อ`, case/space-insensitive). Reads first data sheet by default.
- **Deployment**: Execute as the owner; access = anyone within the org (protects personnel names from the public, no per-user login friction).
- **CSV download**: backend returns CSV string via `google.script.run`; frontend builds a `Blob` + temporary download link (works inside IFRAME sandbox).
- **Export schema**: append rows to sheet `Export_Groups` as `[Timestamp, Name, Group Name, Status]`, Status = `Checked-in`.
- **Check-in behavior**: checkbox toggle adds/removes from in-memory staging list; duplicates within staging prevented.
- **Group saves**: append (never overwrite); timestamp distinguishes sessions; reusing a group name is allowed.

## Deliverables (3 files)
1. `apps/personnel-checkin-grouping/Code.gs`
2. `apps/personnel-checkin-grouping/Index.html`
3. `apps/personnel-checkin-grouping/README.md` (deploy + usage steps)

## Ordered Tasks

### 1. `Code.gs` (backend)
- `doGet()` → `HtmlService.createHtmlOutputFromFile('Index')`, set title, set `XFrameOptionsMode.ALLOWALL` not required; use `.setTitle('ระบบเช็คอินเจ้าหน้าที่')`.
- Constants: `EXPORT_SHEET = 'Export_Groups'`; `HEADER_LABELS = ['ชื่อ-นามสกุล','ชื่อ นามสกุล','ชื่อ','name','fullname']`.
- `getPersonnel()`:
  - Get active spreadsheet → first sheet.
  - Read header row (row 1); find column whose trimmed/normalized header matches any `HEADER_LABELS` (normalize: lowercase, collapse spaces).
  - On no match → return error object `{ ok:false, error:'ไม่พบคอลัมน์ ชื่อ-นามสกุล ในชีต' }`.
  - Collect non-empty name values from that column (row 2+); dedupe preserving order.
  - Return `{ ok:true, names:[...] }`.
- `saveGroup(groupName, names[])`:
  - Validate `groupName` non-empty and `names` non-empty array → else return `{ ok:false, error }`.
  - Get/create `Export_Groups` sheet; ensure header row `[Timestamp, Name, Group Name, Status]` (create on first run; preserve if exists).
  - For each name: append `[new Date(), name, groupName, 'Checked-in']`.
  - Return `{ ok:true, count: names.length }`.
- `getExportCsv()`:
  - Read all rows of `Export_Groups` (include header).
  - Properly CSV-quote/escape (wrap fields containing comma/quote/newline in double quotes; double embedded quotes).
  - Return `{ ok:true, csv:'...' }`.
- Note: container-bound = no manual spreadsheet ID; no `PropertiesService` URL config needed.

### 2. `Index.html` (frontend: HTML + CSS + Vanilla JS in one file)
- **Head**: Bootstrap 5 CSS + JS bundle CDN links; viewport meta for mobile; large base font/touch targets.
- **Layout (single page, mobile-first)**:
  - Title bar.
  - Search section: `<input id="search">` (large) + results list with checkbox per match.
  - Staging section: list of checked-in personnel (each with remove control).
  - Group section: `<input id="groupName">` + "Save Group to Sheet" button.
  - Actions: "Download CSV (Export_Groups)" button.
  - Toast container (Bootstrap toast) + a global loading overlay/spinner.
- **JS**:
  - `google.script.run.withSuccessHandler(...).getPersonnel()` on `DOMContentLoaded`; show spinner until loaded; on error show toast.
  - Render search results: when query empty show all (scrollable, capped height) else client-side filter (case-insensitive, includes).
  - Checkbox change → add/remove name in `staging` Set; re-render staging list.
  - Save flow: validate (non-empty group name + ≥1 staged); disable button + spinner; `google.script.run.withSuccessHandler(...).withFailureHandler(...).saveGroup(groupName, [...staging])`; on success toast + optionally clear staging; re-enable button.
  - CSV: `getExportCsv()` → on success build `new Blob([csv], {type:'text/csv;charset=utf-8;'})`, object URL, `<a download="Export_Groups.csv">` click, revoke URL.
  - Guard double-clicks: every async action disables its trigger until handler returns.

### 3. `README.md`
- Purpose, prerequisites (master Google Sheet with a `ชื่อ-นามสกุล` header column).
- Step-by-step deploy:
  1. Open master Sheet → Extensions → Apps Script.
  2. Replace `Code.gs`; add `Index.html` (Files → HTML).
  3. Save; Run `doGet` once to authorize (accept scopes: spreadsheets).
  4. Deploy → New deployment → Web app: Execute as "Me"; Who has access "Anyone within [org]"; deploy; copy `/exec` URL.
  5. Open URL on a tablet; verify.
- Troubleshooting: header-not-found error, CSV blank if no saves yet, re-deploy (not just save) to publish changes.

## Validation (acceptance checks)
- App loads and shows personnel names from master sheet.
- Typing filters the list; checkbox toggles staging; staging list updates live.
- Cannot save with empty group name or empty staging (clear validation message).
- Save writes correct rows to `Export_Groups` with timestamp + `Checked-in` status; count matches.
- Repeated save appends (no overwrite); spinner + disabled button prevent double-submit.
- CSV download produces a valid file with all `Export_Groups` rows and proper escaping.
- Mobile layout: search input, checkboxes, and buttons are comfortably tappable; layout reflows on a phone-width viewport.
- Header-detection failure shows the specific Thai error toast.

## Risks & Mitigations
- **Header text mismatch** → fuzzy/normalized header match + explicit Thai error toast naming the required header.
- **`Export_Groups` not pre-existing** → backend auto-creates sheet + header on first save.
- **Bootstrap CDN blocked by hospital network** → document fallback (host Bootstrap CSS inline or use minimal custom CSS) as an open option; default keeps CDN.
- **Org deploy disallows anonymous** → expected; users authenticate within the org once.

## Open Questions
- None blocking. (Optional later: offline fallback for Bootstrap CDN; configurable sheet name instead of always first sheet.)
