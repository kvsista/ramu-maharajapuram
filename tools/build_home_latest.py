"""Rebuild the "Latest releases" strip on the homepage from data/youtube_verified.json.

Usage: python3 tools/build_home_latest.py data docs/index.html
Replaces everything between <!-- LATEST:START --> and <!-- LATEST:END --> in the homepage.
"""
import json, re, sys, html, datetime

D, PAGE = sys.argv[1], sys.argv[2]
E = lambda s: html.escape(s or '', quote=True)
v = json.load(open(D + '/youtube_verified.json'))


def disp(t):
    t = re.sub(r'\s+', ' ', t or '').strip()
    return ' '.join(w.capitalize() for w in t.lower().split(' ')) if t.upper() == t and re.search('[A-Z]', t) else t


def date_of(x):
    m = (x.get('meta') or {}).get('date') or (re.search(r'Released on: (\d{4}-\d{2}-\d{2})', x.get('p', {}).get('desc', '')) or [None, None])[1]
    return m


songs, seen_albums = [], set()
for x in v:
    d = date_of(x)
    if not d or x['id'] == 'hmX3KFm-1D0':
        continue
    album = (x.get('meta') or {}).get('album') or ''
    songs.append((d, x['id'], disp(x['title']), disp(album)))
songs.sort(reverse=True)

# one song per album so the strip shows variety
picked = []
for d, vid, title, album in songs:
    if album.lower() in seen_albums:
        continue
    seen_albums.add(album.lower())
    picked.append((d, vid, title, album))
    if len(picked) == 6:
        break


def nice(d):
    return datetime.date.fromisoformat(d).strftime('%-d %b %Y')


cards = ''.join(
    f'''        <a class="latest-card" href="listen/#v={vid}">
          <span class="latest-thumb" style="background-image:url(https://i.ytimg.com/vi/{vid}/hqdefault.jpg)"><span class="latest-play"></span></span>
          <span class="latest-title">{E(title)}</span>
          <span class="latest-meta">{E(album)} · {nice(d)}</span>
        </a>
''' for d, vid, title, album in picked)

block = f'''<!-- LATEST:START -->
  <section class="latest">
    <div class="wrap">
      <div class="latest-head">
        <div><p class="label">New releases</p><h2>Latest <em>songs</em></h2></div>
        <a class="btn quiet small" href="listen/">All songs →</a>
      </div>
      <div class="latest-grid">
{cards}      </div>
    </div>
  </section>
  <!-- LATEST:END -->'''

page = open(PAGE).read()
if '<!-- LATEST:START -->' not in page:
    sys.exit('markers missing in ' + PAGE)
page = re.sub(r'<!-- LATEST:START -->.*?<!-- LATEST:END -->', lambda m: block, page, flags=re.S)
open(PAGE, 'w').write(page)
print('build_home_latest:', [p[2] for p in picked])
