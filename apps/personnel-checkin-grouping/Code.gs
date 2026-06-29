var EXPORT_SHEET = 'Export_Groups';
var PERSONNEL_DB_SHEET = 'Personnel_DB';
var HEADER_LABELS = ['ชื่อ-นามสกุล', 'ชื่อ นามสกุล', 'ชื่อ', 'name', 'fullname'];

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('ระบบเช็คอินเจ้าหน้าที่');
}

function getPersonnel() {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(PERSONNEL_DB_SHEET);
    if (!sheet || sheet.getLastRow() < 2) {
      return { ok: true, names: [], headers: [], nameColIndex: -1, rowCount: 0, rows: [] };
    }
    var lastRow = sheet.getLastRow();
    var lastCol = sheet.getLastColumn();
    var data = sheet.getRange(1, 1, lastRow, lastCol).getValues();
    var headers = data[0];

    var nameColIndex = -1;
    for (var i = 0; i < headers.length; i++) {
      var normalized = normalizeThaiHeader(String(headers[i]));
      if (matchesHeaderLabel(normalized)) {
        nameColIndex = i;
        break;
      }
    }

    var seen = {};
    var names = [];
    var rows = [];
    for (var r = 1; r < data.length; r++) {
      if (nameColIndex >= 0 && data[r][nameColIndex] !== undefined && data[r][nameColIndex] !== null) {
        var name = String(data[r][nameColIndex]).trim();
        if (name.length > 0 && !seen[name]) {
          seen[name] = true;
          names.push(name);
          var rowClone = [];
          for (var cc = 0; cc < data[r].length; cc++) {
            var cellVal = data[r][cc];
            if (typeof cellVal === 'object' && cellVal !== null && typeof cellVal.toISOString === 'function') {
              rowClone.push(cellVal.toISOString());
            } else {
              rowClone.push(cellVal);
            }
          }
          rows.push(rowClone);
        }
      }
    }

    return { ok: true, names: names, rows: rows, headers: headers, nameColIndex: nameColIndex, rowCount: data.length - 1 };
  } catch (e) {
    return { ok: false, error: 'เกิดข้อผิดพลาด: ' + e.toString() };
  }
}

