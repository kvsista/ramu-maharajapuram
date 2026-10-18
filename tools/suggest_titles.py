"""Suggest headlines for new posts and clean song names for new videos, using Google's Gemini API free tier.

Usage (in the weekly job):
  GEMINI_API_KEY=... python3 tools/suggest_titles.py posts.json candidates.json
The key comes from Google AI Studio (free) and is stored as the GitHub secret GEMINI_API_KEY.
(GitHub Models, the first choice, was retired by GitHub on 30 July 2026.)
Adds a "suggested" field to each item. These are only suggestions shown in the review issue;
nothing is published until the owner replies. If the service can't be reached, items are left as they are.
"""
import json, sys, time
from gemini import TOKEN, pick_model, ask as gemini_ask, post_prompt

posts_f, vids_f = sys.argv[1], sys.argv[2]

def ask(prompt):
    return gemini_ask(MODEL, prompt)


def run(path, prompt_for):
    items = json.load(open(path))
    n = 0
    for it in items:
        p = prompt_for(it)
        if not p:
            continue
        try:
            s = ask(p)
        except Exception as e:
            print('suggest_titles: stopped,', e, file=sys.stderr)
            break
        if s:
            it['suggested'] = s
            n += 1
        time.sleep(4.5)  # stay well under the free tier's per-minute limit
    json.dump(items, open(path, 'w'), ensure_ascii=False, indent=1)
    return n


if not TOKEN:
    print('suggest_titles: no GEMINI_API_KEY, skipping (the issue simply shows no suggestions)', file=sys.stderr)
    sys.exit(0)

try:
    MODEL = pick_model()
except Exception as e:
    print('suggest_titles: could not list models,', e, file=sys.stderr)
    sys.exit(0)
print('suggest_titles: using', MODEL, file=sys.stderr)
# Reuse the headline the site already shows for a post, if the daily job has written one.
_cache = json.load(open('data/post_titles.json')) if __import__('os').path.exists('data/post_titles.json') else {}
_posts = json.load(open(posts_f))
for _p in _posts:
    if _cache.get(_p['id']):
        _p['suggested'] = _cache[_p['id']]
json.dump(_posts, open(posts_f, 'w'), ensure_ascii=False, indent=1)
np = run(posts_f, lambda x: post_prompt(x) if x.get('text', '').strip() and not x.get('suggested') else None)
nv = run(vids_f, lambda v: ("Give only the name of the song being performed in this YouTube video, in its usual English spelling, "
                            f"title case, nothing else. Video title: {v['title']}\nChannel: {v.get('channel', '')}"))
print(f'suggest_titles: {np} post headlines, {nv} song names', file=sys.stderr)
