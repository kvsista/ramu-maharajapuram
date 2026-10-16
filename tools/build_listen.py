"""Build docs/listen/index.html from research_notes/Ramu discography/youtube_verified.json.

Usage: python3 tools/build_listen.py "research_notes/Ramu discography" docs/listen/index.html
Only songs whose YouTube credits name Ramu on an album from his verified discography are included
(see tools/ytlist.py, ytverify.py, ytfilter.py).
"""
import json, os, re, sys, html

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

import urllib.parse
track_links = {}
for r in cat['releases']:
    for t in r['tracks']:
        track_links[(norm(r['title']), norm(t['title']))] = (t.get('links') or {}, r.get('links') or {})
        alnum = lambda x: re.sub(r'[^a-z0-9]', '', (x or '').lower())
        track_links.setdefault((norm(r['title']), alnum(t['title'])), (t.get('links') or {}, r.get('links') or {}))


def first(v):
    return v[0] if isinstance(v, list) else v


def app_links(vid, title, album):
    tl, al = track_links.get((norm(album), norm(title))) or track_links.get((norm(album), re.sub(r'[^a-z0-9]', '', title.lower())), ({}, {}))
    out = {}
    for key in ['spotify', 'apple', 'jiosaavn', 'deezer']:
        u = first(tl.get(key)) or first(al.get(key))
        if u:
            out[key] = u
    if 'spotify' not in out:
        out['spotify'] = 'https://open.spotify.com/search/' + urllib.parse.quote(f'{title} Maharajapuram Ramu')
    out['ytmusic'] = f'https://music.youtube.com/watch?v={vid}'
    return out


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
        songs.append({'id': x['id'], 'title': t, 'album': a, 'year': y, 'lang': lang, 'film': True, 'secs': x['p'].get('secs') or 0,
                      'links': app_links(x['id'], x['title'], m.get('album', ''))})
        continue
    key = (norm(x['title']), norm(m['album']))
    if key in seen:
        continue
    seen.add(key)
    songs.append({'id': x['id'], 'title': disp(x['title']), 'album': disp(m['album']), 'year': m.get('year'),
                  'lang': album_lang.get(norm(m['album'])) or 'other', 'film': False, 'secs': x['p'].get('secs') or 0,
                  'links': app_links(x['id'], x['title'], m['album'])})

DEITIES = [  # (key, label, keywords) — first match wins, so more specific names come first
    ('christian', 'Christian', r'yesu|yese|kaluvari|parisudda|yesayya|nithirai'),
    ('sai', 'Sai Baba', r'\bsai|shirdi|shiridi|sayee'),
    ('ayyappa', 'Ayyappa', r'ayyapp|harivarasanam|manikant|sabari|shabari|sastha|harihara|hari hara|swamiye|bhagavan saranam|irumurthy|bhoothanatha|bhuthanatha'),
    ('hanuman', 'Hanuman', r'hanuman|gandi kshethr|anjaney|anjineya|maruthi|maaruthi|vayu kumara'),
    ('narasimha', 'Narasimha', r'narasim'),
    ('guru', 'Gurus & saints', r'raghavendra|guru|alangudi|dhakshina|brahmayya|bramayya|pothulurayya|paramathma'),
    ('ganesha', 'Ganesha', r'vinayak|vinayag|ganapath|gananat|gananad|ganesh|kanipakam|ekadhant|yekadhant|gajamukha|pillaiyaar|dandanayaka|ganamgal'),
    ('murugan', 'Murugan', r'murug|subraman|subrahman|\bvel\b|velaiya|aarupadai|naayagare'),
    ('surya', 'Surya', r'surya|aadhavane|adithya|bhaskara'),
    ('shiva', 'Shiva', r'shiv|\bsiv|eshwara|eswara|shankara|mahadeva|arunachala|annamalai|linga|neelakanta|kailasa|bhairava|bairava|malleshwara|mylara|harane|kasi|param porul|omkara roopame|omkaara'),
    ('devi', 'Devi', r'amma|durga|amman|ambig|ambika|shakthi|shakti|sakthi|rajarajeswari|meenakshi|lakshmi|vaarahi|abirami|karumari|mahishasura|chowdeswari|navarathri|vaaniye|vengamamba'),
    ('rama', 'Rama & Krishna', r'\brama|\bram\b|ramuni|raghurama|krishna|gopal|gopika|nandha kumara|brindhavan|ramayya'),
    ('vishnu', 'Venkateswara & Vishnu', r'venkat|venakt|srinivas|tirumala|govind|perumal|narayana|vishnu|sapthagiri|varaha|madhavan|thiruppaavai'),
]


