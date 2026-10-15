"""Build docs/listen/index.html from research_notes/Ramu discography/youtube_verified.json.

Usage: python3 tools/build_listen.py "research_notes/Ramu discography" docs/listen/index.html
Only songs whose YouTube credits name Ramu on an album from his verified discography are included
(see tools/ytlist.py, ytverify.py, ytfilter.py).
"""
import json, re, sys, html

D, OUT = sys.argv[1], sys.argv[2]
v = json.load(open(D + '/youtube_verified.json'))
cat = json.load(open(D + '/merged_catalogue.json'))
E = lambda s: html.escape(s or '', quote=True)
norm = lambda t: re.sub(r'[^a-z0-9]', '', re.sub(r'\(.*?\)', '', (t or '').lower()))


def disp(t):
    t = re.sub(r'\s+', ' ', t or '').strip()
    if t.upper() == t and re.search('[A-Z]', t):
        t = ' '.join(w.capitalize() for w in t.lower().split(' '))
    return t


album_lang = {}
for r in cat['releases']:
    album_lang.setdefault(norm(r['title']), r.get('language'))

FILMS = {
    'hmX3KFm-1D0': ('Kevvu Keka (comedy version)', 'Attarintiki Daredi', 2013, 'telugu'),
    '--A2Zm54T2U': ('Dabbu', 'Partner (Telugu)', 2023, 'telugu'),
    'oCViKY8ItSA': ('Idam Maarum Nerame (Reprise)', 'Kasthuri Veedu', 2026, 'tamil'),
}

songs, seen = [], set()
for x in v:
    m = x['meta']
    if x['id'] in FILMS:
        t, a, y, lang = FILMS[x['id']]
        songs.append({'id': x['id'], 'title': t, 'album': a, 'year': y, 'lang': lang, 'film': True, 'secs': x['p'].get('secs') or 0})
        continue
    key = (norm(x['title']), norm(m['album']))
    if key in seen:
        continue
    seen.add(key)
    songs.append({'id': x['id'], 'title': disp(x['title']), 'album': disp(m['album']), 'year': m.get('year'),
                  'lang': album_lang.get(norm(m['album'])) or 'other', 'film': False, 'secs': x['p'].get('secs') or 0})

films = sorted([s for s in songs if s['film']], key=lambda s: s['year'])
rest = sorted([s for s in songs if not s['film']], key=lambda s: (-(s['year'] or 0), s['album'].lower(), s['title'].lower()))
songs = films + rest
LANG = {'telugu': 'Telugu', 'tamil': 'Tamil', 'kannada': 'Kannada', 'sanskrit': 'Sanskrit', 'other': ''}
counts = {k: sum(1 for s in songs if s['lang'] == k) for k in LANG}


def dur(s):
    return f"{s // 60}:{s % 60:02d}" if s else ''


rows = []
for i, s in enumerate(songs):
    meta = ' · '.join(x for x in [('Film: ' if s['film'] else '') + s['album'], LANG.get(s['lang'], ''), str(s['year'] or '')] if x)
    rows.append(
        f'<li class="song" data-i="{i}" data-id="{s["id"]}" data-lang="{s["lang"]}" data-film="{1 if s["film"] else 0}" '
        f'data-q="{E((s["title"] + " " + s["album"]).lower())}"><button type="button" class="song-btn">'
        f'<span class="num">{i + 1}</span><span class="st">{E(s["title"])}</span><span class="sm">{E(meta)}</span>'
        f'<span class="sd">{dur(s["secs"])}</span></button></li>')

filters = '<button type="button" class="filter" data-f="film" aria-pressed="false">Film songs <span>{}</span></button>'.format(len(films))
filters += ''.join(f'<button type="button" class="filter" data-f="{k}" aria-pressed="false">{n} <span>{counts[k]}</span></button>'
                   for k, n in LANG.items() if k != 'other' and counts[k])

ld = {"@context": "https://schema.org", "@graph": [
    {"@type": "WebPage", "url": "https://kvsista.github.io/ramu-maharajapuram/listen/", "name": "Listen to Ramu Maharajapuram",
     "isPartOf": {"@id": "https://kvsista.github.io/ramu-maharajapuram/#website"}, "about": {"@id": "https://kvsista.github.io/ramu-maharajapuram/#ramu"}},
    {"@type": "MusicPlaylist", "name": "Ramu Maharajapuram: songs", "numTracks": len(songs),
     "track": [{"@type": "MusicRecording", "name": s['title'], "inAlbum": {"@type": "MusicAlbum", "name": s['album']},
                "byArtist": {"@id": "https://kvsista.github.io/ramu-maharajapuram/#ramu"},
                "url": f"https://www.youtube.com/watch?v={s['id']}"} for s in songs[:60]]},
    {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Ramu Maharajapuram", "item": "https://kvsista.github.io/ramu-maharajapuram/"},
        {"@type": "ListItem", "position": 2, "name": "Listen", "item": "https://kvsista.github.io/ramu-maharajapuram/listen/"}]}]}

