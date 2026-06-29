# Plan — Personnel DB: Column Selection for Display & Export_Groups Download

## Status: ✅ Implemented (base: working versions from Desktop)

## What Changed

### Code.gs
1. `getPersonnel()` now returns `nameRowMap` — maps each unique name to its full row array (needed for frontend display column badges)
2. New `exportGroupsCsv(columnIndices)` — exports Export_Groups with user-selected columns

### Index.html — Two new collapsible sections

#### 1. Display Column Selector (เหนือผลค้นหา)
- Collapsible `<details>` with checkboxes for every Personnel_DB column except name column
- Select All / Deselect All buttons
- On toggle, re-renders search results immediately
- Selected columns appear as `extra-badge` under each name

#### 2. Export_Groups Column Selector
- 4 checkboxes: Timestamp, Name, Group Name, Status (all checked by default)
- Download button disabled when nothing selected
- Calls `exportGroupsCsv(indices)` on backend

### Flow Summary
```
loadPersonnel()
  → stores nameRowMap, headers, names
  → populateDisplayColumns() — builds display checkboxes
  → populateColumnCheckboxes() — builds Personnel_DB download checkboxes
  → shows egColSection

renderResults()
  → for each name, looks up row in nameRowMap
  → appends extra-badge spans for each selected displayColIndex
  → extra columns shown as inline badges below name
```

## Deployment
Deploy Code.gs + Index.html together in GAS. Test:
1. Upload sample .xlsx
2. Check "เลือกคอลัมน์ที่แสดงในผลค้นหา" — select columns → search results show badges
3. Check "เลือกคอลัมน์สำหรับดาวน์โหลด (Export_Groups)" — select columns → download → verify CSV
4. Personnel_DB download still works with column selection
