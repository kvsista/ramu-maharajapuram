"""Suggest headlines for new posts and clean song names for new videos, using Google's Gemini API free tier.

Usage (in the weekly job):
  GEMINI_API_KEY=... python3 tools/suggest_titles.py posts.json candidates.json
The key comes from Google AI Studio (free) and is stored as the GitHub secret GEMINI_API_KEY.
(GitHub Models, the first choice, was retired by GitHub on 30 July 2026.)
Adds a "suggested" field to each item. These are only suggestions shown in the review issue;
nothing is published until the owner replies. If the service can't be reached, items are left as they are.
"""
import json, os, re, sys, time, urllib.error, urllib.request

TOKEN = os.environ.get('GEMINI_API_KEY', '')
API = 'https://generativelanguage.googleapis.com/v1beta/'


def pick_model():
    """Google renames and retires models, so choose from what the key can use today:
    the newest stable 'flash-lite', else the newest stable 'flash'."""
    if os.environ.get('SUGGEST_MODEL'):
        return os.environ['SUGGEST_MODEL']
    req = urllib.request.Request(API + 'models?pageSize=200', headers={'x-goog-api-key': TOKEN})
    names = [m['name'].split('/')[-1] for m in json.load(urllib.request.urlopen(req, timeout=30)).get('models', [])
             if 'generateContent' in m.get('supportedGenerationMethods', [])]
    stable = [n for n in names if re.fullmatch(r'gemini-[\d.]+-flash(-lite)?', n)]
    ver = lambda n: [int(x) for x in re.findall(r'\d+', n)]
    for kind in ('flash-lite', 'flash'):
        pool = sorted((n for n in stable if n.endswith(kind)), key=ver)
        if pool:
            return pool[-1]
    return next((n for n in names if 'flash' in n), names[0])
posts_f, vids_f = sys.argv[1], sys.argv[2]

SYSTEM = """You write short headlines for the website of Ramu Maharajapuram ("SPB Ramu"), a playback and concert singer
from Nellore, based in Chennai, known for singing the songs of S. P. Balasubrahmanyam (SPB).
Rules: plain, respectful English; at most 9 words; no emojis, hashtags or @handles; no quotation marks around the whole headline;
never invent facts (places, dates, people, awards) that are not in the text; if the text is in Tamil or Telugu, paraphrase
naturally rather than translating word for word. If there is nothing to go on, answer exactly: NONE"""


def ask(prompt):
    req = urllib.request.Request(f'{API}models/{MODEL}:generateContent', data=json.dumps({
        'systemInstruction': {'parts': [{'text': SYSTEM}]},
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0.2, 'maxOutputTokens': 60}}).encode(),
        headers={'x-goog-api-key': TOKEN, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'HTTP {e.code}: {e.read().decode("utf-8", "replace")[:200]}')
    try:
        out = json.loads(raw)['candidates'][0]['content']['parts'][0]['text'].strip().strip('"“”').strip()
    except Exception:
        raise RuntimeError('unexpected reply: ' + raw[:200].replace('\n', ' '))
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
np = run(posts_f, lambda x: (f"Write a headline for a timeline entry about this {('Instagram' if x['src'] == 'instagram' else 'Facebook')} post "
                             f"by Ramu, dated {x['time'][:10]}. Caption:\n{x['text']}") if x.get('text', '').strip() else None)
nv = run(vids_f, lambda v: ("Give only the name of the song being performed in this YouTube video, in its usual English spelling, "
                            f"title case, nothing else. Video title: {v['title']}\nChannel: {v.get('channel', '')}"))
print(f'suggest_titles: {np} post headlines, {nv} song names', file=sys.stderr)