data = json.dumps([{'id': s['id'], 't': s['title'], 'a': ('Film: ' if s['film'] else '') + s['album'] + (f" · {s['year']}" if s['year'] else '')} for s in songs], ensure_ascii=False)

page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Listen · Ramu Maharajapuram (SPB Ramu) · {len(songs)} Songs</title>
<meta name="description" content="Listen to {len(songs)} songs by singer Ramu Maharajapuram (SPB Ramu), right here: film songs from Attarintiki Daredi, Partner and Kasthuri Veedu, and devotional songs in Telugu, Tamil, Kannada and Sanskrit.">
<link rel="canonical" href="https://kvsista.github.io/ramu-maharajapuram/listen/">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta property="og:title" content="Listen · Ramu Maharajapuram (SPB Ramu)">
<meta property="og:description" content="{len(songs)} songs, playable right on the page.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://kvsista.github.io/ramu-maharajapuram/listen/">
<meta property="og:site_name" content="Ramu Maharajapuram">
<meta property="og:image" content="https://kvsista.github.io/ramu-maharajapuram/media/stage-closeup-kurta.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#11101a">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%2311101a'/%3E%3Ctext x='32' y='43' font-family='Georgia,serif' font-size='30' text-anchor='middle' fill='%23d2a95e'%3ERM%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;1,9..144,400&family=Manrope:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../site.css">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body class="listen-page">

<header class="bar">
  <div class="wrap bar-inner">
    <a class="mark" href="../">Ramu Maharajapuram</a>
    <nav class="tabs" aria-label="Main">
      <a href="../">Home</a>
      <a href="../life-story/">Story</a>
      <a href="../listen/" aria-current="page">Listen</a>
      <a href="../music/">Music</a>
      <a href="../watch/">Watch</a>
      <a href="../press/">Press</a>
    </nav>
    <a class="btn primary small invite-btn" href="../invite/">Invite</a>
  </div>
</header>

<main>
  <section class="page-head">
    <div class="wrap">
      <p class="label">Listen</p>
      <h1>Hear Ramu <em>sing</em></h1>
      <p class="lead">{len(songs)} songs, from his film work to his devotional albums. Choose a song and it plays here; the next one follows automatically.</p>
    </div>
  </section>

  <section class="listen" style="padding-top:24px">
    <div class="wrap listen-grid">
      <div class="player-col">
        <div class="player-card">
          <div class="player-frame"><div id="yt"></div><button type="button" class="player-start" id="start" aria-label="Play the first song"><span class="big-play"></span><span>Play</span></button></div>
          <div class="now">
            <p class="now-label">Now playing</p>
            <p class="now-title" id="now-title">{E(songs[0]['title'])}</p>
            <p class="now-album" id="now-album">{E(('Film: ' if songs[0]['film'] else '') + songs[0]['album'])}</p>
          </div>
          <div class="controls">
            <button type="button" class="ctl" id="prev" aria-label="Previous song"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="5" width="2.6" height="14" rx="1"/><path d="M19 5.8v12.4a1 1 0 0 1-1.55.83L9.2 13.2a1.45 1.45 0 0 1 0-2.4l8.25-5.85A1 1 0 0 1 19 5.8z"/></svg></button>
            <button type="button" class="ctl main" id="toggle" aria-label="Play"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.4v13.2a1.1 1.1 0 0 0 1.7.92l10.1-6.6a1.1 1.1 0 0 0 0-1.84L9.7 4.48A1.1 1.1 0 0 0 8 5.4z"/></svg></button>
            <button type="button" class="ctl" id="next" aria-label="Next song"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="16.4" y="5" width="2.6" height="14" rx="1"/><path d="M5 5.8v12.4a1 1 0 0 0 1.55.83l8.25-5.83a1.45 1.45 0 0 0 0-2.4L6.55 4.97A1 1 0 0 0 5 5.8z"/></svg></button>
            <button type="button" class="ctl small" id="shuffle" aria-pressed="false" aria-label="Shuffle">Shuffle</button>
          </div>
        </div>
        <p class="yt-note">Songs play from the official YouTube releases by his record labels.</p>
      </div>
      <div class="list-col">
        <div class="toolbar" style="margin-top:0">
          <label class="search"><span class="sr">Search songs</span><input type="search" id="q" placeholder="Search a song or album" autocomplete="off"></label>
        </div>
        <div class="filters" role="group" aria-label="Filter songs" style="margin-top:12px">{filters}</div>
        <p class="count" id="count" aria-live="polite">{len(songs)} songs</p>
        <ol class="songs" id="songs">
{chr(10).join(rows)}
        </ol>
        <p class="empty" id="empty" hidden>No songs match. Try another word or clear the filter.</p>
      </div>
    </div>
  </section>
</main>

<footer>
  <div class="wrap">
    <span>© <span id="yr">2026</span> Ramu Maharajapuram</span>
    <span><a href="mailto:ramusinger@gmail.com">ramusinger@gmail.com</a> · <a href="tel:+919841038926">+91 98410 38926</a></span>
    <span><a href="../">Home</a> · <a href="../life-story/">Story</a> · <a href="../music/">Music</a> · <a href="../watch/">Watch</a> · <a href="../press/">Press</a> · <a href="../invite/">Invite</a></span>
    <span class="disamb">Ramu Maharajapuram, “SPB Ramu”, playback and concert singer. Not to be confused with the Carnatic vocalist Maharajapuram S. Ramachandran.</span>
  </div>
