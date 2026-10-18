document.getElementById('yr').textContent = new Date().getFullYear();
const SONGS = __SONGS__;
const ICON_PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.4v13.2a1.1 1.1 0 0 0 1.7.92l10.1-6.6a1.1 1.1 0 0 0 0-1.84L9.7 4.48A1.1 1.1 0 0 0 8 5.4z"/></svg>';
const ICON_PAUSE = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6.5" y="5" width="4" height="14" rx="1.2"/><rect x="13.5" y="5" width="4" height="14" rx="1.2"/></svg>';
const items = [...document.querySelectorAll('.song')];
const byId = new Map(SONGS.map((s, i) => [s.id, i]));
const $ = (id) => document.getElementById(id);
let sel = 0;  // song shown in the card when nothing is playing yet

// Songs that only play on YouTube itself (data-ext) open there and are left out of the queue.
function visible() { return [...$('songs').children].filter(li => !li.hidden && !li.dataset.ext).map(li => +li.dataset.i); }
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
items.forEach(li => { if (!li.dataset.ext) li.querySelector('button').addEventListener('click', () => playAt(+li.dataset.i)); });
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

const q = $('q'), langSel = $('lang'), dtySel = $('dty'); let cat = 'spb';
const LANGS = JSON.parse(langSel.dataset.langs);
const DTYS = [...dtySel.options].slice(1).map(o => [o.value, o.text.replace(/ \(\d+\)$/, '')]);
// Each dropdown counts what the list would show if you picked that option, given the other filters.
function fill(sel, all, opts, count) {
  const cur = sel.value; sel.replaceChildren(new Option(all, ''));
  opts.map(([k, name]) => [k, name, count(k)]).filter(([k, , n]) => n || k === cur).sort((a, b) => b[2] - a[2])
    .forEach(([k, name, n]) => sel.append(new Option(name + ' (' + n + ')', k)));
  sel.value = cur;
}
function apply() {
  const t = q.value.trim().toLowerCase(), filt = langSel.value, dty = cat === 'dev' ? dtySel.value : '';
  const base = items.filter(li => (cat === 'all' || li.dataset.cat === cat) && (!t || li.dataset.q.includes(t)));
  fill(langSel, 'All languages', LANGS, k => base.filter(li => li.dataset.lang === k && (!dty || li.dataset.deity === dty)).length);
  if (cat === 'dev') fill(dtySel, 'All deities', DTYS, k => base.filter(li => li.dataset.deity === k && (!filt || li.dataset.lang === filt)).length);
  let n = 0;
  [...$('songs').children].forEach(li => {
    const ok = base.includes(li) && (!filt || li.dataset.lang === filt) && (!dty || li.dataset.deity === dty);
    li.hidden = !ok; if (ok) li.querySelector('.num').textContent = ++n;  // number each filtered list from 1
  });
  $('count').textContent = n + (n === 1 ? ' song' : ' songs');
  $('empty').hidden = n > 0;
}
// The page lists each category A to Z in turn; "All" re-sorts the whole list A to Z.
const key = (li) => li.querySelector('.st').textContent.toLowerCase().replace(/[^a-z0-9 ]/g, '').trim();
const byCategory = items.slice(), byTitle = items.slice().sort((a, b) => key(a).localeCompare(key(b)));
// Albums: the discography panel, fetched the first time the tab is opened.
let albumsLoaded = false;
function showAlbums() {
  const panel = $('albums-panel');
  if (albumsLoaded) return;
  albumsLoaded = true;
  const url = new URL('listen/' + panel.dataset.src, document.querySelector('script[src*="app.js"]').src);
  fetch(url).then(r => r.text()).then(html => {
    panel.innerHTML = html;
    const rels = [...panel.querySelectorAll('.rel')], aq = $('aq'), al = $('alang');
    const filter = () => {
      const t = aq.value.trim().toLowerCase(), l = al.value; let n = 0;
      rels.forEach(r => { const ok = (!l || r.dataset.lang === l) && (!t || r.dataset.q.includes(t)); r.hidden = !ok; if (ok) n++; });
      $('acount').textContent = n + (n === 1 ? ' release' : ' releases');
      $('aempty').hidden = n > 0;
    };
    aq.addEventListener('input', filter); al.addEventListener('change', filter);
    // Play an album (or one song of it) in the site player; the rest of that album follows.
    panel.addEventListener('click', (e) => {
      const b = e.target.closest('.rel-play, .trk-play:not(.off)'); if (!b) return;
      e.preventDefault(); e.stopPropagation();
      const rel = b.closest('.rel'), ids = [...rel.querySelectorAll('li[data-id]')].map(li => li.dataset.id).filter(id => byId.has(id));
      if (!ids.length) return;
      const li = b.closest('li[data-id]'), start = li ? Math.max(0, ids.indexOf(li.dataset.id)) : 0;
      RP.play(ids.map(id => SONGS[byId.get(id)]), start);
      rel.open = true;
    });
    markAlbum();
  }).catch(() => { albumsLoaded = false; panel.innerHTML = '<p class="empty">Couldn\u2019t load the albums. Check your connection and tap Albums again.</p>'; });
}
function markAlbum() {
  const c = RP.current();
  document.querySelectorAll('#albums-panel li[data-id]').forEach(li => li.classList.toggle('playing', !!c && li.dataset.id === c.id));
}
function setCat(c) {
  const albums = c === 'albums';
  $('songs-panel').hidden = albums; $('albums-panel').hidden = !albums;
  document.querySelectorAll('.cat').forEach(b => b.setAttribute('aria-selected', String(b.dataset.c === c)));
  // Keep the chosen tab visible in the scrolling tab row (without moving the page).
  const row = document.querySelector('.cats'), tab = row.querySelector('[aria-selected="true"]');
  if (tab && (tab.offsetLeft < row.scrollLeft || tab.offsetLeft + tab.offsetWidth > row.scrollLeft + row.clientWidth)) row.scrollLeft = tab.offsetLeft - 16;
  if (albums) { cat = c; showAlbums(); return; }
  if ((c === 'all') !== (cat === 'all') || !setCat.done) { $('songs').append(...(c === 'all' ? byTitle : byCategory)); setCat.done = true; }
  cat = c; langSel.value = ''; dtySel.value = '';
  document.querySelectorAll('.cat').forEach(b => b.setAttribute('aria-selected', String(b.dataset.c === c)));
  $('dpick').hidden = c !== 'dev';
  apply();
}
q.addEventListener('input', apply);
langSel.addEventListener('change', apply);
dtySel.addEventListener('change', apply);
document.querySelectorAll('.cat').forEach(b => b.addEventListener('click', () => setCat(b.dataset.c)));
// Open on the category of the song that is playing (or deep-linked), else on Songs of SPB; #albums opens Albums.
{ const c = RP.current(), i = hv && byId.has(hv) ? byId.get(hv) : c && byId.has(c.id) ? byId.get(c.id) : null;
  setCat(location.hash === '#albums' && $('albums-panel') && document.querySelector('.cat[data-c=albums]') ? 'albums' : i != null ? items[i].dataset.cat : 'spb'); }

// Phones: once the player is pinned at the top, hide the button row to give the list more room.
const grid = document.querySelector('.listen-grid'), pcol = document.querySelector('.player-col');
const small = matchMedia('(max-width: 900px)');
let raf = 0;
function stuck() { raf = 0; pcol.classList.toggle('stuck', small.matches && grid.getBoundingClientRect().top < -8); }
const onScroll = () => { if (!raf) raf = requestAnimationFrame(stuck); };
addEventListener('scroll', onScroll, { passive: true });
small.addEventListener('change', stuck);

RP.dock($('dock'));
const offChange = RP.on('change', mark), offState = RP.on('state', mark), offAlbum = RP.on('change', markAlbum);
RP.onLeave(() => { offChange(); offState(); offAlbum(); removeEventListener('scroll', onScroll); small.removeEventListener('change', stuck); });
stuck();
mark();
