"""Keep the "N albums and singles since 1998" figures in step with the discography.

Usage: python3 tools/update_counts.py data docs
Counts releases in data/merged_catalogue.json and rewrites the number wherever the pages quote it.
"""
import glob, json, os, re, sys

D, DOCS = sys.argv[1], sys.argv[2]
cat = json.load(open(os.path.join(D, 'merged_catalogue.json')))
n = len(cat['releases'])
PATTERNS = [
    (r'(<strong>)\d+(</strong><span>Albums and singles since)', r'\g<1>{n}\g<2>'),
    (r'(\b(?:released|With|with) )\d+( albums and singles)', r'\g<1>{n}\g<2>'),
    (r'(\b)\d+( albums and singles in Telugu)', r'\g<1>{n}\g<2>'),
]
changed = []
for page in glob.glob(os.path.join(DOCS, '**', 'index.html'), recursive=True):
    s = open(page).read()
    t = s
    for rx, rep in PATTERNS:
        t = re.sub(rx, rep.format(n=n), t)
    if t != s:
        open(page, 'w').write(t)
        changed.append(os.path.relpath(page, DOCS))
print(f'update_counts: {n} releases', ('updated ' + ', '.join(changed)) if changed else '(pages already current)')
