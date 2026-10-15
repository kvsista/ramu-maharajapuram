"""Rebuild the "Recently added" videos section of the Watch page from data/approved_videos.json.

Usage: python3 tools/build_watch_latest.py data docs/watch/index.html
Replaces everything between <!-- LATEST-VIDEOS:START --> and <!-- LATEST-VIDEOS:END -->.
Videos show as thumbnails and only load YouTube's player when tapped.
"""
import json, os, re, sys, html

D, PAGE = sys.argv[1], sys.argv[2]
E = lambda s: html.escape(s or '', quote=True)
path = os.path.join(D, 'approved_videos.json')
vids = json.load(open(path)) if os.path.exists(path) else []

if vids:
    cards = ''.join(
        f'''        <figure class="clip std yt-lite" data-id="{v['id']}">
          <button type="button" aria-label="Play {E(v['title'])}" style="background-image:url(https://i.ytimg.com/vi/{v['id']}/hqdefault.jpg)"><span class="big-play"></span></button>
          <figcaption>{E(v['title'])}<small>{E(v.get('channel'))}</small></figcaption>
        </figure>
''' for v in vids[:12])
    block = f'''<!-- LATEST-VIDEOS:START -->
  <section>
    <div class="wrap">
      <p class="label">Recently added</p>
      <h2>New <em>videos</em></h2>
      <div class="watch-row">
{cards}      </div>
    </div>
  </section>
  <!-- LATEST-VIDEOS:END -->'''
else:
    block = '<!-- LATEST-VIDEOS:START -->\n  <!-- LATEST-VIDEOS:END -->'

page = open(PAGE).read()
if '<!-- LATEST-VIDEOS:START -->' not in page:
    sys.exit('markers missing in ' + PAGE)
open(PAGE, 'w').write(re.sub(r'<!-- LATEST-VIDEOS:START -->.*?<!-- LATEST-VIDEOS:END -->', lambda m: block, page, flags=re.S))
print('build_watch_latest:', len(vids), 'videos')
