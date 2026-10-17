"""Suggest headlines for new posts and clean song names for new videos, using GitHub Models (free in Actions).

Usage (in the weekly job, which has `permissions: models: read`):
  GITHUB_TOKEN=... python3 tools/suggest_titles.py posts.json candidates.json
Adds a "suggested" field to each item. These are only suggestions shown in the review issue;
nothing is published until the owner replies. If the service can't be reached, items are left as they are.
"""
import json, os, re, sys, urllib.request

TOKEN = os.environ.get('GITHUB_TOKEN', '')
URL = 'https://models.github.ai/inference/chat/completions'
MODEL = os.environ.get('SUGGEST_MODEL', 'openai/gpt-4.1-mini')
posts_f, vids_f = sys.argv[1], sys.argv[2]

SYSTEM = """You write short headlines for the website of Ramu Maharajapuram ("SPB Ramu"), a playback and concert singer
from Nellore, based in Chennai, known for singing the songs of S. P. Balasubrahmanyam (SPB).
Rules: plain, respectful English; at most 9 words; no emojis, hashtags or @handles; no quotation marks around the whole headline;
never invent facts (places, dates, people, awards) that are not in the text; if the text is in Tamil or Telugu, paraphrase
naturally rather than translating word for word. If there is nothing to go on, answer exactly: NONE"""


def ask(prompt):
    req = urllib.request.Request(URL, data=json.dumps({'model': MODEL, 'temperature': 0.2, 'max_tokens': 40, 'messages': [
        {'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': prompt}]}).encode(),
        headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)['choices'][0]['message']['content'].strip().strip('"“”').strip()
    out = re.sub(r'[#@]\w+', '', out).strip(' .')
    return '' if not out or out.upper() == 'NONE' or len(out) > 90 else out


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
            print('suggest_titles: stopped,', e.__class__.__name__, getattr(e, 'code', ''), file=sys.stderr)
            break
        if s:
            it['suggested'] = s
            n += 1
    json.dump(items, open(path, 'w'), ensure_ascii=False, indent=1)
    return n


if not TOKEN:
    print('suggest_titles: no token, skipping', file=sys.stderr)
    sys.exit(0)

np = run(posts_f, lambda x: (f"Write a headline for a timeline entry about this {('Instagram' if x['src'] == 'instagram' else 'Facebook')} post "
                             f"by Ramu, dated {x['time'][:10]}. Caption:\n{x['text']}") if x.get('text', '').strip() else None)
nv = run(vids_f, lambda v: ("Give only the name of the song being performed in this YouTube video, in its usual English spelling, "
                            f"title case, nothing else. Video title: {v['title']}\nChannel: {v.get('channel', '')}"))
print(f'suggest_titles: {np} post headlines, {nv} song names', file=sys.stderr)
