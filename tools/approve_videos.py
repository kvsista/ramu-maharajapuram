"""Publish the videos the site owner approved in a "New videos to review" issue.

Usage (run by .github/workflows/approve-videos.yml):
  COMMENT="add 1 3" ISSUE_BODY="..." python3 tools/approve_videos.py data
Reads the candidate list embedded in the issue body, appends the chosen ones to
data/approved_videos.json and prints the titles that were added.
"""
import json, os, re, sys, time

D = sys.argv[1]
APPROVED = os.path.join(D, 'approved_videos.json')
comment = os.environ.get('COMMENT', '').strip().lower()
body = os.environ.get('ISSUE_BODY', '')

m = re.search(r'<!-- candidates:(.*?) -->', body, re.S)
if not m or not comment.startswith('add'):
    sys.exit('nothing to do')
cands = json.loads(m.group(1))
if 'all' in comment:
    picks = list(range(1, len(cands) + 1))
else:
    picks = [int(n) for n in re.findall(r'\d+', comment)]
approved = json.load(open(APPROVED)) if os.path.exists(APPROVED) else []
have = {a['id'] for a in approved}
added = []
for n in picks:
    if 1 <= n <= len(cands) and cands[n - 1]['id'] not in have:
        c = dict(cands[n - 1], added=time.strftime('%Y-%m-%d'))
        approved.insert(0, c)
        have.add(c['id'])
        added.append(c['title'])
json.dump(approved, open(APPROVED, 'w'), ensure_ascii=False, indent=1)
print('\n'.join(added) if added else 'none')
