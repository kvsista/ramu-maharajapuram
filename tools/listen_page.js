document.getElementById('yr').textContent = new Date().getFullYear();
const SONGS = __SONGS__;
const ICON_PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.4v13.2a1.1 1.1 0 0 0 1.7.92l10.1-6.6a1.1 1.1 0 0 0 0-1.84L9.7 4.48A1.1 1.1 0 0 0 8 5.4z"/></svg>';
const ICON_PAUSE = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6.5" y="5" width="4" height="14" rx="1.2"/><rect x="13.5" y="5" width="4" height="14" rx="1.2"/></svg>';
const items = [...document.querySelectorAll('.song')];
const byId = new Map(SONGS.map((s, i) => [s.id, i]));
const $ = (id) => document.getElementById(id);
let sel = 0;  // song shown in the card when nothing is playing yet

function visible() { return items.filter(li => !li.hidden).map(li => +li.dataset.i); }
function shownIndex() { const c = RP.current(); return c && byId.has(c.id) ? byId.get(c.id) : sel; }
function mark() {
  const i = shownIndex(), s = SONGS[i], c = RP.current();
  items.forEach(li => li.classList.toggle('playing', +li.dataset.i === i));
  $('now-title').textContent = c ? c.t : s.t; $('now-album').textContent = c ? c.a : s.a;
  const L = (c ? c.l : s.l) || {}, names = [['spotify', 'Spotify'], ['apple', 'Apple Music'], ['ytmusic', 'YouTube Music'], ['jiosaavn', 'JioSaavn'], ['deezer', 'Deezer']];
  const apps = $('apps'); apps.replaceChildren();
  const lab = document.createElement('span'); lab.className = 'apps-label'; lab.textContent = 'Open in'; apps.append(lab);
  names.forEach(([k, n]) => { if (!L[k]) return; const a = document.createElement('a'); a.href = L[k]; a.target = '_blank'; a.rel = 'noopener'; a.className = 'app-chip'; a.textContent = n; apps.append(a); });
  const NAMES = { apple: 'Apple Music', spotify: 'Spotify', deezer: 'Deezer' };
  const srcNow = RP.getSource(), apple = RP.usingApple(), wantApple = srcNow !== 'yt', appName = NAMES[srcNow];
  $('start').hidden = !!c || apple;
  const note = $('src-note'), song = c || s;
  // Only offer the apps this song is actually on (YouTube always). The highlighted button is the one playing.
  const inUse = apple ? srcNow : 'yt';
  document.querySelectorAll('.src-btn').forEach(b => {
    const ok = b.dataset.src === 'yt' || RP.hasSource(song, b.dataset.src);
    b.hidden = !ok;
    b.setAttribute('aria-pressed', String(b.dataset.src === inUse));
  });
  if (apple) {
    note.textContent = 'Press play in the ' + appName + ' player. You\u2019ll hear a preview, or the full song if you\u2019re signed in to ' + appName + ' in this browser.'
      + (srcNow === 'apple' ? ' Still a preview after signing in? Safari may block it; sign in at music.apple.com in this browser first, or tap Apple Music under \u201cOpen in\u201d.' : '');
    note.hidden = false;
  }
  else note.hidden = true;
  const p = RP.isPlaying();
  $('shuffle').setAttribute('aria-pressed', RP.getShuffle());
}
function playAt(i) {
  const v = visible(); const order = v.includes(i) ? v : SONGS.map((_, k) => k);
  RP.play(order.map(k => SONGS[k]), order.indexOf(i));
}
items.forEach(li => li.querySelector('button').addEventListener('click', () => playAt(+li.dataset.i)));
$('start').addEventListener('click', () => playAt(shownIndex()));
$('next').addEventListener('click', () => { if (RP.current()) RP.next(); else playAt(visible()[(visible().indexOf(sel) + 1) % visible().length]); });
$('shuffle').addEventListener('click', () => { RP.setShuffle(!RP.getShuffle()); mark(); });
document.querySelectorAll('.src-btn').forEach(b => b.addEventListener('click', () => {
  RP.setSource(b.dataset.src);
  if (!RP.current()) RP.prepare(SONGS, sel, 0);
  mark();
}));

// Deep link from the homepage: listen/#v=VIDEO_ID selects that song (a tap starts the sound).
const hv = (location.hash.match(/^#v=([\w-]{11})$/) || [])[1];
if (hv && byId.has(hv) && !(RP.current() && RP.current().id === hv)) {
  sel = byId.get(hv);
  if (RP.current()) RP.play(SONGS, sel); else RP.prepare(SONGS, sel, 0);
  setTimeout(() => items[sel].scrollIntoView({ block: 'center' }), 300);
} else if (!RP.current()) {
  RP.prepare(SONGS, 0, 0);
} else if (RP._resumeAt != null) {
  const c = RP.current(); RP.prepare(RP.queueIds().map(id => SONGS[byId.get(id)] || c), RP.queueIds().indexOf(c.id), RP._resumeAt); RP._resumeAt = null;
}

const q = $('q'); let filt = null;
function apply() {
  const t = q.value.trim().toLowerCase(); let n = 0;
  items.forEach(li => {
    const ok = (!filt || (filt === 'film' ? li.dataset.film === '1' : li.dataset.lang === filt)) && (!t || li.dataset.q.includes(t));
    li.hidden = !ok; if (ok) n++;
  });
  $('count').textContent = n === items.length ? n + ' songs' : n + ' of ' + items.length + ' songs';
  $('empty').hidden = n > 0;
}
q.addEventListener('input', apply);
document.querySelectorAll('.filter').forEach(b => b.addEventListener('click', () => {
  const on = b.getAttribute('aria-pressed') === 'true';
  document.querySelectorAll('.filter').forEach(x => x.setAttribute('aria-pressed', 'false'));
  if (!on) { b.setAttribute('aria-pressed', 'true'); filt = b.dataset.f; } else filt = null;
  apply();
}));

// Phones: once the player is pinned at the top, hide the button row to give the list more room.
const grid = document.querySelector('.listen-grid'), pcol = document.querySelector('.player-col');
const small = matchMedia('(max-width: 900px)');
let raf = 0;
function stuck() { raf = 0; pcol.classList.toggle('stuck', small.matches && grid.getBoundingClientRect().top < -8); }
const onScroll = () => { if (!raf) raf = requestAnimationFrame(stuck); };
addEventListener('scroll', onScroll, { passive: true });
small.addEventListener('change', stuck);

RP.dock($('dock'));
const offChange = RP.on('change', mark), offState = RP.on('state', mark);
RP.onLeave(() => { offChange(); offState(); removeEventListener('scroll', onScroll); small.removeEventListener('change', stuck); });
stuck();
mark();