def deity(s):
    hay = (s['title'] + ' ' + s['album']).lower()
    return next((k for k, _, rx in DEITIES if re.search(rx, hay)), 'other')


for s in songs:
    s['cat'] = 'film' if s['film'] else 'dev'
    s['deity'] = '' if s['film'] else deity(s)
    s['note'] = ''

# Live and TV performances, verified one by one (see data/live_performances.json).
live_path = os.path.join(D, 'live_performances.json')
live = json.load(open(live_path)) if os.path.exists(live_path) else []
for x in live:
    songs.append({'id': x['id'], 'title': x['song'], 'album': x['film'] or '', 'year': x.get('year'), 'lang': x['lang'], 'film': False,
                  'secs': x.get('secs') or 0, 'cat': 'spb' if x.get('spb') else 'stage', 'deity': '',
                  'venue': x['venue'], 'note': x.get('note', ''),
                  'links': {'ytmusic': f"https://music.youtube.com/watch?v={x['id']}"}})

ORDER = ['spb', 'film', 'stage', 'dev']
CATS = {'spb': 'Songs of SPB', 'film': 'His film songs', 'stage': 'More on stage & TV', 'dev': 'Devotional'}
abc = lambda s: (re.sub(r'[^a-z0-9 ]', '', s['title'].lower()).strip(), s['album'].lower(), -(s['year'] or 0))
songs = [s for c in ORDER for s in sorted((x for x in songs if x['cat'] == c), key=abc)]  # A to Z within each category
LANG = {'telugu': 'Telugu', 'tamil': 'Tamil', 'kannada': 'Kannada', 'sanskrit': 'Sanskrit', 'hindi': 'Hindi', 'other': ''}
counts = {k: sum(1 for s in songs if s['lang'] == k) for k in LANG}
ccount = {c: sum(1 for s in songs if s['cat'] == c) for c in ORDER}
dcount = {k: sum(1 for s in songs if s['deity'] == k) for k, _, _ in DEITIES}


def dur(s):
    return f"{s // 60}:{s % 60:02d}" if s else ''


def album_line(s):
    if s['cat'] in ('spb', 'stage'):
        return ' · '.join(x for x in [s['album'], s['venue']] if x)
    return ('Film: ' if s['film'] else '') + s['album'] + (f" · {s['year']}" if s['year'] else '')


rows = []
for i, s in enumerate(songs):
    if s['cat'] in ('spb', 'stage'):
        meta = ' · '.join(x for x in [s['album'], LANG.get(s['lang'], ''), s['venue'], s['note']] if x)
    else:
        meta = ' · '.join(x for x in [('Film: ' if s['film'] else '') + s['album'], LANG.get(s['lang'], ''), str(s['year'] or '')] if x)
    rows.append(
        f'<li class="song" data-i="{i}" data-id="{s["id"]}" data-lang="{s["lang"]}" data-cat="{s["cat"]}" data-deity="{s["deity"]}" '
        f'data-q="{E((s["title"] + " " + s["album"] + " " + s.get("venue", "") + " " + s["note"]).lower())}"><button type="button" class="song-btn">'
        f'<span class="num">{i + 1}</span><span class="st">{E(s["title"])}</span><span class="sm">{E(meta)}</span>'
        f'<span class="sd">{dur(s["secs"])}</span></button></li>')

