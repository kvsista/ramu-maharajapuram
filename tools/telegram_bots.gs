/**
 * Ramu Maharajapuram website – two Telegram bots on free Google Apps Script.
 *
 *  1. INTAKE bot  (public): anyone can send news. It asks one question at a time.
 *  2. APPROVAL bot (private): Ramu (and approvers he adds) get each submission with
 *     ✅ Publish / ❌ Reject buttons. Only published items reach the website.
 *
 * Storage: a Google Sheet with two tabs.
 *   "Submissions" – everything, including pending items and who sent them (PRIVATE, never publish).
 *   "Published"   – approved items only, public columns only. Publish ONLY this tab to the web as CSV;
 *                   the website (docs/news-config.js) reads that link.
 *
 * SETUP (one time, signed in to Ramu's Google account):
 *   1. In Telegram, message @BotFather → /newbot → create the intake bot (e.g. "Ramu Updates").
 *      Repeat → create the approval bot (e.g. "Ramu Approvals"). Keep both tokens private.
 *   2. script.google.com → New project → paste this file → Save.
 *   3. Project Settings (gear) → Script properties → add:
 *        INTAKE_TOKEN   = token of the intake bot
 *        APPROVAL_TOKEN = token of the approval bot
 *   4. Run → setup   (allow the permissions). The Execution log prints an OWNER CODE.
 *   5. Deploy → New deployment → type "Web app" → Execute as: Me → Who has access: Anyone → Deploy.
 *      Copy the Web app URL.
 *   6. Script properties → add WEBAPP_URL = that URL.  Then Run → connectBots.
 *   7. Ramu opens the approval bot in Telegram and sends:  /start OWNER-CODE
 *   8. In the sheet: File → Share → Publish to web → tab "Published" → CSV → Publish. Send that link
 *      to whoever maintains the website.
 * After changing this code later: Deploy → Manage deployments → edit → New version.
 */

var TYPES = ['Concert', 'New song or video', 'TV or interview', 'Award or honour', 'Other'];
var SUB_HEADERS = ['Id', 'Submitted', 'What is it?', 'Title', 'Date', 'City and venue', 'Details', 'Link', 'Photo',
                   'Your name', 'Telegram user id', 'Telegram username', 'Status', 'Reviewed by', 'Reviewed at'];
var PUB_HEADERS = ['What is it?', 'Title', 'Date', 'City and venue', 'Details', 'Link', 'Photo', 'Show'];
var MAX_PER_DAY = 5;

function props() { return PropertiesService.getScriptProperties(); }

/* ---------- one-time setup ---------- */

function setup() {
  var p = props();
  var ss;
  if (p.getProperty('SHEET_ID')) ss = SpreadsheetApp.openById(p.getProperty('SHEET_ID'));
  else {
    ss = SpreadsheetApp.create('Ramu website – updates');
    ss.setSpreadsheetLocale('en_US');
    p.setProperty('SHEET_ID', ss.getId());
  }
  var sub = ss.getSheetByName('Submissions') || ss.insertSheet('Submissions');
  sub.getRange(1, 1, 1, SUB_HEADERS.length).setValues([SUB_HEADERS]).setFontWeight('bold');
  sub.setFrozenRows(1);
  var pub = ss.getSheetByName('Published') || ss.insertSheet('Published');
  pub.getRange(1, 1, 1, PUB_HEADERS.length).setValues([PUB_HEADERS]).setFontWeight('bold');
  var s1 = ss.getSheetByName('Sheet1'); if (s1 && ss.getSheets().length > 2) ss.deleteSheet(s1);

  var folder;
  if (p.getProperty('FOLDER_ID')) folder = DriveApp.getFolderById(p.getProperty('FOLDER_ID'));
  else { folder = DriveApp.createFolder('Ramu website – photos'); p.setProperty('FOLDER_ID', folder.getId()); }

  if (!p.getProperty('HOOK_SECRET')) p.setProperty('HOOK_SECRET', Utilities.getUuid().replace(/-/g, ''));
  var code = 'OWNER-' + Math.floor(100000 + Math.random() * 900000);
  p.setProperty('OWNER_CODE', code);
  Logger.log('Sheet: ' + ss.getUrl());
  Logger.log('OWNER CODE (Ramu sends "/start ' + code + '" to the approval bot): ' + code);
}

