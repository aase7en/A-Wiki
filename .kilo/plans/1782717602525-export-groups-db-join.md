# Plan: Export_Groups Download — JOIN Personnnel_DB columns

## Goal

Export_Groups download checkbox list currently shows only 4 hardcoded EG columns (Timestamp, Name, Group Name, Status). Add Personnel_DB columns (เบอร์โทร, ตำแหน่ง, หน่วยงาน, etc.) as extra selectable columns. Backend JOINs Personnel_DB on name to pull the selected DB columns.

## Design

| Layer | Frontend checkbox value | Backend lookup |
|-------|------------------------|----------------|
| EG columns | `0`, `1`, `2`, `3` (literal EG col index) | Direct `data[r][v]` |
| DB columns | Actual DB header index (e.g. `5` for เบอร์โทร) | `dbRow[v]` via name→row map |

Download calls `exportGroupsCsv(egIndices, dbIndices)` — two separate arrays.

## Tasks (ordered)

### 1. Code.gs — redesign `exportGroupsCsv`

Replace current single `columnIndices` signature with `(egIndices, dbIndices)`:

- **Validate**: `egIndices` in [0,3]. `dbIndices` (if non-empty) in [0, DB_headers.length-1].
- **Read EG**: `sheet.getRange(1,1,lastRow,4).getValues()`
- **Read DB (lazy)**: Only if `dbIndices.length > 0` AND `Personnel_DB` exists with data → read all rows/cols, find `nameColIndex`, build `var dbMap = {}; dbMap[name] = rowClone` (same clone pattern as getPersonnel fix).
- **Build header row**: EG headers at selected indices + DB headers at selected indices
- **Build data rows**: For each EG row, output EG selected values + DB lookup values (empty string if name not in DB map or DB unavailable)
- **Edge case**: If anyone in Export_Groups has a name not in Personnel_DB, DB values appear as blank cells

### 2. Index.html — replace hardcoded checkboxes with dynamic populate

**HTML** (`#exportGroupsColList`, lines 129-145):
- Remove all 4 hardcoded `<div>` checkboxes
- Keep only `<div class="col-scroll" style="max-height:150px;" id="exportGroupsColList"></div>` (no child elements)

**New function `populateExportGroupsColumns()`**:
```javascript
function populateExportGroupsColumns() {
  var container = document.getElementById('exportGroupsColList');
  container.innerHTML = '';
  var html = '';
  // 4 EG columns — always present, default checked
  var egLabels = ['Timestamp', 'Name', 'Group Name', 'Status'];
  for (var i = 0; i < egLabels.length; i++) {
    html += '<div class="result-item" style="min-height:32px;padding:6px 10px;">';
    html += '<input class="form-check-input" type="checkbox" value="' + i + '" id="egcol_' + i + '" checked onchange="onExportGroupsToggle()">';
    html += '<label class="form-check-label" for="egcol_' + i + '" style="font-size:0.85rem;">' + egLabels[i] + '</label>';
    html += '</div>';
  }
  // DB columns — only if personnelHeaders exist, skip nameColIndex
  if (personnelHeaders.length > 0 && personnelNameColIndex >= 0) {
    for (var j = 0; j < personnelHeaders.length; j++) {
      if (j === personnelNameColIndex) continue;
      var hdr = String(personnelHeaders[j] || '(คอลัมน์ ' + (j+1) + ')');
      html += '<div class="result-item" style="min-height:32px;padding:6px 10px;">';
      html += '<input class="form-check-input" type="checkbox" value="' + j + '" id="egcol_db_' + j + '" onchange="onExportGroupsToggle()">';
      html += '<label class="form-check-label" for="egcol_db_' + j + '" style="font-size:0.85rem;">' + escapeHtml(hdr) + ' (DB)</label>';
      html += '</div>';
    }
  }
  container.innerHTML = html;
}
```

**Update `onExportGroupsToggle()`**:
- Keep enable/disable logic (same as now)

**Update `downloadExportGroups()`**:
- Iterate checked checkboxes, separate: `v <= 3` → `egIndices`, `v > 3` → `dbIndices`
- Call `google.script.run...exportGroupsCsv(egIndices, dbIndices)`

**Update `loadPersonnel()` success handler**:
- Call `populateExportGroupsColumns()` after `populateColumnCheckboxes()`
- Change `egColSection` visibility to always show: `egSection.style.display = 'block';`

**Update `executeDelete()`**:
- Call `populateExportGroupsColumns()` to reset to 4 EG columns only (since DB data is cleared)

### 3. Index.html — minor: update `egColSection` hide logic

- `loadPersonnel`: remove condition, set `display: 'block'` always
- `executeDelete`: keep `display: 'block'` (user may want to download EG after deleting DB)

## Validation

1. No DB uploaded → EG section shows 4 EG checkboxes only → download works as before
2. DB uploaded with เบอร์โทร, ตำแหน่ง, หน่วยงาน → EG section shows 4 EG + all DB columns → select EG+DB columns → CSV has joined data
3. Name in Export_Groups not in DB → DB columns blank, EG columns OK
4. After `executeDelete()` → EG section resets to 4 checkboxes only
5. After re-upload DB → EG section shows DB columns again
