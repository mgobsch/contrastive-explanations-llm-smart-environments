/**
 * SmartEx study – receives answers from the study page and writes them into this Google Sheet.
 * One row per participant (pid). A later message from the same participant updates that row,
 * so partial answers (after each situation) are replaced by the complete answers at the end.
 *
 * Sheet "Answers": one column per value (easy to analyse / export to Excel)
 * Sheet "Raw Data":  the complete raw data as JSON (backup, nothing gets lost)
 */
// ID of the Google Sheet the answers are written into (the part between /d/ and /edit in its address)
var SHEET_ID = '1uVBdl9cdbfP2r6fCstALj2_TuoDuU5WdtdBeoESOFhA';

// Bot protection
var MAX_NEW_PER_HOUR = 30;     // more new participants than this within one hour -> study pauses automatically
var MAX_BODY_CHARS = 300000;   // larger submissions are rejected (a real one is far smaller)
var ALERT_EMAIL = '';          // '' = the Google account that owns this script

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);                       // avoid two participants writing at the same moment
  try {
    var props = PropertiesService.getScriptProperties();
    if (props.getProperty('PAUSED') === 'true') return ContentService.createTextOutput('paused');

    // basic check: only accept submissions that look like they come from the study page
    var body = e && e.postData ? e.postData.contents : '';
    if (!body || body.length > MAX_BODY_CHARS) return ContentService.createTextOutput('rejected');
    var payload = JSON.parse(body);
    var summary = payload && payload.summary;
    if (!summary || typeof summary !== 'object' || !payload.raw || typeof payload.raw !== 'object' ||
        typeof summary.pid !== 'string' || !/^P[0-9a-z]{8,24}$/.test(summary.pid)) {
      return ContentService.createTextOutput('rejected');
    }

    summary.received_at = new Date().toISOString();
    var ss = SpreadsheetApp.openById(SHEET_ID);
    var answers = getSheet_(ss, 'Answers');

    // automatic stop: too many NEW participants within one hour
    if (!pidExists_(answers, summary.pid)) {
      var now = Date.now();
      var times = JSON.parse(props.getProperty('NEW_TIMES') || '[]').filter(function (t) { return now - t < 60 * 60 * 1000; });
      if (times.length >= MAX_NEW_PER_HOUR) {
        props.setProperty('PAUSED', 'true');
        sendAlert_('More than ' + MAX_NEW_PER_HOUR + ' new participants within one hour. The study has been paused automatically. ' +
                   'Check the sheet (and the backups), then run resumeStudy() in Apps Script to continue.');
        return ContentService.createTextOutput('paused');
      }
      times.push(now);
      props.setProperty('NEW_TIMES', JSON.stringify(times));
    }

    upsertRow_(answers, summary);
    upsertRow_(getSheet_(ss, 'Raw Data'), {pid: summary.pid, received_at: summary.received_at, finished: summary.finished, raw_json: JSON.stringify(payload.raw)});
    return ContentService.createTextOutput('ok');
  } catch (err) {
    console.error(err);                       // shows up under "Executions" in Apps Script
    return ContentService.createTextOutput('error: ' + err);
  } finally {
    lock.releaseLock();
  }
}

function doGet() {                            // lets you check in the browser that the web app is running
  return ContentService.createTextOutput('SmartEx study endpoint is running.');
}

/* ---------- on/off switch: run these by hand in Apps Script ---------- */
function pauseStudy() {                       // stop accepting answers immediately
  PropertiesService.getScriptProperties().setProperty('PAUSED', 'true');
}
function resumeStudy() {                      // accept answers again (also resets the hourly counter)
  var props = PropertiesService.getScriptProperties();
  props.setProperty('PAUSED', 'false');
  props.setProperty('NEW_TIMES', '[]');
}

function sendAlert_(text) {
  try {
    var to = ALERT_EMAIL || Session.getEffectiveUser().getEmail();
    if (to) MailApp.sendEmail(to, 'SmartEx study paused', text);
  } catch (err) { console.error(err); }
}

// true if a row with this pid already exists in the sheet
function pidExists_(sheet, pid) {
  var lastCol = sheet.getLastColumn(), lastRow = sheet.getLastRow();
  if (lastCol === 0 || lastRow < 2) return false;
  var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  var col = headers.indexOf('pid') + 1;
  if (col === 0) return false;
  var pids = sheet.getRange(2, col, lastRow - 1, 1).getValues();
  for (var i = 0; i < pids.length; i++) { if (pids[i][0] === pid) return true; }
  return false;
}

function getSheet_(ss, name) {
  return ss.getSheetByName(name) || ss.insertSheet(name);
}

// Writes obj as a row. Adds any new column headers automatically. Updates the row if the pid exists.
function upsertRow_(sheet, obj) {
  var keys = Object.keys(obj);
  var lastCol = sheet.getLastColumn();
  var headers = lastCol > 0 ? sheet.getRange(1, 1, 1, lastCol).getValues()[0] : [];
  keys.forEach(function (k) { if (headers.indexOf(k) === -1) headers.push(k); });
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');
  sheet.setFrozenRows(1);

  var row = headers.map(function (h) {
    var v = obj.hasOwnProperty(h) ? obj[h] : '';
    if (typeof v === 'string' && v.length > 49000) v = v.slice(0, 49000);   // Google Sheets cell limit
    return v === null || v === undefined ? '' : v;
  });

  var pidCol = headers.indexOf('pid') + 1;
  var lastRow = sheet.getLastRow();
  var target = lastRow + 1;
  if (lastRow > 1) {
    var pids = sheet.getRange(2, pidCol, lastRow - 1, 1).getValues();
    for (var i = 0; i < pids.length; i++) { if (pids[i][0] === obj.pid) { target = i + 2; break; } }
  }
  sheet.getRange(target, 1, 1, row.length).setValues([row]);
}

/* =====================================================================
 * Hourly backup of this Google Sheet
 * - backupNow():          copies the whole sheet into the Drive folder "SmartEx study backups"
 *                         and moves backups older than BACKUP_KEEP_DAYS to the Drive trash
 * - startHourlyBackup():  run ONCE by hand to switch on the hourly backup (never creates two timers)
 * - stopHourlyBackup():   run by hand to switch the hourly backup off again
 * ===================================================================== */
var BACKUP_FOLDER_NAME = 'SmartEx study backups';
var BACKUP_KEEP_DAYS = 7;

function backupNow() {
  var folder = getBackupFolder_();
  var stamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm');
  DriveApp.getFileById(SHEET_ID).makeCopy('Backup ' + stamp, folder);

  // remove old backups (only files created by this function, recognisable by the name "Backup ...")
  var cutoff = new Date(Date.now() - BACKUP_KEEP_DAYS * 24 * 60 * 60 * 1000);
  var files = folder.getFiles();
  while (files.hasNext()) {
    var f = files.next();
    if (f.getName().indexOf('Backup ') === 0 && f.getDateCreated() < cutoff) f.setTrashed(true);
  }
}

function startHourlyBackup() {
  stopHourlyBackup();                         // remove an existing timer first, so there is never more than one
  ScriptApp.newTrigger('backupNow').timeBased().everyHours(1).create();
  backupNow();                                // make the first backup right away
}

function stopHourlyBackup() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'backupNow') ScriptApp.deleteTrigger(t);
  });
}

function getBackupFolder_() {
  var folders = DriveApp.getFoldersByName(BACKUP_FOLDER_NAME);
  return folders.hasNext() ? folders.next() : DriveApp.createFolder(BACKUP_FOLDER_NAME);
}