function connectBots() {
  var p = props(), url = p.getProperty('WEBAPP_URL'), k = p.getProperty('HOOK_SECRET');
  if (!url) throw new Error('Add the WEBAPP_URL script property first.');
  [['intake', 'INTAKE_TOKEN'], ['approval', 'APPROVAL_TOKEN']].forEach(function (b) {
    var r = tg(b[1], 'setWebhook', { url: url + '?bot=' + b[0] + '&k=' + k, drop_pending_updates: true,
                                      allowed_updates: ['message', 'callback_query'] });
    Logger.log(b[0] + ' bot: ' + JSON.stringify(r));
  });
  tg('INTAKE_TOKEN', 'setMyCommands', { commands: [{ command: 'start', description: 'Share news for the website' },
                                                    { command: 'cancel', description: 'Start over' }] });
  tg('APPROVAL_TOKEN', 'setMyCommands', { commands: [
    { command: 'pending', description: 'Updates waiting for approval' },
    { command: 'live', description: 'News on the website (remove items)' },
    { command: 'invite', description: 'Add another approver' },
    { command: 'approvers', description: 'Who can approve' }] });
}

/* ---------- webhook ---------- */

function doPost(e) {
  var p = props();
  if (!e || !e.parameter || e.parameter.k !== p.getProperty('HOOK_SECRET')) return ok();
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(20000);
    var u = JSON.parse(e.postData.contents);
    // Telegram may resend an update; handle each one only once.
    var seen = CacheService.getScriptCache(), key = 'u:' + e.parameter.bot + ':' + u.update_id;
    if (seen.get(key)) return ok();
    seen.put(key, '1', 21600);
    if (e.parameter.bot === 'intake') intake(u); else if (e.parameter.bot === 'approval') approval(u);
  } catch (err) {
    console.error(err);
  } finally { lock.releaseLock(); }
  return ok();
}
function doGet() { return ok(); }
function ok() { return ContentService.createTextOutput('ok'); }

function tg(tokenProp, method, payload) {
  var res = UrlFetchApp.fetch('https://api.telegram.org/bot' + props().getProperty(tokenProp) + '/' + method, {
    method: 'post', contentType: 'application/json', payload: JSON.stringify(payload), muteHttpExceptions: true });
  return JSON.parse(res.getContentText());
}
function sendIntake(chat, text, extra) { return tg('INTAKE_TOKEN', 'sendMessage', Object.assign({ chat_id: chat, text: text }, extra || {})); }
function sendApproval(chat, text, extra) { return tg('APPROVAL_TOKEN', 'sendMessage', Object.assign({ chat_id: chat, text: text }, extra || {})); }
function kb(rows) { return { reply_markup: { inline_keyboard: rows } }; }
function clip(s, n) { s = String(s || '').trim(); return s.length > n ? s.slice(0, n) : s; }

/* ---------- intake bot (anyone) ---------- */

function getState(chat) { var s = CacheService.getScriptCache().get('st:' + chat); return s ? JSON.parse(s) : null; }
function setState(chat, s) { if (s) CacheService.getScriptCache().put('st:' + chat, JSON.stringify(s), 21600); else CacheService.getScriptCache().remove('st:' + chat); }

