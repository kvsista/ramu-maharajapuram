"""Write the "From his Instagram and Facebook" strip on the homepage from data/social.json.

Usage: python3 tools/build_social.py data docs/index.html
Fills the block between <!-- SOCIAL:START --> and <!-- SOCIAL:END -->; with no posts the block stays empty.
Also adds his Facebook and Instagram addresses to the homepage's structured data (sameAs) so search engines link them.
"""
import datetime, html, json, os, re, sys, urllib.parse

D, PAGE = sys.argv[1], sys.argv[2]
p = os.path.join(D, 'social.json')
data = json.load(open(p)) if os.path.exists(p) else {'items': []}
E = lambda s: html.escape(s or '', quote=True)
SHOW = 8


def snippet(text, n=110):
    t = ' '.join((text or '').split())
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0] + '…'


def embed_url(it):
    """The platform's own player for this post, opened only when a visitor taps the card."""
    link = it['link']
    # Instagram's embed player is verified to play here; Facebook posts open on Facebook instead.
    return link.rstrip('/') + '/embed/' if it['src'] == 'instagram' else ''


def card(it):
    d = datetime.datetime.fromisoformat(it['time'].replace('+0000', '+00:00')).strftime('%-d %b %Y')
    where = 'Instagram' if it['src'] == 'instagram' else 'Facebook'
    thumb = (f'<span class="social-thumb" style="background-image:url({E(it["photo"])})">' if it.get('photo')
             else '<span class="social-thumb social-thumb-text">')
    video = it.get('video') or re.search(r'/(reel|videos?)/', it['link'])
    thumb += ('<span class="latest-play"></span>' if video else '') + '</span>'
    return (f'<a class="social-card" href="{E(it["link"])}" target="_blank" rel="noopener" {(' data-embed="' + E(embed_url(it)) + '"') if embed_url(it) else ''} data-where="{where}">{thumb}'
            f'<span class="social-text">{E(snippet(it["text"])) or ("A video on " if it.get("video") else "A photo on ") + where}</span>'
            f'<span class="latest-meta">{where} · {d}</span></a>')


items = [i for i in data.get('items', []) if i.get('link')][:SHOW]
follow = ''.join(f'<a class="btn quiet small" href="{E(u)}" target="_blank" rel="noopener">{n} ↗</a>'
                 for n, u in [('Instagram', data.get('instagram')), ('Facebook', data.get('facebook'))] if u)
block = ''
if items:
    block = f'''
  <section class="social">
    <div class="wrap">
      <div class="latest-head">
        <div><p class="label">Follow Ramu</p><h2>From his <em>posts</em></h2></div>
        <div class="social-follow">{follow}</div>
      </div>
      <div class="social-grid">
        {"".join(card(i) for i in items)}
      </div>
    </div>
    <dialog class="social-player" id="social-player" aria-label="Post">
      <div class="social-player-bar"><a id="social-open" target="_blank" rel="noopener">Open ↗</a><button type="button" id="social-close">Close</button></div>
      <div class="social-player-frame" id="social-frame"></div>
    </dialog>
    <script>
    (() => {{
      // Tapping a post opens Instagram's or Facebook's own player here; nothing loads from Meta until then.
      const dlg = document.getElementById('social-player'), frame = document.getElementById('social-frame'), open = document.getElementById('social-open');
      if (!dlg.showModal) return;
      const shut = () => {{ frame.replaceChildren(); dlg.close(); }};
      document.querySelectorAll('.social-card[data-embed]').forEach((a) => a.addEventListener('click', (e) => {{
        e.preventDefault();
        if (window.RP) RP.pause();
        const f = document.createElement('iframe');
        f.src = a.dataset.embed; f.title = a.dataset.where + ' post'; f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen'; f.allowFullscreen = true;
        frame.replaceChildren(f); open.href = a.href; open.textContent = 'Open on ' + a.dataset.where + ' ↗';
        dlg.showModal();
      }}));
      document.getElementById('social-close').addEventListener('click', shut);
      dlg.addEventListener('click', (e) => {{ if (e.target === dlg) shut(); }});
      dlg.addEventListener('cancel', () => frame.replaceChildren());
    }})();
    </script>
  </section>
  '''

s = open(PAGE).read()
s = re.sub(r'<!-- SOCIAL:START -->.*?<!-- SOCIAL:END -->', lambda m: '<!-- SOCIAL:START -->' + block + '<!-- SOCIAL:END -->', s, flags=re.S)
for u in [data.get('facebook'), data.get('instagram')]:
    if u and u not in s:
        s = re.sub(r'("sameAs": \[)', lambda m: m.group(1) + f'\n        "{u}",', s, count=1)
open(PAGE, 'w').write(s)
print('build_social:', len(items), 'posts on the homepage')
