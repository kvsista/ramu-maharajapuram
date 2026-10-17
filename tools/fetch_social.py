"""Pull Ramu's latest Facebook Page and Instagram posts into data/social.json, with photos saved on the site.

Usage: META_PAGE_TOKEN=... python3 tools/fetch_social.py data docs
The token is a Page access token for the "Ramu Maharajapuram" Facebook Page (stored as a GitHub secret).
Instagram is read through the Page, so his Instagram must be linked to the Page.
Photos are copied to docs/media/social/ so visitors' browsers never load anything from Meta.
Without a token, or if Meta refuses, the existing data is left as it is.
"""
import io, json, os, sys, urllib.parse, urllib.request

D, DOCS = sys.argv[1], sys.argv[2]
TOKEN = os.environ.get('META_PAGE_TOKEN', '').strip()
OUT = os.path.join(D, 'social.json')
MEDIA = os.path.join(DOCS, 'media', 'social')
KEEP = 12
if not TOKEN:
    print('fetch_social: no META_PAGE_TOKEN, skipping')
    sys.exit(0)


def graph(path, **params):
    params['access_token'] = TOKEN
    url = 'https://graph.facebook.com/v23.0/' + path + '?' + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        msg = json.load(e).get('error', {}).get('message', str(e))
        raise SystemExit(f'fetch_social: Meta refused {path.split("/")[-1] or path}: {msg}')


def save_photo(key, url):
    """Download, shrink to 900px and store as JPEG. Returns the site-relative path, or '' on failure."""
    if not url:
        return ''
    name = f'{key}.jpg'
    dest = os.path.join(MEDIA, name)
    if not os.path.exists(dest):
        try:
            raw = urllib.request.urlopen(url, timeout=30).read()
            from PIL import Image
            im = Image.open(io.BytesIO(raw)).convert('RGB')
            im.thumbnail((900, 900))
            os.makedirs(MEDIA, exist_ok=True)
            im.save(dest, 'JPEG', quality=82, optimize=True)
        except Exception as e:
            print('fetch_social: photo failed', key, e.__class__.__name__)
            return ''
    return 'media/social/' + name


page = graph('me', fields='id,name,link,username,instagram_business_account{id,username}')
ig = page.get('instagram_business_account') or {}
items = []

posts = graph(f"{page['id']}/posts", fields='id,message,created_time,permalink_url,full_picture', limit=15).get('data', [])
for p in posts:
    if not (p.get('message') or p.get('full_picture')):
        continue
    items.append({'src': 'facebook', 'id': p['id'], 'time': p['created_time'], 'text': p.get('message', ''),
                  'link': p.get('permalink_url', ''), 'photo': save_photo('fb_' + p['id'].split('_')[-1], p.get('full_picture'))})

if ig.get('id'):
    media = graph(f"{ig['id']}/media", fields='id,caption,media_type,media_url,thumbnail_url,permalink,timestamp', limit=15).get('data', [])
    for m in media:
        pic = m.get('thumbnail_url') if m.get('media_type') == 'VIDEO' else m.get('media_url')
        items.append({'src': 'instagram', 'id': m['id'], 'time': m['timestamp'], 'text': m.get('caption', ''),
                      'link': m.get('permalink', ''), 'video': m.get('media_type') == 'VIDEO', 'photo': save_photo('ig_' + m['id'], pic)})

# The same post often goes to both; keep the Instagram copy when captions match.
seen, uniq = set(), []
for it in sorted(items, key=lambda x: (x['time'], x['src'] == 'instagram'), reverse=True):
    k = ' '.join(it['text'].split())[:80].lower()
    if k and k in seen:
        continue
    seen.add(k)
    uniq.append(it)
uniq = uniq[:KEEP]

# Remove photos no longer shown.
used = {os.path.basename(i['photo']) for i in uniq if i['photo']}
for f in os.listdir(MEDIA) if os.path.isdir(MEDIA) else []:
    if f not in used:
        os.remove(os.path.join(MEDIA, f))

data = {'facebook': page.get('link') or f"https://www.facebook.com/{page['id']}", 'facebook_name': page.get('name', ''),
        'instagram': f"https://www.instagram.com/{ig['username']}/" if ig.get('username') else '', 'items': uniq}
json.dump(data, open(OUT, 'w'), ensure_ascii=False, indent=1)
print(f"fetch_social: {sum(i['src'] == 'facebook' for i in uniq)} Facebook, {sum(i['src'] == 'instagram' for i in uniq)} Instagram;"
      f" page={data['facebook']} instagram={data['instagram'] or 'not linked'}")