var STEPS = ['type', 'title', 'date', 'venue', 'details', 'link', 'photo', 'name', 'confirm'];
var ASK = {
  type: 'What would you like to share?',
  title: 'What is the title? For example: SPB Night with Ramu, Dallas',
  date: 'Which date? For example: 8 Nov 2026',
  venue: 'City and venue? (or tap Skip)',
  details: 'Any details visitors should know, like time, orchestra or tickets? (or tap Skip)',
  link: 'Any link: YouTube, Facebook, tickets or poster? (or tap Skip)',
  photo: 'Want to add a photo or poster? Send it now (or tap Skip)',
  name: 'Your name, so Ramu knows who sent this?'
};
var SKIPPABLE = { venue: 1, details: 1, link: 1, photo: 1 };

function ask(chat, st) {
  var step = STEPS[st.i];
  if (step === 'type') return sendIntake(chat, ASK.type, kb(TYPES.map(function (t) { return [{ text: t, callback_data: 'type:' + t }]; })));
  if (step === 'confirm') {
    return sendIntake(chat, summary(st.d) + '\n\nSend this for approval?', kb([[{ text: '✅ Send', callback_data: 'send' }, { text: '↺ Start over', callback_data: 'restart' }]]));
  }
  return sendIntake(chat, ASK[step], SKIPPABLE[step] ? kb([[{ text: 'Skip', callback_data: 'skip' }]]) : {});
}

function summary(d) {
  return [d.type + ' · ' + fmtDate(d.date) + (d.venue ? ' · ' + d.venue : ''), d.title, d.details || '', d.link || '',
          d.photo ? '(photo attached)' : '', 'From: ' + d.name].filter(String).join('\n');
}

function intake(u) {
  var msg = u.message, cb = u.callback_query;
  var chat = msg ? msg.chat : cb.message.chat;
  if (chat.type !== 'private') return;
  var from = msg ? msg.from : cb.from, st = getState(chat.id);
  if (cb) tg('INTAKE_TOKEN', 'answerCallbackQuery', { callback_query_id: cb.id });

  var text = msg && msg.text ? msg.text.trim() : '';
  if (text === '/start' || text === '/cancel' || (cb && cb.data === 'restart')) {
    if (overLimit(from.id)) return sendIntake(chat.id, 'Thank you! You have sent several updates today. Please try again tomorrow.');
    st = { i: 0, d: {} }; setState(chat.id, st);
    sendIntake(chat.id, 'Hi! I collect news for Ramu Maharajapuram\'s website: concerts, new songs or videos, TV appearances and awards. Ramu approves everything before it appears.');
    return ask(chat.id, st);
  }
  if (!st) return sendIntake(chat.id, 'Send /start to share news for Ramu\'s website.');

  var step = STEPS[st.i];
  if (cb && cb.data.indexOf('type:') === 0 && step === 'type') { st.d.type = cb.data.slice(5); return next(chat.id, st); }
  if (cb && cb.data === 'skip' && SKIPPABLE[step]) return next(chat.id, st);
  if (cb && cb.data === 'send' && step === 'confirm') return submit(chat.id, from, st);

  if (step === 'photo' && msg && msg.photo) { st.d.photo = msg.photo[msg.photo.length - 1].file_id; return next(chat.id, st); }
  if (!text) return ask(chat.id, st);
  if (step === 'title') st.d.title = clip(text, 120);
  else if (step === 'date') {
    var iso = parseDate(text);
    if (!iso) return sendIntake(chat.id, 'Sorry, I didn\'t understand that date. Please write it like 8 Nov 2026.');
    st.d.date = iso;
  }
  else if (step === 'venue') st.d.venue = clip(text, 120);
  else if (step === 'details') st.d.details = clip(text, 600);
  else if (step === 'link') {
    if (!/^https?:\/\/\S+$/i.test(text)) return sendIntake(chat.id, 'Please send a full link starting with https://, or tap Skip.', kb([[{ text: 'Skip', callback_data: 'skip' }]]));
    st.d.link = clip(text, 300);
  }
  else if (step === 'name') st.d.name = clip(text, 80);
  else return ask(chat.id, st);
  return next(chat.id, st);
}

function next(chat, st) { st.i++; setState(chat, st); return ask(chat, st); }

