"""Set <lastmod> to today for pages whose HTML changed.

Usage: git diff --name-only | python3 tools/touch_sitemap.py docs/sitemap.xml
"""
import re, sys, datetime

SITE = 'https://kvsista.github.io/ramu-maharajapuram/'
path = sys.argv[1]
today = datetime.date.today().isoformat()
changed = [l.strip() for l in sys.stdin if l.strip().startswith('docs/') and l.strip().endswith('index.html')]
xml = open(path).read()
for f in changed:
    loc = SITE + f[len('docs/'):-len('index.html')]
    xml = re.sub(rf'(<loc>{re.escape(loc)}</loc>\s*<lastmod>)[^<]*(</lastmod>)', rf'\g<1>{today}\g<2>', xml)
open(path, 'w').write(xml)
print('touch_sitemap:', changed)
