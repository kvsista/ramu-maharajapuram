"""Find new YouTube videos of Ramu, for a person to review.

Usage: python3 tools/discover_videos.py data > candidates.json
Searches YouTube by name and searches the channels he is known to perform on (live_util.TRUSTED).
Gopal Sapthaswaram videos name the film and original singers in their description, so those are
added to the Listen page straight away (data/live_performances.json). Everything else is printed
as a JSON list for the weekly review issue, and recorded in data/seen_videos.json so the same
video is never suggested twice. Official label releases are skipped (refresh_youtube.py handles them).
"""
import json, os, re, sys, glob, urllib.request, urllib.parse, time
from live_util import UA, TRUSTED, NOT_HIM, EMBED_BLOCKED_CHANNELS, watch_page, gopal_credits, song_from_title, partner, venue

D = sys.argv[1]
SEEN = os.path.join(D, 'seen_videos.json')
LIVE = os.path.join(D, 'live_performances.json')
BLOCKED = os.path.join(D, 'embed_blocked.json')
QUERIES = ['Ramu Maharajapuram', 'Maharajapuram Ramu', 'SPB Ramu singer', 'Singer Ramu SPB voice', 'SPB Ramu live',
           'Ramu Maharajapuram live orchestra']


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en'}), timeout=30) as r:
        page = r.read().decode()
    return json.loads(re.search(r'var ytInitialData = (\{.*?\});</script>', page, re.S).group(1))


def text(o):
    if not o:
        return ''
    return o.get('simpleText') or ''.join(r.get('text', '') for r in o.get('runs', []))


def walk(o, out, channel=''):
    if isinstance(o, dict):
        vr = o.get('videoRenderer')
        if vr and vr.get('videoId'):
            out.append({'id': vr['videoId'], 'title': text(vr.get('title')), 'channel': text(vr.get('ownerText')) or channel,
                        'published': text(vr.get('publishedTimeText')), 'length': text(vr.get('lengthText'))})
        for v in o.values():
            walk(v, out, channel)
    elif isinstance(o, list):
        for v in o:
            walk(v, out, channel)


seen = set(json.load(open(SEEN))) if os.path.exists(SEEN) else set()
live = json.load(open(LIVE)) if os.path.exists(LIVE) else []
blocked = json.load(open(BLOCKED)) if os.path.exists(BLOCKED) else []
on_site = {x['id'] for x in live}
for f in glob.glob('docs/**/*.html', recursive=True):
    on_site |= set(re.findall(r'(?:youtube\.com/watch\?v=|youtu\.be/|ytimg\.com/vi/|data-id=")([\w-]{11})', open(f).read()))
on_site |= {x['id'] for x in json.load(open(os.path.join(D, 'youtube_verified.json')))}

pages = [('https://www.youtube.com/results?' + urllib.parse.urlencode({'search_query': q, 'sp': 'CAI='}), '') for q in QUERIES]  # newest first
pages += [(f'https://www.youtube.com/channel/{cid}/search?' + urllib.parse.urlencode({'query': 'Ramu'}), name) for name, cid in TRUSTED.items()]
found = {}
for url, channel in pages:
    try:
        out = []
        walk(get(url), out, channel)
    except Exception as e:
        print(f'search failed for {url[:80]}: {e.__class__.__name__}', file=sys.stderr)
        continue
    for v in out:
        hay = f"{v['title']} {v['channel']}"
        if not re.search(r'\bramu\b|ராமு|రాము|maharajapuram', hay, re.I) or NOT_HIM.search(hay):
            continue
        if v['id'] in seen or v['id'] in on_site:
            continue
        found.setdefault(v['id'], v)
    time.sleep(1)

auto, cands = [], []
for v in found.values():
    if v['channel'] == 'Gopal Sapthaswaram':
        try:
            w = watch_page(v['id'])
        except Exception:
            w = None
        cr = gopal_credits(w['desc']) if w else None
        if cr and re.search(r'\bRamu\b', v['title'] + w['desc']):
            live.append({'id': v['id'], 'song': song_from_title(v['title']).strip('"'), 'film': cr['film'], 'year': cr['year'],
                         'lang': 'tamil', 'orig': cr['orig'], 'spb': cr['spb'], 'confidence': 'high',
                         'venue': venue(v['channel'], v['title'], w['desc'], w['date']), 'secs': w['secs'], 'date': w['date'],
                         'note': (f"with {partner(v['title'], w['desc'])}" if partner(v['title'], w['desc']) else ''),
                         'channel': v['channel'], 'source': 'video description', 'added': time.strftime('%Y-%m-%d')})
            auto.append(v)
            continue
    v['trusted'] = v['channel'] in TRUSTED
    v['blocked'] = v['channel'] in EMBED_BLOCKED_CHANNELS
    cands.append(v)

# Trusted channels first: those are almost certainly him.
cands = sorted(cands, key=lambda c: not c['trusted'])[:25]
json.dump(sorted(seen | {c['id'] for c in cands} | {a['id'] for a in auto}), open(SEEN, 'w'), indent=0)
if auto:
    json.dump(live, open(LIVE, 'w'), ensure_ascii=False, indent=1)
json.dump(cands, sys.stdout, ensure_ascii=False, indent=1)
print(f'discover_videos: {len(cands)} new candidates; {len(auto)} added to Listen automatically'
      + ''.join(f"\n  + {a['title']}" for a in auto), file=sys.stderr)