function overLimit(userId) {
  var c = CacheService.getScriptCache(), key = 'n:' + userId + ':' + Utilities.formatDate(new Date(), 'GMT', 'yyyyMMdd');
  return Number(c.get(key) || 0) >= MAX_PER_DAY;
}

function submit(chat, from, st) {
  var c = CacheService.getScriptCache(), key = 'n:' + from.id + ':' + Utilities.formatDate(new Date(), 'GMT', 'yyyyMMdd');
  if (overLimit(from.id)) { setState(chat, null); return sendIntake(chat, 'Thank you! You have sent several updates today. Please try again tomorrow.'); }
  c.put(key, String(Number(c.get(key) || 0) + 1), 86400);

  var d = st.d, photoUrl = '';
  if (d.photo) photoUrl = savePhoto(d.photo);
  var id = 'U' + Date.now().toString(36);
  sheet('Submissions').appendRow([id, new Date(), d.type, d.title, d.date, d.venue || '', d.details || '', d.link || '', photoUrl,
                                  d.name, String(from.id), from.username || '', 'Pending', '', '']);
  setState(chat, null);
  sendIntake(chat, 'Thank you! Your update was sent to Ramu for approval. I\'ll let you know when it\'s on the website.');
  notifyApprovers(id);
}

function savePhoto(fileId) {
  try {
    var f = tg('INTAKE_TOKEN', 'getFile', { file_id: fileId }).result;
    var blob = UrlFetchApp.fetch('https://api.telegram.org/file/bot' + props().getProperty('INTAKE_TOKEN') + '/' + f.file_path).getBlob();
    var file = DriveApp.getFolderById(props().getProperty('FOLDER_ID')).createFile(blob.setName('update-' + Date.now() + '.jpg'));
    file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    return 'https://drive.google.com/thumbnail?id=' + file.getId() + '&sz=w1000';
  } catch (e) { console.error(e); return ''; }
}

/* ---------- approval bot (Ramu + approvers) ---------- */

function approvers() { return JSON.parse(props().getProperty('APPROVERS') || '{}'); }
function saveApprovers(a) { props().setProperty('APPROVERS', JSON.stringify(a)); }

