"""Write the homepage "What's new" strip: his newest songs, posts and news in one row, newest first.

Usage: python3 tools/build_home_new.py data docs/index.html
Sources: data/youtube_verified.json (new label releases), data/social.json (Instagram / Facebook posts,
kept fresh daily) and data/news.json (posts picked as news in the weekly review).
Fills <!-- WHATSNEW:START --> … <!-- WHATSNEW:END -->. Instagram posts open Instagram's own player in a pop-up.
Also adds his Facebook and Instagram addresses to the homepage's structured data (sameAs).
"""
import datetime, html, json, os, re, sys
from social_ui import player

D, PAGE = sys.argv[1], sys.argv[2]
E = lambda s: html.escape(s or '', quote=True)
load = lambda n, d: json.load(open(os.path.join(D, n))) if os.path.exists(os.path.join(D, n)) else d
SHOW = 6


def disp(t):
    t = re.sub(r'\s+', ' ', t or '').strip()
    return ' '.join(w.capitalize() for w in t.lower().split(' ')) if t.upper() == t and re.search('[A-Z]', t) else t


def snippet(text, n=90):
    t = ' '.join(re.sub(r'[#@][\w.]+', '', text or '').split())
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0] + '…'


items = []

# New songs from his labels: one per album so a batch release doesn't fill the row.
albums = set()
rel = lambda x: (x.get('meta') or {}).get('date') or (re.search(r'Released on: (\d{4}-\d{2}-\d{2})', (x.get('p') or {}).get('desc', '')) or [None, ''])[1]
for x in sorted(load('youtube_verified.json', []), key=rel, reverse=True):
    d = rel(x)
    album = re.sub(r'\s*\((?:original )?motion picture soundtrack\)', '', disp((x.get('meta') or {}).get('album') or ''), flags=re.I)
    if not d or x['id'] == 'hmX3KFm-1D0' or album.lower() in albums:
        continue
    albums.add(album.lower())
    items.append({'kind': 'Song', 'date': d, 'title': disp(x['title']), 'meta': album, 'href': f'listen/#v={x["id"]}',
                  'img': f'https://i.ytimg.com/vi/{x["id"]}/hqdefault.jpg', 'play': True})
    if len(albums) == SHOW:
        break

# News picked in the weekly review: shown instead of the post it came from.
news = load('news.json', [])
news_links = {n['link'] for n in news}
for n in news:
    items.append({'kind': 'News', 'date': n['date'], 'title': n['title'], 'meta': '', 'href': n['link'],
                  'img': n.get('photo', ''), 'ext': True, 'embed': n['link'].rstrip('/') + '/embed/' if 'instagram.com' in n['link'] else ''})

social = load('social.json', {'items': []})
for p in social.get('items', []):
    if p['link'] in news_links:
        continue
    where = 'Instagram' if p['src'] == 'instagram' else 'Facebook'
    video = p.get('video') or re.search(r'/(reel|videos?)/', p['link'])
    items.append({'kind': 'Post', 'date': p['time'][:10], 'title': snippet(p['text']) or ('A video on ' if video else 'A photo on ') + where,
                  'meta': where, 'href': p['link'], 'img': p.get('photo') or '', 'play': bool(video), 'ext': True,
                  'embed': p['link'].rstrip('/') + '/embed/' if p['src'] == 'instagram' else ''})

items.sort(key=lambda i: i['date'], reverse=True)
items = items[:SHOW]


def card(i):
    d = datetime.date.fromisoformat(i['date']).strftime('%-d %b %Y')
    meta = ' · '.join(x for x in [i['meta'], d] if x)
    attrs = (' target="_blank" rel="noopener"' if i.get('ext') else '') + (f' data-embed="{E(i["embed"])}" data-where="{E(i["meta"] or "Instagram")}"' if i.get('embed') else '')
    style = ' style="background-image:url(' + E(i['img']) + ')"' if i['img'] else ''
    thumb = f'<span class="new-thumb"{style}>'
    thumb += f'<span class="new-kind">{i["kind"]}</span>' + ('<span class="latest-play"></span>' if i.get('play') else '') + '</span>'
    return f'<a class="new-card" href="{E(i["href"])}"{attrs}>{thumb}<span class="new-title">{E(i["title"])}</span><span class="new-meta">{E(meta)}</span></a>'


follow = ''.join(f'<a class="btn quiet small" href="{E(u)}" target="_blank" rel="noopener">{n} ↗</a>'
                 for n, u in [('Instagram', social.get('instagram')), ('Facebook', social.get('facebook'))] if u)
block = f'''<!-- WHATSNEW:START -->
  <section class="whatsnew">
    <div class="wrap">
      <div class="latest-head">
        <div><p class="label">What’s new</p><h2>Latest from <em>Ramu</em></h2></div>
        <div class="social-follow"><a class="btn quiet small" href="listen/">All songs →</a>{follow}</div>
      </div>
      <div class="new-grid">
        {"".join(card(i) for i in items)}
      </div>
    </div>
{player('.new-card')}  </section>
  <!-- WHATSNEW:END -->'''

s = open(PAGE).read()
if '<!-- WHATSNEW:START -->' not in s:
    sys.exit('markers missing in ' + PAGE)
s = re.sub(r'<!-- WHATSNEW:START -->.*?<!-- WHATSNEW:END -->', lambda m: block, s, flags=re.S)
for u in [social.get('facebook'), social.get('instagram')]:
    if u and u not in s:
        s = re.sub(r'("sameAs": \[)', lambda m: m.group(1) + f'\n        "{u}",', s, count=1)
open(PAGE, 'w').write(s)
print('build_home_new:', ', '.join(f"{i['kind']} {i['date']}" for i in items))
