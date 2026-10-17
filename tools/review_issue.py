"""Write the weekly review issue from candidates.json and posts.json.

Usage: python3 tools/review_issue.py candidates.json posts.json          # open a new issue
       python3 tools/review_issue.py candidates.json posts.json --edit 2 # rewrite issue #2 in place
Needs GH_TOKEN (the workflow's token) for the gh command.
"""
import json, subprocess, sys

c, p = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
edit = sys.argv[sys.argv.index('--edit') + 1] if '--edit' in sys.argv else None
if not c and not p:
    print('Nothing new to review.')
    raise SystemExit
L = ['New things found this week. Nothing here is on the site until you reply.', '',
     'Reply with one instruction per line, for example:', '',
     '```', 'listen 1 3', 'add 2', 'news P1', 'story P2: Canada Day concert, Mississauga', '```', '',
     '- `listen N` adds a video to **Listen → Songs of SPB** (he sings an SPB song). `listen N: Song name` also names the song',
     '- `stage N` adds it to **Listen → More on stage & TV** (any other song)',
     '- `add N` puts it on the **Watch** page (`add all` for every video)',
     '- `news PN` shows a post in the **homepage news** (optionally `news PN: Your headline`)',
     '- `story PN: Title` adds a post to the top of the **Story** timeline', '',
     'Where a **suggested** headline or song name is shown, `story PN`, `news PN` or `listen N` on its own uses it. '
     'Suggestions come from an AI model: check them before accepting.', '',
     'You can reply more than once. Close the issue when you are done.', '']
if c:
    L.append(f'### Videos ({len(c)})')
    for i, v in enumerate(c, 1):
        meta = ' · '.join(x for x in [v.get('channel'), v.get('published'), v.get('length')] if x)
        tags = (' ✓ his usual channel' if v.get('trusted') else '') + (' · plays on YouTube only' if v.get('blocked') else '')
        L.append(f"{i}. [{v['title']}](https://www.youtube.com/watch?v={v['id']}) — {meta}{tags}"
                 + (f"<br>Song: **{v['suggested']}**" if v.get('suggested') else ''))
    L.append('')
if p:
    L.append(f'### His posts ({len(p)})')
    for i, x in enumerate(p, 1):
        t = ' '.join(x['text'].split())[:120] or '(no caption)'
        where = 'Instagram' if x['src'] == 'instagram' else 'Facebook'
        L.append(f"P{i}. [{t}]({x['link']}) — {where} · {x['time'][:10]}{' · video' if x.get('video') else ''}"
                 + (f"<br>Suggested headline: **{x['suggested']}**" if x.get('suggested') else ''))
    L.append('')
L += ['<!-- candidates:' + json.dumps(c, ensure_ascii=False) + ' -->', '<!-- posts:' + json.dumps(p, ensure_ascii=False) + ' -->']
body = '\n'.join(L)
if edit:
    subprocess.run(['gh', 'issue', 'edit', edit, '--body', body], check=True)
else:
    subprocess.run(['gh', 'label', 'create', 'video-review', '--color', 'D2A95E', '--force'], check=False)
    subprocess.run(['gh', 'issue', 'create', '--title', f'Weekly review: {len(c)} videos, {len(p)} posts',
                    '--label', 'video-review', '--body', body], check=True)
