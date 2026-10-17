"""Act on the owner's reply to a weekly review issue.

Usage (run by .github/workflows/approve-videos.yml):
  COMMENT="..." ISSUE_BODY="..." python3 tools/approve_videos.py data docs
One instruction per line (several can share a comment):
  add 1 3          put videos 1 and 3 on the Watch page ("add all" for every video)
  listen 2 5       add videos 2 and 5 to Listen → Songs of SPB ("listen 2: Song name" names it)
  stage 4          add video 4 to Listen → More on stage & TV
  news P2          show post P2 in the homepage news (add ": a title" to choose the headline)
  story P3: Title  add post P3 to the top of the Story timeline with that title
Prints one line per thing it did.
"""
import datetime, html, json, os, re, shutil, sys, time
from live_util import watch_page, song_from_title, partner, venue, lang_guess, EMBED_BLOCKED_CHANNELS

D, DOCS = sys.argv[1], sys.argv[2]
comment = os.environ.get('COMMENT', '')
body = os.environ.get('ISSUE_BODY', '')
E = lambda s: html.escape(s or '', quote=True)


def embedded(tag):
    m = re.search(r'<!-- ' + tag + r':(.*?) -->', body, re.S)
    return json.loads(m.group(1)) if m else []


def load(name, default):
    p = os.path.join(D, name)
    return json.load(open(p)) if os.path.exists(p) else default


def save(name, data):
    json.dump(data, open(os.path.join(D, name), 'w'), ensure_ascii=False, indent=1)


videos, posts = embedded('candidates'), embedded('posts')
done = []


def keep_photo(post, folder):
    """Copy a post's stored photo somewhere permanent (social/ photos are pruned as new posts arrive)."""
    src = os.path.join(DOCS, post.get('photo') or '')
    if not post.get('photo') or not os.path.exists(src):
        return ''
    os.makedirs(os.path.join(DOCS, 'media', folder), exist_ok=True)
    dest = os.path.join('media', folder, os.path.basename(src))
    shutil.copy(src, os.path.join(DOCS, dest))
    return dest


def headline(text, n=90):
    t = re.sub(r'#\w+|@\w+', '', ' '.join((text or '').split())).strip()
    t = re.split(r'(?<=[.!?])\s', t)[0].strip(' .') if t else ''
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0] + '…'


for line in comment.splitlines():
    line = line.strip()
    m = re.match(r'(add|listen|stage|news|story)\b\s*(.*)', line, re.I)
    if not m:
        continue
    cmd, rest = m.group(1).lower(), m.group(2)
    title = rest.split(':', 1)[1].strip() if ':' in rest else ''
    nums = rest.split(':', 1)[0]

    if cmd in ('add', 'listen', 'stage'):
        picks = list(range(1, len(videos) + 1)) if 'all' in nums.lower() else [int(n) for n in re.findall(r'\d+', nums)]
        for n in picks:
            if not 1 <= n <= len(videos):
                continue
            v = videos[n - 1]
            if cmd == 'add':
                approved = load('approved_videos.json', [])
                if v['id'] not in {a['id'] for a in approved}:
                    approved.insert(0, dict(v, added=time.strftime('%Y-%m-%d')))
                    save('approved_videos.json', approved)
                    done.append(f"Watch page: {v['title']}")
                continue
            live = load('live_performances.json', [])
            if v['id'] in {x['id'] for x in live}:
                continue
            try:
                w = watch_page(v['id'])
            except Exception:
                w = {'desc': '', 'date': '', 'secs': 0, 'channel': v.get('channel', '')}
            ch = v.get('channel') or w['channel']
            p = partner(v['title'], w['desc'])
            live.insert(0, {'id': v['id'], 'song': (title if len(picks) == 1 else '') or v.get('suggested') or song_from_title(v['title']), 'film': '', 'year': None,
                            'lang': lang_guess(ch, v['title']), 'orig': [], 'spb': cmd == 'listen', 'confidence': 'owner',
                            'venue': venue(ch, v['title'], w['desc'], w['date']), 'secs': w['secs'], 'date': w['date'],
                            'note': f'with {p}' if p else '', 'channel': ch, 'source': 'approved in review issue',
                            'added': time.strftime('%Y-%m-%d')})
            save('live_performances.json', live)
            if v.get('blocked') or ch in EMBED_BLOCKED_CHANNELS:
                save('embed_blocked.json', sorted(set(load('embed_blocked.json', [])) | {v['id']}))
            done.append(f"Listen ({'Songs of SPB' if cmd == 'listen' else 'More on stage & TV'}): {live[0]['song']}")

    else:
        for n in [int(x) for x in re.findall(r'[Pp](\d+)', nums)]:
            if not 1 <= n <= len(posts):
                continue
            post = posts[n - 1]
            when = post['time'][:10]
            where = 'Instagram' if post['src'] == 'instagram' else 'Facebook'
            if cmd == 'news':
                news = load('news.json', [])
                if post['id'] in {x.get('post') for x in news}:
                    continue
                news.insert(0, {'post': post['id'], 'type': 'News', 'title': title or post.get('suggested') or headline(post['text']) or f'New on {where}',
                                'date': when, 'venue': '', 'details': headline(post['text'], 220) if title else '', 'link': post['link'],
                                'photo': '/' + keep_photo(post, 'news') if post.get('photo') else ''})
                save('news.json', news)
                done.append(f"Home news: {news[0]['title']}")
            else:
                title = title or post.get('suggested', '')
                if not title:
                    done.append(f'Story P{n} skipped: add a title after a colon, e.g. "story P{n}: Canada Day concert"')
                    continue
                page = os.path.join(DOCS, 'life-story', 'index.html')
                s = open(page).read()
                if post['link'] in s:
                    continue
                photo = keep_photo(post, 'story')
                d = datetime.date.fromisoformat(when)
                text = headline(post['text'], 300)
                media = (f'<div class="t-media"><figure><a class="yt-ext" href="{E(post["link"])}" target="_blank" rel="noopener" '
                         f'aria-label="{E(title)} (opens {where})" style="background-image:url(../{E(photo)})">'
                         + ('<span class="big-play"></span>' if post.get('video') else '')
                         + f'<span class="yt-ext-note">View on {where} ↗</span></a></figure></div>') if photo else ''
                entry = (f'''
        <li class="event">
          <time datetime="{d.strftime('%Y-%m')}">{d.strftime('%b %Y')}</time>
          <div class="card{' has-media' if media else ''}">
            <div class="t-text">
            <h3>{E(title)}</h3>
''' + (f'            <p>{E(text)}</p>\n' if text else '') + f'''            <p class="src"><a href="{E(post['link'])}" target="_blank" rel="noopener">{where}</a></p>
            </div>
            {media}
          </div>
        </li>
''')
                # Newest first: right after the first era heading.
                s = re.sub(r'(<ol class="timeline">\s*<li class="era">.*?</li>\n)', lambda m: m.group(1) + entry, s, count=1, flags=re.S)
                open(page, 'w').write(s)
                done.append(f'Story: {title}')

print('\n'.join(f'- {x}' for x in done) if done else 'Nothing matched. Use lines like `add 1 3`, `listen 2`, `stage 4`, `news P2` or `story P3: Title`.')
