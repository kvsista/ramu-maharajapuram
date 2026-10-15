"""Add a content-based version to stylesheet/script links so browsers never use a stale copy.

Usage: python3 tools/stamp_assets.py docs
Rewrites e.g. href="../site.css" or href="site.css?v=old" to href="../site.css?v=<hash>" in every page,
for site.css, news.js and news-config.js. Run after any change to those files (the weekly job runs it too).
"""
import hashlib, os, re, sys, glob

DOCS = sys.argv[1]
ASSETS = ['site.css', 'news.js', 'news-config.js', 'app.js']
ver = {a: hashlib.sha1(open(os.path.join(DOCS, a), 'rb').read()).hexdigest()[:10] for a in ASSETS if os.path.exists(os.path.join(DOCS, a))}
changed = 0
for page in glob.glob(os.path.join(DOCS, '**', '*.html'), recursive=True):
    s = open(page).read()
    t = s
    for a, v in ver.items():
        t = re.sub(r'((?:href|src)="(?:\.\./)*' + re.escape(a) + r')(?:\?v=[\w]+)?"', r'\1?v=' + v + '"', t)
    if t != s:
        open(page, 'w').write(t)
        changed += 1
print('stamp_assets:', ver, 'pages updated:', changed)
