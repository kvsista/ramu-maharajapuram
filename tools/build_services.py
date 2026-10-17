"""Write the "What Ramu does" list from data/services.json into every page that has the markers.

Usage: python3 tools/build_services.py data docs
One list, used by the homepage and the Invite page, so the two can't drift apart.
Text may contain simple HTML (<i>, &nbsp;); titles are escaped.
"""
import glob, html, json, os, re, sys

D, DOCS = sys.argv[1], sys.argv[2]
items = json.load(open(os.path.join(D, 'services.json')))
cards = ''.join(f'<article><h3>{html.escape(x["title"])}</h3><p>{x["text"]}</p></article>' for x in items)
n = 0
for page in glob.glob(os.path.join(DOCS, '**', 'index.html'), recursive=True):
    s = open(page).read()
    t = re.sub(r'<!-- SERVICES:START -->.*?<!-- SERVICES:END -->', lambda m: f'<!-- SERVICES:START -->{cards}<!-- SERVICES:END -->', s, flags=re.S)
    if t != s:
        open(page, 'w').write(t)
        n += 1
print(f'build_services: {len(items)} services on {n} page(s)')
