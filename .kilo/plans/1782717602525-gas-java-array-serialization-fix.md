# Plan: Fix Java Array Serialization — nameRowMap breaks getPersonnel response

## Root Cause

Line 40 in Code.gs: `nameRowMap[name] = data[r]` stores a reference to a **GAS Java array** (from `sheet.getValues()`). When `google.script.run` serializes the response, Rhino can serialize Java arrays as **direct** properties (e.g. `headers: data[0]` ✓) but fails when Java arrays are **nested inside** a JS object (`nameRowMap: { "John": JavaArray }` ✗). The response arrives with corrupted/missing fields → frontend sees `allNames: []`.

Working Code.gs (user's paste) does NOT return `nameRowMap`, so the bug never triggered.

## Fix (3 changes)

### 1. Code.gs — `getPersonnel()` — clone rows + switch to `rows[]` array

Replace lines 31-45:
```javascript
var seen = {};
var names = [];
var nameRowMap = {};       // DELETE
var rows = [];              // ADD: plain JS array of cloned rows
for (var r = 1; r < data.length; r++) {
  if (nameColIndex >= 0 && data[r][nameColIndex] !== undefined && data[r][nameColIndex] !== null) {
    var name = String(data[r][nameColIndex]).trim();
    if (name.length > 0 && !seen[name]) {
      seen[name] = true;
      names.push(name);
      // Clone Java array into plain JS array
      var rowClone = [];
      for (var c = 0; c < data[r].length; c++) {
        rowClone.push(data[r][c]);
      }
      rows.push(rowClone);
    }
  }
}
return { ok: true, names: names, rows: rows, headers: headers, nameColIndex: nameColIndex, rowCount: data.length - 1 };
```
Also update early return (line 15): `nameRowMap: {}` → `rows: []`

### 2. Code.gs — `exportGroupsCsv` — keep as-is (no change needed)

### 3. Index.html — `renderResults()` — use `rows[allNames.indexOf(name)]` instead of `nameRowMap[name]`

Replace:
```javascript
var row = personnelNameRowMap[name] || [];
```
With:
```javascript
var rowIndex = allNames.indexOf(name);
var row = (rowIndex >= 0 && rowIndex < rows.length) ? rows[rowIndex] : [];
```

Also in `loadPersonnel()` success handler:
- Replace `personnelNameRowMap = result.nameRowMap || {};` with `rows = result.rows || [];`
- Replace `var personnelNameRowMap = {};` declaration with `var rows = [];`

Also in `executeDelete()`: replace `personnelNameRowMap = {};` with `rows = [];`

## Validation

1. Upload sample .xlsx → names appear in search results ✓
2. Select display columns → extra badges appear under each name ✓
3. Search by name → filters correctly ✓
4. Export_Groups column select → download correct columns ✓
5. Personnel_DB column select → download correct columns ✓
