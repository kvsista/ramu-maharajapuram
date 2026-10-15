"""Fetch Ramu Maharajapuram's releases from free public music APIs (no keys needed).

Usage: python3 tools/fetch_catalogue.py data
Writes data/auto_releases.json (same shape as jiosaavn2_apple_qobuz.json releases) for tools/merge.py.
Each source is optional: if one fails, the others still run and the previous file's entries
for the failed source are kept, so a temporary outage never removes songs from the site.
"""
import json, os, re, sys, time, urllib.request, html

D = sys.argv[1]
OUT = os.path.join(D, 'auto_releases.json')
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'}

DEEZER_ARTISTS = [14754839, 226969425]            # "Maharajapuram Ramu", "Ramu Maharajapuram"
APPLE_ARTISTS = [1382880352, 1704160769, 1852789625]
JIOSAAVN_ARTISTS = [5947501]
LANGS = {'telugu', 'tamil', 'kannada', 'sanskrit', 'hindi'}


def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def is_ramu(name):
    return bool(name) and 'ramu' in name.lower() and 'ramachandran' not in name.lower()


def deezer():
    out = []
    for aid in DEEZER_ARTISTS:
        url = f'https://api.deezer.com/artist/{aid}/albums?limit=100'
        while url:
            page = get(url)
            for a in page.get('data', []):
                al = get(f"https://api.deezer.com/album/{a['id']}")
                tracks = [{'title': t['title'], 'ramu_sings': is_ramu(t.get('artist', {}).get('name')),
                           'links': {'deezer': t.get('link')}} for t in al.get('tracks', {}).get('data', [])]
                out.append({'source': 'deezer', 'title': al['title'], 'year': int(al['release_date'][:4]) if al.get('release_date') else None,
                            'date': al.get('release_date'), 'language': None, 'label': al.get('label'),
                            'type': 'single' if al.get('record_type') == 'single' else 'album',
                            'links': {'deezer': al.get('link')}, 'tracks': tracks})
                time.sleep(0.15)
            url = page.get('next')
    return out


def apple():
    out, seen = [], set()
    for aid in APPLE_ARTISTS:
        albums = get(f'https://itunes.apple.com/lookup?id={aid}&entity=album&limit=200&country=in').get('results', [])[1:]
        for al in albums:
            cid = al.get('collectionId')
            if not cid or cid in seen:
                continue
            seen.add(cid)
            songs = get(f'https://itunes.apple.com/lookup?id={cid}&entity=song&country=in').get('results', [])[1:]
            tracks = [{'title': s['trackName'], 'ramu_sings': is_ramu(s.get('artistName')), 'links': {'apple': s.get('trackViewUrl')}} for s in songs]
            title = re.sub(r'\s*-\s*(Single|EP)$', '', al.get('collectionName', ''))
            out.append({'source': 'apple', 'title': title, 'year': int(al['releaseDate'][:4]) if al.get('releaseDate') else None,
                        'date': (al.get('releaseDate') or '')[:10] or None, 'language': None, 'label': None,
                        'type': 'single' if al.get('trackCount') == 1 else 'album',
                        'links': {'apple': al.get('collectionViewUrl')}, 'tracks': tracks})
            time.sleep(0.2)
    return out


def jiosaavn():
    out = {}
    for aid in JIOSAAVN_ARTISTS:
        for page in range(3):  # newest 30 songs is plenty for a weekly check
            d = get(f'https://www.jiosaavn.com/api.php?__call=artist.getArtistMoreSong&artistId={aid}&page={page}'
                    f'&sort_order=desc&category=latest&api_version=4&_format=json&_marker=0&ctx=web6dot0')
            songs = (d.get('topSongs') or {}).get('songs') or []
            if not songs:
                break
            for s in songs:
                mi = s.get('more_info') or {}
                album = html.unescape(mi.get('album') or s.get('title') or '')
                singers = ' '.join(a.get('name', '') for a in ((mi.get('artistMap') or {}).get('primary_artists') or []))
                r = out.setdefault(album, {'source': 'jiosaavn', 'title': album, 'year': int(s['year']) if str(s.get('year', '')).isdigit() else None,
                                           'date': None, 'language': s.get('language') if s.get('language') in LANGS else None,
                                           'label': mi.get('label'), 'type': 'album',
                                           'links': {'jiosaavn': mi.get('album_url')}, 'tracks': []})
                r['tracks'].append({'title': html.unescape(s.get('title', '')), 'ramu_sings': is_ramu(singers) or not singers,
                                    'links': {'jiosaavn': s.get('perma_url')}})
            time.sleep(0.3)
    return list(out.values())


previous = json.load(open(OUT))['releases'] if os.path.exists(OUT) else []
releases, report = [], {}
for name, fn in [('deezer', deezer), ('apple', apple), ('jiosaavn', jiosaavn)]:
    try:
        got = fn()
        releases += got
        report[name] = len(got)
    except Exception as e:  # keep last good data for this source
        kept = [r for r in previous if r.get('source') == name]
        releases += kept
        report[name] = f'failed ({e.__class__.__name__}); kept {len(kept)} from last run'
releases = [r for r in releases if any(t.get('ramu_sings') for t in r['tracks'])]
json.dump({'fetched': time.strftime('%Y-%m-%d'), 'releases': releases}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('fetch_catalogue:', report, '->', len(releases), 'releases')
