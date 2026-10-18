"""Small client for Google's Gemini API free tier (key in the GEMINI_API_KEY secret, from Google AI Studio).
GitHub Models, the first choice, was retired by GitHub on 30 July 2026."""
import json, os, re, urllib.error, urllib.request

TOKEN = os.environ.get('GEMINI_API_KEY', '')
API = 'https://generativelanguage.googleapis.com/v1beta/'

# Shared rules for every headline written for the site.
SYSTEM = """You write short headlines for the website of Ramu Maharajapuram ("SPB Ramu"), a playback and concert singer
from Nellore, based in Chennai, known for singing the songs of S. P. Balasubrahmanyam (SPB).
Rules: plain, respectful English; at most 9 words; no emojis, hashtags or @handles; no quotation marks around the whole headline.
Use only what the text actually says. Never add facts, places, dates, people, awards or actions that are not stated:
for example, do not say he performed, sang or was honoured somewhere unless the text says so; a bare place or date stays a place or date.
If the text is in Tamil or Telugu, paraphrase naturally rather than translating word for word.
If there is nothing to go on, answer exactly: NONE"""


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


def ask(model, prompt, system=SYSTEM):
    req = urllib.request.Request(f'{API}models/{model}:generateContent', data=json.dumps({
        'systemInstruction': {'parts': [{'text': system}]},
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


def post_prompt(post):
    where = 'Instagram' if post['src'] == 'instagram' else 'Facebook'
    return f"Write a headline for this {where} post by Ramu, dated {post['time'][:10]}. Caption:\n{post['text']}"
