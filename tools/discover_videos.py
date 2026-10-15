"""Find new YouTube videos that mention Ramu, for a person to review (nothing is published here).

Usage: python3 tools/discover_videos.py data > candidates.json
Prints a JSON list of new candidate videos and records them in data/seen_videos.json so the
same video is never suggested twice. Official label releases are skipped (the Listen page
handles those automatically), as are videos already on the site.
"""
import json, os, re, sys, glob, urllib.request, urllib.parse, time

D = sys.argv[1]
SEEN = os.path.join(D, 'seen_videos.json')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'
QUERIES = ['Ramu Maharajapuram', 'Maharajapuram Ramu', 'SPB Ramu singer', 'Singer Ramu SPB voice']
EXCLUDE = re.compile(r'ramachandran|santhanam|- topic', re.I)


def fetch(q):
    url = 'https://www.youtube.com/results?' + urllib.parse.urlencode({'search_query': q, 'sp': 'CAI='})  # newest first
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en'}), timeout=30) as r:
        page = r.read().decode()
    return json.loads(re.search(r'var ytInitialData = (\{.*?\});</script>', page, re.S).group(1))


def text(o):
    if not o:
        return ''
    return o.get('simpleText') or ''.join(r.get('text', '') for r in o.get('runs', []))


def walk(o, out):
    if isinstance(o, dict):
        vr = o.get('videoRenderer')
        if vr and vr.get('videoId'):
            out.append({'id': vr['videoId'], 'title': text(vr.get('title')), 'channel': text(vr.get('ownerText')),
                        'published': text(vr.get('publishedTimeText')), 'length': text(vr.get('lengthText'))})
        for v in o.values():
            walk(v, out)
    elif isinstance(o, list):
        for v in o:
            walk(v, out)


seen = set(json.load(open(SEEN))) if os.path.exists(SEEN) else set()
on_site = set()
for f in glob.glob('docs/**/*.html', recursive=True):
    on_site |= set(re.findall(r'(?:youtube\.com/watch\?v=|youtu\.be/|ytimg\.com/vi/|data-id=")([\w-]{11})', open(f).read()))
on_site |= {x['id'] for x in json.load(open(os.path.join(D, 'youtube_verified.json')))}

found = {}
for q in QUERIES:
    try:
        out = []
        walk(fetch(q), out)
    except Exception as e:
        print(f'search failed for {q!r}: {e.__class__.__name__}', file=sys.stderr)
        continue
    for v in out:
        hay = f"{v['title']} {v['channel']}"
        if 'ramu' not in hay.lower() or EXCLUDE.search(hay):
            continue
        if v['id'] in seen or v['id'] in on_site:
            continue
        found[v['id']] = v
    time.sleep(1)

cands = list(found.values())[:25]
json.dump(sorted(seen | {c['id'] for c in cands}), open(SEEN, 'w'), indent=0)
json.dump(cands, sys.stdout, ensure_ascii=False, indent=1)
print(f'discover_videos: {len(cands)} new candidates', file=sys.stderr)