cats = ''.join(f'<button type="button" class="cat" role="tab" data-c="{c}" aria-selected="{str(c == ORDER[0]).lower()}">{CATS[c]} <span>{ccount[c]}</span></button>'
               for c in ORDER if ccount[c])
cats += f'<button type="button" class="cat" role="tab" data-c="all" aria-selected="false">All <span>{len(songs)}</span></button>'
filters = ''.join(f'<button type="button" class="filter" data-f="{k}" aria-pressed="false">{n} <span>{counts[k]}</span></button>'
                  for k, n in LANG.items() if k != 'other' and counts[k])
deities = ''.join(f'<button type="button" class="filter" data-d="{k}" aria-pressed="false">{n} <span>{dcount[k]}</span></button>'
                  for k, n, _ in sorted(DEITIES, key=lambda d: -dcount[d[0]]) if dcount[k])
if any(s['deity'] == 'other' for s in songs):
    deities += f'<button type="button" class="filter" data-d="other" aria-pressed="false">More <span>{sum(1 for s in songs if s["deity"] == "other")}</span></button>'

ld = {"@context": "https://schema.org", "@graph": [
    {"@type": "WebPage", "url": "https://ramumaharajapuram.com/listen/", "name": "Listen to Ramu Maharajapuram",
     "isPartOf": {"@id": "https://ramumaharajapuram.com/#website"}, "about": {"@id": "https://ramumaharajapuram.com/#ramu"}},
    {"@type": "MusicPlaylist", "name": "Ramu Maharajapuram: songs", "numTracks": len(songs),
     "track": [{"@type": "MusicRecording", "name": s['title'], "inAlbum": {"@type": "MusicAlbum", "name": s['album']},
                "byArtist": {"@id": "https://ramumaharajapuram.com/#ramu"},
                "url": f"https://www.youtube.com/watch?v={s['id']}"} for s in songs[:60]]},
    {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Ramu Maharajapuram", "item": "https://ramumaharajapuram.com/"},
        {"@type": "ListItem", "position": 2, "name": "Listen", "item": "https://ramumaharajapuram.com/listen/"}]}]}

data = json.dumps([{'id': s['id'], 't': s['title'], 'a': album_line(s), 'l': s['links']} for s in songs], ensure_ascii=False)

listen_js = open(os.path.join(os.path.dirname(__file__), 'listen_page.js')).read().replace('__SONGS__', data)