function approval(u) {
  var msg = u.message, cb = u.callback_query;
  var chat = msg ? msg.chat : cb.message.chat;
  if (chat.type !== 'private') return;
  var from = msg ? msg.from : cb.from, a = approvers(), me = a[String(from.id)];
  var text = msg && msg.text ? msg.text.trim() : '';

  // Claiming ownership or joining with an invite code
  var m = text.match(/^\/start\s+(\S+)/);
  if (m) {
    var p = props(), code = m[1];
    if (code === p.getProperty('OWNER_CODE') && !Object.keys(a).some(function (k) { return a[k].owner; })) {
      a[String(from.id)] = { name: from.first_name || 'Owner', owner: true }; saveApprovers(a); p.deleteProperty('OWNER_CODE');
      return sendApproval(chat.id, 'You are now the owner. New updates will arrive here with Publish / Reject buttons.\n\nCommands: /pending /live /invite /approvers');
    }
    var inv = JSON.parse(p.getProperty('INVITES') || '{}');
    if (inv[code] && inv[code] > Date.now()) {
      delete inv[code]; p.setProperty('INVITES', JSON.stringify(inv));
      a[String(from.id)] = { name: from.first_name || 'Approver' }; saveApprovers(a);
      notifyAll('👤 ' + (from.first_name || 'Someone') + ' joined as an approver.');
      return sendApproval(chat.id, 'Welcome! You can now approve updates for Ramu\'s website. Commands: /pending /live');
    }
  }
  if (!me) { if (msg) sendApproval(chat.id, 'This bot is private. To send news for the website, use the updates bot instead.'); return; }

  if (cb) {
    tg('APPROVAL_TOKEN', 'answerCallbackQuery', { callback_query_id: cb.id });
    var parts = cb.data.split(':'), action = parts[0], id = parts[1];
    if (action === 'ap' || action === 'rj') return review(id, action === 'ap', from, cb.message);
    if (action === 'rm') return unpublish(id, from, cb.message);
    if (action === 'kick' && me.owner) { delete a[id]; saveApprovers(a); return sendApproval(chat.id, 'Removed.'); }
    return;
  }
  if (text === '/start' || text === '/help') return sendApproval(chat.id, 'Commands:\n/pending – updates waiting for you\n/live – news on the website (remove items)\n/invite – add another approver\n/approvers – who can approve');
  if (text === '/pending') {
    var pend = rows().filter(function (r) { return r.Status === 'Pending'; });
    if (!pend.length) return sendApproval(chat.id, 'Nothing waiting. 🎉');
    return pend.forEach(function (r) { card(chat.id, r); });
  }
  if (text === '/live') {
    var live = rows().filter(function (r) { return r.Status === 'Published'; }).slice(-15);
    if (!live.length) return sendApproval(chat.id, 'No news on the website yet.');
    return live.forEach(function (r) {
      sendApproval(chat.id, fmtDate(r.Date) + ' · ' + r.Title, kb([[{ text: '🗑 Remove from website', callback_data: 'rm:' + r.Id }]]));
    });
  }
  if (text === '/invite') {
    var p2 = props(), inv2 = JSON.parse(p2.getProperty('INVITES') || '{}'), c2 = 'JOIN-' + Math.floor(100000 + Math.random() * 900000);
    inv2[c2] = Date.now() + 48 * 3600 * 1000; p2.setProperty('INVITES', JSON.stringify(inv2));
    return sendApproval(chat.id, 'Ask the new approver to open this bot and send:\n/start ' + c2 + '\n(The code works once, for 48 hours.)');
  }
  if (text === '/approvers') {
    return Object.keys(a).forEach(function (k) {
      sendApproval(chat.id, a[k].name + (a[k].owner ? ' (owner)' : ''),
        me.owner && !a[k].owner ? kb([[{ text: 'Remove', callback_data: 'kick:' + k }]]) : {});
    });
  }
  sendApproval(chat.id, 'Commands: /pending /live /invite /approvers');
}

function card(chat, r) {
  var text = '📝 New update\n\n' + [r['What is it?'] + ' · ' + fmtDate(r.Date) + (r['City and venue'] ? ' · ' + r['City and venue'] : ''),
    r.Title, r.Details, r.Link, 'From: ' + r['Your name'] + (r['Telegram username'] ? ' (@' + r['Telegram username'] + ')' : '')].filter(String).join('\n');
  var buttons = kb([[{ text: '✅ Publish', callback_data: 'ap:' + r.Id }, { text: '❌ Reject', callback_data: 'rj:' + r.Id }]]);
  if (r.Photo) {
    var res = tg('APPROVAL_TOKEN', 'sendPhoto', Object.assign({ chat_id: chat, photo: r.Photo, caption: text.slice(0, 1000) }, buttons));
    if (res && res.ok) return res;
    text += '\nPhoto: ' + r.Photo;
  }
  return sendApproval(chat, text, buttons);
}

function notifyApprovers(id) {
  var r = rows().filter(function (x) { return x.Id === id; })[0], a = approvers();
  Object.keys(a).forEach(function (k) { card(k, r); });
}
function notifyAll(text) { var a = approvers(); Object.keys(a).forEach(function (k) { sendApproval(k, text); }); }

