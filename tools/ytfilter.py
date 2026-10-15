import json, re, sys, urllib.request, urllib.error, concurrent.futures as cf, collections
sp=sys.argv[1]
res=json.load(open(sp+'/yt/verified_raw.json'))
norm=lambda t: re.sub(r'[^a-z0-9]','',re.sub(r'\(.*?\)','',(t or '').lower()))
def parse(desc):
    lines=[l.strip() for l in desc.split('\n')]
    if not lines or not lines[0].startswith('Provided to YouTube by'): return None
    label=lines[0].replace('Provided to YouTube by','').strip()
    rest=[l for l in lines[1:] if l]
    credit=rest[0] if rest else ''; album=rest[1] if len(rest)>1 else ''
    parts=[p.strip() for p in credit.split('·')]
    yr=re.search(r'Released on: (\d{4})',desc) or re.search(r'℗ (\d{4})',desc)
    return {'label':label,'artists':parts[1:],'album':album,'year':int(yr.group(1)) if yr else None}
UA='Mozilla/5.0'
def oembed(vid):
    try:
        urllib.request.urlopen(urllib.request.Request(f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json',headers={'User-Agent':UA}),timeout=20); return True
    except urllib.error.HTTPError as e: return e.code
    except Exception as e: return str(e)[:40]
keep=[]; why=collections.Counter()
for r in res:
    d=parse(r['p'].get('desc',''))
    if r['id']=='hmX3KFm-1D0':
        r['meta']={'label':'Aditya Music','artists':['Ramu'],'album':'Attarintiki Daredi','year':2013}; keep.append(r); continue
    if not d: why['no-credit']+=1; continue
    if not any('ramu' in a.lower() for a in d['artists']): why['no-ramu']+=1; continue
    cands=r.get('cands')
    if cands and not any(norm(c[0])==norm(d['album']) for c in cands): why['album-mismatch']+=1; continue
    r['meta']=d; keep.append(r)
print('kept',len(keep),dict(why))
with cf.ThreadPoolExecutor(8) as ex: emb=list(ex.map(lambda r: oembed(r['id']), keep))
for r,e in zip(keep,emb): r['embed']=e
print('embed:',collections.Counter(str(r['embed']) for r in keep))
json.dump(keep,open(sp+'/yt/verified.json','w'),ensure_ascii=False,indent=1)
