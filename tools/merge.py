import json, re, sys, collections
D=sys.argv[1]
a=json.load(open(D+'/jiosaavn_maharajapuram_ramu.json'))
b=json.load(open(D+'/jiosaavn2_apple_qobuz.json'))
c=json.load(open(D+'/other_platforms_films.json'))
def norm(t):
    t=t.lower()
    t=re.sub(r'\((from|feat|original|single|ep)[^)]*\)','',t)
    t=re.sub(r'\s*-\s*(single|ep)$','',t)
    return re.sub(r'[^a-z0-9]','',t)
R={}
def get(title):
    k=norm(title)
    if k not in R: R[k]={'title':title,'years':set(),'language':None,'label':None,'labels':set(),'type':None,'film':False,'links':{},'tracks':{}}
    return R[k]
def addtracks(r, tracks, src):
    for t in tracks:
        if not t.get('ramu_sings'): continue
        tk=norm(t['title'])
        e=r['tracks'].setdefault(tk,{'title':t['title'],'links':{}})
        links=t.get('links') or {}
        if src=='js1' and t.get('url'): links={'jiosaavn':t['url']}
        for p,u in links.items():
            if u and p not in e['links']: e['links'][p]=u
for x in a['releases']:
    r=get(x['title']); r['years'].add(x.get('year')); r['language']=r['language'] or (x.get('language') if x.get('language')!='unknown' else None)
    r['labels'].add(x.get('label')); r['type']=r['type'] or x.get('type'); r['film']|=bool(x.get('is_film_soundtrack'))
    r['links'].setdefault('jiosaavn',x.get('url')); addtracks(r,x['tracks'],'js1')
for x in b['releases']:
    r=get(x['title']); r['years'].add(x.get('year'))
    if x.get('language') not in (None,'unknown'): r['language']=r['language'] or x['language']
    r['labels'].add(x.get('label')); r['type']=r['type'] or x.get('type'); r['film']|=bool(x.get('is_film_soundtrack'))
    for p,u in (x.get('links') or {}).items():
        if u: r['links'].setdefault(p,u)
    addtracks(r,x['tracks'],'b')
for x in c['releases']:
    r=get(x['title']); r['years'].add(x.get('year'))
    if x.get('language'): r['language']=r['language'] or x['language'].lower()
    r['labels'].add(x.get('label')); r['type']=r['type'] or x.get('type'); r['film']|=bool(x.get('is_film_soundtrack'))
    for p,u in (x.get('links') or {}).items():
        if u: r['links'].setdefault(p,u)
    addtracks(r,x['tracks'],'c')
out=[]
for k,r in R.items():
    ys=sorted(y for y in r['years'] if y)
    labels=[l for l in r['labels'] if l]
    out.append({'title':r['title'],'year':ys[0] if ys else None,'language':r['language'],'label':(sorted(labels,key=lambda l:('jayasindoor' not in l.lower(),l))[0] if labels else None),
      'type':'single' if len(r['tracks'])<=1 and r['type']!='album' else (r['type'] or 'album'),'film':r['film'],'links':r['links'],'tracks':list(r['tracks'].values())})
out=[o for o in out if o['tracks']]
out.sort(key=lambda o:(-(o['year'] or 0), o['title'].lower()))
json.dump({'releases':out,'artist_pages':c['artist_pages'],'videos':c['videos'],'film_and_tv':c['film_and_tv_credits']},open(D+'/merged_catalogue.json','w'),ensure_ascii=False,indent=1)
C=collections.Counter
print('releases',len(out),'tracks',sum(len(o['tracks']) for o in out))
print('lang',C(o['language'] for o in out))
print('platforms',C(p for o in out for p in o['links']))
print('years',min(o['year'] for o in out if o['year']),max(o['year'] for o in out if o['year']))
print('films',[o['title'] for o in out if o['film']])