function review(id, publish, from, message) {
  var sh = sheet('Submissions'), data = sh.getDataRange().getValues(), H = data[0];
  for (var i = 1; i < data.length; i++) {
    if (data[i][0] !== id) continue;
    var status = data[i][H.indexOf('Status')];
    if (status !== 'Pending') return sendApproval(message.chat.id, 'Already ' + status.toLowerCase() + '.');
    sh.getRange(i + 1, H.indexOf('Status') + 1, 1, 3).setValues([[publish ? 'Published' : 'Rejected', from.first_name || '', new Date()]]);
    rebuildPublished();
    var title = data[i][H.indexOf('Title')];
    notifyAll((publish ? '✅ Published: ' : '❌ Rejected: ') + title + ' (by ' + (from.first_name || 'approver') + ')');
    var submitter = data[i][H.indexOf('Telegram user id')];
    if (submitter && publish) sendIntake(submitter, '🎉 Your update "' + title + '" is now on Ramu\'s website. Thank you!');
    return;
  }
}

function unpublish(id, from, message) {
  var sh = sheet('Submissions'), data = sh.getDataRange().getValues(), H = data[0];
  for (var i = 1; i < data.length; i++) {
    if (data[i][0] !== id) continue;
    sh.getRange(i + 1, H.indexOf('Status') + 1, 1, 3).setValues([['Removed', from.first_name || '', new Date()]]);
    rebuildPublished();
    return sendApproval(message.chat.id, 'Removed from the website: ' + data[i][H.indexOf('Title')]);
  }
}

/* ---------- sheet helpers ---------- */

function sheet(name) { return SpreadsheetApp.openById(props().getProperty('SHEET_ID')).getSheetByName(name); }

function rows() {
  var data = sheet('Submissions').getDataRange().getValues(), H = data.shift();
  return data.map(function (r) {
    var o = {}; H.forEach(function (h, j) { o[h] = r[j] instanceof Date && h === 'Date' ? Utilities.formatDate(r[j], 'GMT', 'yyyy-MM-dd') : r[j]; });
    return o;
  });
}

function rebuildPublished() {
  var pub = sheet('Published');
  var live = rows().filter(function (r) { return r.Status === 'Published'; }).map(function (r) {
    return [r['What is it?'], r.Title, "'" + r.Date, r['City and venue'], r.Details, r.Link, r.Photo, 'Yes'];
  });
  pub.getRange(2, 1, Math.max(pub.getMaxRows() - 1, 1), PUB_HEADERS.length).clearContent();
  if (live.length) pub.getRange(2, 1, live.length, PUB_HEADERS.length).setValues(live);
}

/* ---------- dates ---------- */

var MONTHS = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };
function month(word) { return MONTHS[String(word).slice(0, 3)] || null; }
// Accepts "8 Nov 2026", "Nov 8", "8th November", "08/11/2026" (day first, as in India), "2026-11-08".
function parseDate(t) {
  t = String(t).toLowerCase().replace(/(\d)(st|nd|rd|th)\b/g, '$1').replace(/,/g, ' ').replace(/\s+/g, ' ').trim();
  var y = new Date().getFullYear(), m = null, d = null, x;
  if ((x = t.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/))) { y = +x[1]; m = +x[2]; d = +x[3]; }
  else if ((x = t.match(/^(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{2,4})$/))) { d = +x[1]; m = +x[2]; y = +x[3]; }
  else if ((x = t.match(/^(\d{1,2}) ([a-z]+)(?: (\d{4}))?$/))) { d = +x[1]; m = month(x[2]); if (x[3]) y = +x[3]; }
  else if ((x = t.match(/^([a-z]+) (\d{1,2})(?: (\d{4}))?$/))) { m = month(x[1]); d = +x[2]; if (x[3]) y = +x[3]; }
  if (!m || !d) return null;
  if (y < 100) y += 2000;
  var dt = new Date(Date.UTC(y, m - 1, d));
  if (dt.getUTCMonth() !== m - 1 || dt.getUTCDate() !== d || y < 1990 || y > 2100) return null;
  return dt.toISOString().slice(0, 10);
}
function fmtDate(iso) { var p = String(iso).split('-'); return p.length === 3 ? +p[2] + ' ' + ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+p[1] - 1] + ' ' + p[0] : iso; }
