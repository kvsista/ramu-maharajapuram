"""Write the news picked in the weekly review (data/news.json) into the pages, for search engines and visitors.

Usage: python3 tools/build_news.py docs
Fills the blocks between <!-- NEWS:upcoming:START/END --> (Invite page) and, if present, <!-- NEWS:latest:START/END -->.
Each section is hidden while it has nothing to show. (The homepage "Latest from Ramu" strip is written by build_home_new.py.)
"""
import csv, datetime, html, io, json, os, re, sys, urllib.request

DOCS = sys.argv[1]
text = ''
rows = list(csv.reader(io.StringIO(text)))
head = [h.strip().lower() for h in (rows[0] if rows else [])]


def col(*names):
    return next((i for i, h in enumerate(head) if any(h.startswith(n) for n in names)), None)


C = {k: col(*v) for k, v in {'type': ('what is it', 'type'), 'title': ('title',), 'date': ('date',), 'venue': ('city', 'venue'),
                              'details': ('details',), 'link': ('link',), 'photo': ('photo',), 'show': ('show',)}.items()}
get = lambda r, k: (r[C[k]].strip() if C[k] is not None and C[k] < len(r) else '')
items = [dict((k, get(r, k)) for k in C) for r in rows[1:]]
items = [x for x in items if re.fullmatch(r'y(es)?', x['show'], re.I) and x['title'] and re.fullmatch(r'\d{4}-\d{2}-\d{2}', x['date'])]
# News picked from his Instagram / Facebook posts in the weekly review issue (data/news.json).
jp = os.path.join(DOCS, '..', 'data', 'news.json')
for x in (json.load(open(jp)) if os.path.exists(jp) else []):
    items.append(dict({k: '' for k in C}, **{k: x.get(k, '') for k in C if k != 'show'}))
items.sort(key=lambda x: x['date'], reverse=True)
today = datetime.date.today().isoformat()
E = lambda s: html.escape(s, quote=True)


def card(x):
    upcoming = x['date'] >= today and 'concert' in x['type'].lower()
    d = datetime.date.fromisoformat(x['date']).strftime('%-d %b %Y')
    meta = ' · '.join(p for p in ['Upcoming' if upcoming else x['type'], d, x['venue']] if p)
    out = f'<article class="news-card"><p class="news-meta">{E(meta)}</p><h3>{E(x["title"])}</h3>'
    if x['details']:
        out += f'<p class="news-details">{E(x["details"])}</p>'
    link = x['link'] if re.match(r'https?://', x['link'], re.I) else ''
    photo = x['photo'] if re.match(r'https?://|/media/', x['photo'], re.I) else ''
    if photo and 'youtu' not in link:
        out += f'<img class="news-photo" src="{E(photo)}" alt="{E(x["title"])}" loading="lazy">'
    if link:
        label = 'View on Facebook ↗' if re.search(r'facebook\.com|fb\.watch', link) else 'View on Instagram ↗' if 'instagram.com' in link else 'Watch ↗' if 'youtu' in link else 'More details ↗'
        out += f'<a class="news-link" href="{E(link)}" target="_blank" rel="noopener">{label}</a>'
    return out + '</article>'


blocks = {
    'latest': items[:6],
    'upcoming': sorted([x for x in items if 'concert' in x['type'].lower() and x['date'] >= today], key=lambda x: x['date']),
}
for page in ['index.html', 'invite/index.html']:
    p = os.path.join(DOCS, page)
    s = open(p).read()
    for kind, lst in blocks.items():
        start, end = f'<!-- NEWS:{kind}:START -->', f'<!-- NEWS:{kind}:END -->'
        if start in s:
            s = re.sub(re.escape(start) + '.*?' + re.escape(end), lambda m: start + ''.join(card(x) for x in lst) + end, s, flags=re.S)
            # show/hide the surrounding section in the static HTML
            s = re.sub(r'(<section class="news-section[^"]*"[^>]*data-kind="' + kind + r'")( hidden)?', lambda m: m.group(1) + ('' if lst else ' hidden'), s)
    open(p, 'w').write(s)
print('build_news:', {k: len(v) for k, v in blocks.items()})
