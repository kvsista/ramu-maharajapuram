"""Give each of Ramu's posts a clean headline for the site (Home "Latest from Ramu" and Watch "Reels and posts").

Usage (daily social job): GEMINI_API_KEY=... python3 tools/post_headlines.py data
Headlines are written once per post by Gemini (free tier) and kept in data/post_titles.json, so the site
doesn't change from day to day and a headline can be corrected by editing that file. Posts without a caption
get none and the site falls back to "A video on Instagram". Without a key nothing changes.
"""
import json, os, sys, time
from gemini import TOKEN, pick_model, ask, post_prompt

D = sys.argv[1]
TITLES = os.path.join(D, 'post_titles.json')
titles = json.load(open(TITLES)) if os.path.exists(TITLES) else {}
social = json.load(open(os.path.join(D, 'social.json'))) if os.path.exists(os.path.join(D, 'social.json')) else {'items': []}
todo = [p for p in social.get('items', []) if p['id'] not in titles and p.get('text', '').strip()]
if not TOKEN or not todo:
    print('post_headlines:', 'no GEMINI_API_KEY' if not TOKEN else 'nothing new', file=sys.stderr)
    sys.exit(0)
try:
    model = pick_model()
except Exception as e:
    print('post_headlines: could not list models,', e, file=sys.stderr)
    sys.exit(0)
n = 0
for p in todo:
    try:
        h = ask(model, post_prompt(p))
    except Exception as e:
        print('post_headlines: stopped,', e, file=sys.stderr)
        break
    titles[p['id']] = h  # '' means "no good headline": keep the caption
    n += bool(h)
    time.sleep(4.5)
json.dump(titles, open(TITLES, 'w'), ensure_ascii=False, indent=1)
print(f'post_headlines: {n} new headlines with {model}', file=sys.stderr)
