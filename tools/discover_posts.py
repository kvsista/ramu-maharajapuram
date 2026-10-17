"""List Ramu's Instagram / Facebook posts that haven't been offered for review yet.

Usage: python3 tools/discover_posts.py data > posts.json
Reads data/social.json (kept fresh by the daily social job) and remembers what it offered in
data/seen_posts.json. The weekly review issue lists these so the owner can turn one into Home
news ("news P2") or a Story entry ("story P2: title").
"""
import json, os, sys

D = sys.argv[1]
SEEN = os.path.join(D, 'seen_posts.json')
social = json.load(open(os.path.join(D, 'social.json'))) if os.path.exists(os.path.join(D, 'social.json')) else {'items': []}
seen = set(json.load(open(SEEN))) if os.path.exists(SEEN) else set()
new = [i for i in social.get('items', []) if i['id'] not in seen and i.get('link')]
json.dump(sorted(seen | {i['id'] for i in new}), open(SEEN, 'w'), indent=0)
json.dump(new, sys.stdout, ensure_ascii=False, indent=1)
print(f'discover_posts: {len(new)} new posts', file=sys.stderr)
