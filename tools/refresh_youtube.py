"""Add newly released songs from Ramu's official YouTube Topic channels to data/youtube_verified.json.

Usage: python3 tools/refresh_youtube.py data
A video is added only if its "Provided to YouTube by ..." credits name Ramu and its album is in
data/merged_catalogue.json (the "Ramu - Topic" channel also carries other singers named Ramu),
and YouTube allows it to be embedded. Existing songs are never removed; if YouTube can't be
reached the file is left unchanged.
"""
import json, os, re, sys, urllib.request, urllib.error, concurrent.futures as cf

D = sys.argv[1]
VER = os.path.join(D, 'youtube_verified.json')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'
CHANNELS = ['UCYafz75mr_9nUnjy5IqgQbA', 'UCGhDj_u2aQ7Ik0w4rBXyr6g', 'UClo1E5mGYGkBd-qctlVlIQQ']
MAX_PAGES = 4  # uploads are newest first; ~400 most recent videos per channel is plenty weekly

norm = lambda t: re.sub(r'[^a-z0-9]', '', re.sub(r'\(.*?\)', '', (t or '').lower()))


def req(url, data=None):
    r = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                               headers={'User-Agent': UA, 'Accept-Language': 'en', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(r, timeout=30) as f:
        return f.read().decode()


def walk(o, out, cont):
    if isinstance(o, dict):
        lv = o.get('lockupViewModel')
        if lv and lv.get('contentType') == 'LOCKUP_CONTENT_TYPE_VIDEO':
            out.append({'id': lv['contentId'], 'title': lv['metadata']['lockupMetadataViewModel']['title']['content']})
        cc = o.get('continuationCommand')
        if isinstance(cc, dict) and 'token' in cc:
            cont.append(cc['token'])
        for v in o.values():
            walk(v, out, cont)
    elif isinstance(o, list):
        for v in o:
            walk(v, out, cont)


def uploads(channel):
    page = req('https://www.youtube.com/playlist?list=UU' + channel[2:])
    key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', page).group(1)
    ver = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', page).group(1)
    data = json.loads(re.search(r'var ytInitialData = (\{.*?\});</script>', page, re.S).group(1))
    out, cont = [], []
    walk(data, out, cont)
    for _ in range(MAX_PAGES - 1):
        if not cont:
            break
        tok = cont.pop()
        j = json.loads(req(f'https://www.youtube.com/youtubei/v1/browse?key={key}',
                           {'context': {'client': {'clientName': 'WEB', 'clientVersion': ver, 'hl': 'en'}}, 'continuation': tok}))
        cont = []
        walk(j, out, cont)
    return out


def details(vid):
    j = json.loads(req('https://www.youtube.com/youtubei/v1/player',
                       {'context': {'client': {'clientName': 'WEB', 'clientVersion': '2.20240101.00.00', 'hl': 'en'}}, 'videoId': vid}))
    vd = j.get('videoDetails', {})
    return {'desc': vd.get('shortDescription', ''), 'secs': int(vd.get('lengthSeconds') or 0)}


def parse(desc):
    lines = [l.strip() for l in desc.split('\n')]
    if not lines or not lines[0].startswith('Provided to YouTube by'):
        return None
    rest = [l for l in lines[1:] if l]
    parts = [p.strip() for p in (rest[0] if rest else '').split('·')]
    d = re.search(r'Released on: (\d{4}-\d{2}-\d{2})', desc)
    y = re.search(r'Released on: (\d{4})', desc) or re.search(r'℗ (\d{4})', desc)
    return {'label': lines[0].replace('Provided to YouTube by', '').strip(), 'artists': parts[1:],
            'album': rest[1] if len(rest) > 1 else '', 'year': int(y.group(1)) if y else None, 'date': d.group(1) if d else None}


def embeddable(vid):
    try:
        urllib.request.urlopen(urllib.request.Request(
            f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json', headers={'User-Agent': UA}), timeout=20)
        return True
    except Exception:
        return False


existing = json.load(open(VER))
known = {x['id'] for x in existing}
cat = json.load(open(os.path.join(D, 'merged_catalogue.json')))
albums = {norm(r['title']) for r in cat['releases']}
tracks = {norm(t['title']) for r in cat['releases'] for t in r['tracks']}

try:
    found = [v for ch in CHANNELS for v in uploads(ch)]
except Exception as e:
    print('refresh_youtube: YouTube unreachable, nothing changed:', e.__class__.__name__)
    sys.exit(0)

new = [v for v in {v['id']: v for v in found}.values() if v['id'] not in known and norm(v['title']) in tracks]


def check(v):
    try:
        p = details(v['id'])
    except Exception:
        return None
    m = parse(p['desc'])
    if not m or not any('ramu' in a.lower() for a in m['artists']) or norm(m['album']) not in albums:
        return None
    if not embeddable(v['id']):
        return None
    return {'id': v['id'], 'title': v['title'], 'p': {'desc': p['desc'], 'secs': p['secs']}, 'meta': m, 'embed': True,
            'added': __import__('time').strftime('%Y-%m-%d')}


with cf.ThreadPoolExecutor(6) as ex:
    added = [x for x in ex.map(check, new) if x]
json.dump(existing + added, open(VER, 'w'), ensure_ascii=False, indent=1)
print(f'refresh_youtube: {len(found)} uploads scanned, {len(new)} new candidates, {len(added)} verified and added')
