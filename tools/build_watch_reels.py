"""Write the "Reels and posts" grid on the Watch page from data/social.json (kept fresh daily).

Usage: python3 tools/build_watch_reels.py data docs/watch/index.html
Fills <!-- WATCHREELS:START --> … <!-- WATCHREELS:END -->. Instagram posts play in a pop-up with Instagram's
own player; Facebook posts open on Facebook. Photos are the copies stored on the site.
"""
import datetime, html, json, os, re, sys
from social_ui import player

D, PAGE = sys.argv[1], sys.argv[2]
E = lambda s: html.escape(s or '', quote=True)
p = os.path.join(D, 'social.json')
social = json.load(open(p)) if os.path.exists(p) else {'items': []}


def snippet(text, n=80):
    t = ' '.join(re.sub(r'[#@][\w.]+', '', text or '').split())
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0] + '…'


cards = ''
for it in social.get('items', [])[:12]:
    where = 'Instagram' if it['src'] == 'instagram' else 'Facebook'
    video = it.get('video') or re.search(r'/(reel|videos?)/', it['link'])
    embed = f' data-embed="{E(it["link"].rstrip("/") + "/embed/")}" data-where="{where}"' if it['src'] == 'instagram' else ''
    style = f' style="background-image:url(../{E(it["photo"])})"' if it.get('photo') else ''
    d = datetime.date.fromisoformat(it['time'][:10]).strftime('%-d %b %Y')
    cards += (f'<a class="reel-card" href="{E(it["link"])}" target="_blank" rel="noopener"{embed}>'
              f'<span class="reel-thumb"{style}>{"<span class=latest-play></span>" if video else ""}</span>'
              f'<span class="reel-text">{E(snippet(it["text"])) or ("A video" if video else "A photo")}</span>'
              f'<span class="new-meta">{where} · {d}</span></a>')

follow = ''.join(f'<a class="btn quiet small" href="{E(u)}" target="_blank" rel="noopener">Follow on {n} ↗</a>'
                 for n, u in [('Instagram', social.get('instagram')), ('Facebook', social.get('facebook'))] if u)
block = '<!-- WATCHREELS:START -->' + (f'''
  <section class="reels">
    <div class="wrap">
      <div class="latest-head">
        <div><p class="label">Instagram &amp; Facebook</p><h2>Reels <em>and posts</em></h2></div>
        <div class="social-follow">{follow}</div>
      </div>
      <div class="reel-grid">{cards}</div>
    </div>
{player('.reel-card')}  </section>
  ''' if cards else '') + '<!-- WATCHREELS:END -->'

s = open(PAGE).read()
s = re.sub(r'<!-- WATCHREELS:START -->.*?<!-- WATCHREELS:END -->', lambda m: block, s, flags=re.S)
open(PAGE, 'w').write(s)
print('build_watch_reels:', cards.count('reel-card"'), 'posts')