</footer>

<script>
document.getElementById('yr').textContent = new Date().getFullYear();
const SONGS = {data};
const ICON_PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.4v13.2a1.1 1.1 0 0 0 1.7.92l10.1-6.6a1.1 1.1 0 0 0 0-1.84L9.7 4.48A1.1 1.1 0 0 0 8 5.4z"/></svg>', ICON_PAUSE = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6.5" y="5" width="4" height="14" rx="1.2"/><rect x="13.5" y="5" width="4" height="14" rx="1.2"/></svg>';
const items = [...document.querySelectorAll('.song')];
let cur = 0, player = null, ready = false, wantPlay = false, shuffle = false;
const $ = (id) => document.getElementById(id);
function visible() {{ return items.filter(li => !li.hidden).map(li => +li.dataset.i); }}
function mark() {{
  items.forEach(li => li.classList.toggle('playing', +li.dataset.i === cur));
  $('now-title').textContent = SONGS[cur].t; $('now-album').textContent = SONGS[cur].a;
}}
function play(i) {{
  cur = i; mark(); $('start').hidden = true;
  if (ready) player.loadVideoById(SONGS[i].id); else wantPlay = true;
}}
function step(d) {{
  const v = visible(); if (!v.length) return;
  if (shuffle) {{ play(v[Math.floor(Math.random() * v.length)]); return; }}
  const p = v.indexOf(cur); play(v[(p + d + v.length) % v.length]);
}}
window.onYouTubeIframeAPIReady = function () {{
  player = new YT.Player('yt', {{
    host: 'https://www.youtube-nocookie.com', videoId: SONGS[cur].id,
    playerVars: {{ playsinline: 1, rel: 0, modestbranding: 1 }},
    events: {{
      onReady: () => {{ ready = true; if (wantPlay) player.loadVideoById(SONGS[cur].id); }},
      onStateChange: (e) => {{
        if (e.data === YT.PlayerState.ENDED) step(1);
        const playing = e.data === YT.PlayerState.PLAYING;
        $('toggle').innerHTML = playing ? ICON_PAUSE : ICON_PLAY; $('toggle').setAttribute('aria-label', playing ? 'Pause' : 'Play');
        if (playing) $('start').hidden = true;
      }},
      onError: () => step(1)
    }}
  }});
}};
const s = document.createElement('script'); s.src = 'https://www.youtube.com/iframe_api'; document.head.appendChild(s);
items.forEach(li => li.querySelector('button').addEventListener('click', () => play(+li.dataset.i)));
$('start').addEventListener('click', () => play(cur));
// Deep link from the homepage: listen/#v=VIDEO_ID selects that song (browsers need a tap to start sound).
const hv = (location.hash.match(/^#v=([\\w-]{{11}})$/) || [])[1];
if (hv) {{
  const i = SONGS.findIndex(s => s.id === hv);
  if (i >= 0) {{ cur = i; const li = items[i]; setTimeout(() => li.scrollIntoView({{ block: 'center' }}), 300); }}
}}
$('toggle').addEventListener('click', () => {{
  if (!ready) {{ play(cur); return; }}
  const st = player.getPlayerState();
  if (st === YT.PlayerState.PLAYING) player.pauseVideo();
  else if (st === YT.PlayerState.PAUSED) player.playVideo();
  else play(cur);
}});
$('next').addEventListener('click', () => step(1));
$('prev').addEventListener('click', () => step(-1));
$('shuffle').addEventListener('click', (e) => {{ shuffle = !shuffle; e.currentTarget.setAttribute('aria-pressed', shuffle); }});
const q = $('q'); let filt = null;
function apply() {{
  const t = q.value.trim().toLowerCase(); let n = 0;
  items.forEach(li => {{
    const ok = (!filt || (filt === 'film' ? li.dataset.film === '1' : li.dataset.lang === filt)) && (!t || li.dataset.q.includes(t));
    li.hidden = !ok; if (ok) n++;
  }});
  $('count').textContent = n === items.length ? n + ' songs' : n + ' of ' + items.length + ' songs';
  $('empty').hidden = n > 0;
}}
q.addEventListener('input', apply);
document.querySelectorAll('.filter').forEach(b => b.addEventListener('click', () => {{
  const on = b.getAttribute('aria-pressed') === 'true';
  document.querySelectorAll('.filter').forEach(x => x.setAttribute('aria-pressed', 'false'));
  if (!on) {{ b.setAttribute('aria-pressed', 'true'); filt = b.dataset.f; }} else filt = null;
  apply();
}}));
mark();
</script>
</body>
</html>
'''
open(OUT, 'w').write(page)
print(len(songs), 'songs', len(films), 'films', counts, len(page) // 1024, 'KB')