page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Listen · Ramu Maharajapuram (SPB Ramu) · {len(songs)} Songs</title>
<meta name="description" content="Listen to {len(songs)} songs by singer Ramu Maharajapuram (SPB Ramu), right here: {ccount['spb']} songs of S. P. Balasubrahmanyam sung live and on TV, film songs from Attarintiki Daredi, Partner and Kasthuri Veedu, and devotional songs in Telugu, Tamil, Kannada and Sanskrit.">
<link rel="canonical" href="https://ramumaharajapuram.com/listen/">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta property="og:title" content="Listen · Ramu Maharajapuram (SPB Ramu)">
<meta property="og:description" content="{len(songs)} songs, playable right on the page.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://ramumaharajapuram.com/listen/">
<meta property="og:site_name" content="Ramu Maharajapuram">
<meta property="og:image" content="https://ramumaharajapuram.com/media/stage-closeup-kurta.jpg">
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
      <p class="lead">{len(songs)} songs: the songs of S.&nbsp;P.&nbsp;Balasubrahmanyam as Ramu sings them on stage and on TV, his own film songs, and his devotional albums. Choose a song and it plays here; the next one follows automatically.</p>
    </div>
  </section>

  <section class="listen" style="padding-top:24px">
    <div class="wrap listen-grid">
      <div class="player-col">
        <div class="player-tools">
          <div class="apps" id="apps" aria-label="Open this song in a music app"></div>
          <div class="src" role="group" aria-label="Play on"><span class="apps-label">Play on</span><button type="button" class="src-btn" data-src="yt" aria-pressed="true">YouTube</button><button type="button" class="src-btn" data-src="apple" aria-pressed="false">Apple Music</button><button type="button" class="src-btn" data-src="spotify" aria-pressed="false">Spotify</button><button type="button" class="src-btn" data-src="deezer" aria-pressed="false">Deezer</button></div>
          <p class="src-note" id="src-note" hidden></p>
        </div>
        <div class="player-card">
          <div class="player-frame" id="dock"><button type="button" class="player-start" id="start" aria-label="Play"><span class="big-play"></span><span>Play</span></button></div>
          <div class="now now-row">
            <div class="now-text">
            <p class="now-title" id="now-title">{E(songs[0]['title'])}</p>
            <p class="now-album" id="now-album">{E(album_line(songs[0]))}</p>
            </div>
            <div class="now-actions">
              <button type="button" class="icon-btn" id="shuffle" aria-pressed="false" aria-label="Shuffle" title="Shuffle"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17 3.5 21.5 8 17 12.5V9.5h-2.2c-1.1 0-2.1.5-2.8 1.4l-4.6 6.2c-1.1 1.4-2.8 2.3-4.6 2.3H1.5v-3h1.3c.9 0 1.7-.4 2.2-1.1l4.6-6.2C10.8 7.4 12.7 6.5 14.8 6.5H17V3.5zm0 8 4.5 4.5L17 20.5v-3h-2.2c-1.6 0-3.1-.6-4.2-1.6l1.9-2.5c.6.7 1.4 1.1 2.3 1.1H17v-3zM1.5 6.5h1.3c1.6 0 3.1.6 4.2 1.6L5.1 10.6c-.6-.7-1.4-1.1-2.3-1.1H1.5v-3z"/></svg></button>
              <button type="button" class="icon-btn" id="next" aria-label="Next song" title="Next song"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="16.4" y="5" width="2.6" height="14" rx="1"/><path d="M5 5.8v12.4a1 1 0 0 0 1.55.83l8.25-5.83a1.45 1.45 0 0 0 0-2.4L6.55 4.97A1 1 0 0 0 5 5.8z"/></svg></button>
            </div>
          </div>
        </div>
        <p class="yt-note">Album songs play from his record labels' official YouTube releases; stage and TV performances from the organisers' and channels' own uploads.</p>
      </div>
      <div class="list-col">
        <div class="cats" role="tablist" aria-label="Categories">{cats}</div>
        <div class="toolbar" style="margin-top:14px">
          <label class="search"><span class="sr">Search songs</span><input type="search" id="q" placeholder="Search a song, film or album" autocomplete="off"></label>
        </div>
        <div class="filters" role="group" aria-label="Language" style="margin-top:12px">{filters}</div>
        <div class="filters deities" id="deities" role="group" aria-label="Devotional songs by deity" style="margin-top:8px" hidden>{deities}</div>
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
    <span><a href="mailto:ramusinger@gmail.com">ramusinger@gmail.com</a> · <a href="../invite/">Invite Ramu</a></span>
    <span><a href="../">Home</a> · <a href="../life-story/">Story</a> · <a href="../music/">Music</a> · <a href="../watch/">Watch</a> · <a href="../press/">Press</a> · <a href="../invite/">Invite</a></span>
    <span class="disamb">Ramu Maharajapuram, “SPB Ramu”, playback and concert singer. Not to be confused with the Carnatic vocalist Maharajapuram S. Ramachandran.</span>
  </div>
</footer>

<script src="../app.js"></script>
<script>
{listen_js}
</script>
</body>
</html>
'''
open(OUT, 'w').write(page)
print(len(songs), 'songs', ccount, counts, len(page) // 1024, 'KB')