function normalizeThaiHeader(str) {
  return str
    .replace(/[\u200B\u200C\u200D\uFEFF\u00A0]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

function matchesHeaderLabel(normalized) {
  for (var i = 0; i < HEADER_LABELS.length; i++) {
    var label = HEADER_LABELS[i]
      .replace(/[\u200B\u200C\u200D\uFEFF\u00A0]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();
    if (normalized === label) {
      return true;
    }
  }
  return false;
}

function getOrCreatePersonnelDb(ss) {
  var sheet = ss.getSheetByName(PERSONNEL_DB_SHEET);
  if (!sheet) {
    sheet = ss.insertSheet(PERSONNEL_DB_SHEET);
  }
  return sheet;
}

function uploadPersonnel(rows) {
  try {
    if (!Array.isArray(rows) || rows.length === 0) {
      return { ok: false, error: 'ไม่มีข้อมูลในไฟล์' };
    }
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = getOrCreatePersonnelDb(ss);

    var headerRowIdx = -1;
    var nameCol = -1;
    for (var scan = 0; scan < Math.min(3, rows.length); scan++) {
      var row = rows[scan];
      if (!row) continue;
      for (var c = 0; c < row.length; c++) {
        var cell = String(row[c] || '').trim();
        if (cell.length === 0) continue;
        if (matchesHeaderLabel(normalizeThaiHeader(cell))) {
          headerRowIdx = scan;
          nameCol = c;
          break;
        }
      }
      if (headerRowIdx >= 0) break;
    }

    if (nameCol === -1) {
      nameCol = 0;
      headerRowIdx = -1;
    }

    var dataStart = (headerRowIdx >= 0) ? headerRowIdx + 1 : 0;
    var finalHeaders = (headerRowIdx >= 0) ? rows[headerRowIdx] : [];
    var maxCols = finalHeaders.length > 0 ? finalHeaders.length : 0;
    if (maxCols === 0 && rows.length > 0) {
      for (var rr = 0; rr < rows.length; rr++) {
        if (rows[rr] && rows[rr].length > maxCols) maxCols = rows[rr].length;
      }
    }

    var dataRows = [];
    if (finalHeaders.length > 0) {
      dataRows.push(finalHeaders.slice());
    }

    for (var r = dataStart; r < rows.length; r++) {
      if (!rows[r]) continue;
      var rowData = [];
      for (var cc = 0; cc < maxCols; cc++) {
        rowData.push((rows[r][cc] !== undefined && rows[r][cc] !== null) ? rows[r][cc] : '');
      }
      dataRows.push(rowData);
    }

    if (dataRows.length < 2) {
      return { ok: false, error: 'ไม่พบข้อมูลบุคลากรในไฟล์' };
    }

    sheet.clear();
    sheet.getRange(1, 1, dataRows.length, dataRows[0].length).setValues(dataRows);

    var personCount = 0;
    if (nameCol < dataRows[0].length) {
      for (var p = 1; p < dataRows.length; p++) {
        var pv = dataRows[p][nameCol];
        if (pv !== undefined && pv !== null && String(pv).trim().length > 0) {
          personCount++;
        }
      }
    }

    return {
      ok: true,
      added: personCount,
      total: personCount,
      headers: dataRows[0],
      nameColumnIndex: nameCol
    };
  } catch (e) {
    return { ok: false, error: 'เกิดข้อผิดพลาด: ' + e.toString() };
  }
}

function clearPersonnel() {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(PERSONNEL_DB_SHEET);
    if (!sheet || sheet.getLastRow() <= 1) {
      return { ok: true, removed: 0 };
    }
    var count = sheet.getLastRow() - 1;
    sheet.deleteRows(2, count);
    return { ok: true, removed: count };
  } catch (e) {
    return { ok: false, error: 'เกิดข้อผิดพลาด: ' + e.toString() };
  }
}

function exportPersonnelCsv(columnIndices) {
  try {
    if (!Array.isArray(columnIndices) || columnIndices.length === 0) {
      return { ok: false, error: 'กรุณาเลือกอย่างน้อย 1 คอลัมน์' };
    }
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(PERSONNEL_DB_SHEET);
    if (!sheet || sheet.getLastRow() < 2) {
      return { ok: false, error: 'ไม่มีข้อมูลใน Personnel_DB' };
    }
    var lastRow = sheet.getLastRow();
    var lastCol = sheet.getLastColumn();
    var data = sheet.getRange(1, 1, lastRow, lastCol).getValues();

    for (var v = 0; v < columnIndices.length; v++) {
      if (columnIndices[v] < 0 || columnIndices[v] >= lastCol) {
        return { ok: false, error: 'หมายเลขคอลัมน์ไม่ถูกต้อง' };
      }
    }

    var lines = [];
    for (var r = 0; r < data.length; r++) {
      var row = [];
      for (var c = 0; c < columnIndices.length; c++) {
        row.push(csvEscape(data[r][columnIndices[c]]));
      }
      lines.push(row.join(','));
    }
    return { ok: true, csv: lines.join('\n') };
  } catch (e) {
    return { ok: false, error: 'เกิดข้อผิดพลาด: ' + e.toString() };
  }
}

function exportGroupsCsv(egIndices, dbIndices) {
  try {
    if (!Array.isArray(egIndices) || egIndices.length === 0) {
      return { ok: false, error: 'กรุณาเลือกคอลัมน์ Export_Groups อย่างน้อย 1 คอลัมน์' };
    }
    if (!Array.isArray(dbIndices)) {
      dbIndices = [];
    }
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(EXPORT_SHEET);
    if (!sheet || sheet.getLastRow() === 0) {
      return { ok: false, error: 'ไม่มีข้อมูลใน Export_Groups' };
    }
    var lastRow = sheet.getLastRow();
    var data = sheet.getRange(1, 1, lastRow, 4).getValues();

    for (var v = 0; v < egIndices.length; v++) {
      if (egIndices[v] < 0 || egIndices[v] > 3) {
        return { ok: false, error: 'หมายเลขคอลัมน์ Export_Groups ไม่ถูกต้อง' };
      }
    }

    var dbMap = null;
    var dbHeaders = null;
    var dbNameCol = -1;
    if (dbIndices.length > 0) {
      var dbSheet = ss.getSheetByName(PERSONNEL_DB_SHEET);
      if (dbSheet && dbSheet.getLastRow() >= 2) {
        var dbLastRow = dbSheet.getLastRow();
        var dbLastCol = dbSheet.getLastColumn();
        var dbData = dbSheet.getRange(1, 1, dbLastRow, dbLastCol).getValues();
        dbHeaders = dbData[0];
        for (var h = 0; h < dbHeaders.length; h++) {
          if (matchesHeaderLabel(normalizeThaiHeader(String(dbHeaders[h])))) {
            dbNameCol = h;
            break;
          }
        }
        if (dbNameCol >= 0) {
          dbMap = {};
          for (var r = 1; r < dbData.length; r++) {
            var dbName = String(dbData[r][dbNameCol]).trim();
            if (dbName.length > 0 && dbMap[dbName] === undefined) {
              dbMap[dbName] = dbData[r];
            }
          }
        }
        for (var d = 0; d < dbIndices.length; d++) {
          if (dbIndices[d] < 0 || dbIndices[d] >= dbLastCol) {
            return { ok: false, error: 'หมายเลขคอลัมน์ฐานข้อมูลไม่ถูกต้อง' };
          }
        }
      }
    }

    var lines = [];
    for (var r = 0; r < data.length; r++) {
      var row = [];
      for (var c = 0; c < egIndices.length; c++) {
        row.push(csvEscape(data[r][egIndices[c]]));
      }
      if (dbIndices.length > 0 && dbHeaders) {
        if (r === 0) {
          for (var d = 0; d < dbIndices.length; d++) {
            row.push(csvEscape(dbHeaders[dbIndices[d]]));
          }
        } else {
          var personName = String(data[r][1] || '').trim();
          var dbRow = dbMap !== null ? dbMap[personName] : undefined;
          for (var d = 0; d < dbIndices.length; d++) {
            if (dbRow && dbIndices[d] < dbRow.length) {
              row.push(csvEscape(dbRow[dbIndices[d]]));
            } else {
              row.push('');
            }
          }
        }
      } else if (dbIndices.length > 0) {
        for (var d = 0; d < dbIndices.length; d++) {
          row.push('');
        }
      }
      lines.push(row.join(','));
    }
    return { ok: true, csv: lines.join('\n') };
  } catch (e) {
    return { ok: false, error: 'เกิดข้อผิดพลาด: ' + e.toString() };
  }
}

function saveGroup(groupName, names) {
  try {
    if (!groupName || String(groupName).trim().length === 0) {
      return { ok: false, error: 'กรุณากรอกชื่อกลุ่ม' };
    }
    if (!Array.isArray(names) || names.length === 0) {
      return { ok: false, error: 'กรุณาเลือกบุคลากรอย่างน้อย 1 คน' };
    }
    var trimmedGroup = String(groupName).trim();
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var exportSheet = ss.getSheetByName(EXPORT_SHEET);
    if (!exportSheet) {
      exportSheet = ss.insertSheet(EXPORT_SHEET);
      exportSheet.appendRow(['Timestamp', 'Name', 'Group Name', 'Status']);
    } else {
      var exportHeaders = exportSheet.getRange(1, 1, 1, 4).getValues()[0];
      var expected = ['Timestamp', 'Name', 'Group Name', 'Status'];
      var hasHeader = exportHeaders[0] === expected[0]
        && exportHeaders[1] === expected[1]
        && exportHeaders[2] === expected[2]
        && exportHeaders[3] === expected[3];
      if (!hasHeader) {
        exportSheet.insertRowBefore(1);
        exportSheet.getRange(1, 1, 1, 4).setValues([expected]);
      }
    }
    var rows = [];
    var now = new Date();
    for (var i = 0; i < names.length; i++) {
      rows.push([now, String(names[i]).trim(), trimmedGroup, 'Checked-in']);
    }
    var lastRow = exportSheet.getLastRow();
    exportSheet.getRange(lastRow + 1, 1, rows.length, 4).setValues(rows);
    return { ok: true, count: names.length };
  } catch (e) {
    return { ok: false, error: 'เกิดข้อผิดพลาด: ' + e.toString() };
  }
}

function getExportCsv() {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var exportSheet = ss.getSheetByName(EXPORT_SHEET);
    if (!exportSheet || exportSheet.getLastRow() === 0) {
      return { ok: true, csv: 'Timestamp,Name,Group Name,Status' };
    }
    var lastRow = exportSheet.getLastRow();
    var data = exportSheet.getRange(1, 1, lastRow, 4).getValues();
    var lines = [];
    for (var i = 0; i < data.length; i++) {
      var row = [];
      for (var j = 0; j < data[i].length; j++) {
        row.push(csvEscape(data[i][j]));
      }
      lines.push(row.join(','));
    }
    return { ok: true, csv: lines.join('\n') };
  } catch (e) {
    return { ok: false, error: 'เกิดข้อผิดพลาด: ' + e.toString() };
  }
}

function csvEscape(value) {
  if (value instanceof Date) {
    value = value.toISOString();
  } else {
    value = String(value);
  }
  if (value.indexOf(',') !== -1 || value.indexOf('"') !== -1 || value.indexOf('\n') !== -1) {
    value = '"' + value.replace(/"/g, '""') + '"';
  }
  return value;
}
