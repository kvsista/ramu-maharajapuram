import json, html, re, sys, collections
D, OUT = sys.argv[1], sys.argv[2]
d=json.load(open(D+'/merged_catalogue.json'))
def _fix(l):
    return {k:(v[0] if isinstance(v,list) else v) for k,v in l.items() if v}
for _r in d['releases']:
    _r['links']=_fix(_r['links'])
    for _t in _r['tracks']: _t['links']=_fix(_t['links'])
rel=d['releases']
E=lambda s: html.escape(s or '', quote=True)
def disp(t):
    t=t.replace('(ORIGINAL MOTION PICTURE SOUNDTRACK)',' (Original Motion Picture Soundtrack)')
    if t.upper()==t and re.search('[A-Z]',t):
        t=' '.join(w.capitalize() if not re.match(r'^[IVX]+$',w) else w for w in t.lower().split(' '))
        t=re.sub(r'\b(Sri|Om|Ki|Ka)\b', lambda m:m.group(0), t)
    return re.sub(r'\s+',' ',t).strip()
P=[('spotify','Spotify'),('apple','Apple Music'),('jiosaavn','JioSaavn'),('youtube','YouTube'),('deezer','Deezer'),('qobuz','Qobuz'),('gaana','Gaana'),('amazon','Amazon')]
LANG={'telugu':'Telugu','tamil':'Tamil','kannada':'Kannada','sanskrit':'Sanskrit',None:'Other'}
def chips(links, cls='chip'):
    return ''.join(f'<a class="{cls}" href="{E(links[k])}" target="_blank" rel="noopener">{n}</a>' for k,n in P if links.get(k))
films=[r for r in rel if r['film']]
cat=[r for r in rel if not r['film']]
cnt=collections.Counter(r['language'] for r in cat)
ntracks=sum(len(r['tracks']) for r in rel)
years=[r['year'] for r in rel if r['year']]
# film cards from film_and_tv credits (richer links)
ft={x['title']:x for x in d['film_and_tv']}
# In-film song confirmed by Ramu's family (2026-10-15); not on the released soundtrack, so no platform credit exists.
film_cards='''        <article class="film-card">
          <p class="film-meta">Telugu film · 2013</p>
          <h3>“Kevvu Keka” (comedy version)</h3>
          <p class="film-work"><i>Attarintiki Daredi</i> · Music: Devi Sri Prasad · On screen: Pawan Kalyan, Brahmanandam, Ali</p>
          <p class="film-note">Full song sung by Ramu. An in-film song, not released on the soundtrack album.</p>
          <div class="chips"><a class="chip" href="https://www.youtube.com/watch?v=hmX3KFm-1D0" target="_blank" rel="noopener">YouTube</a></div>
        </article>
'''
for key,work,lang,year,music in [('Dabbu','Partner (Telugu)','Telugu',2023,'Santhosh Dhayanidhi'),('Idam Maarum Nerame (Reprise)','Kasthuri Veedu','Tamil',2026,'Karthik Raja')]:
    x=ft[key]; links={k.replace('apple_music','apple'):v for k,v in x['links'].items() if not k.endswith('_album')}
    film_cards+=f'''        <article class="film-card">
          <p class="film-meta">{lang} film · {year}</p>
          <h3>“{E(key)}”</h3>
          <p class="film-work"><i>{E(work)}</i> · Music: {E(music)}</p>
          <div class="chips">{chips(links)}</div>
        </article>
'''
mano=ft.get('Title song') 
tv_items=''
for v in d['videos']:
    if v['kind']=='tv' and 'etvtelugu' in (v.get('channel') or ''):
        name=v['title'].split('|')[0].replace(' Song','').strip()
        when=re.search(r'(\d{1,2} \w{3} \d{4})',v['title'])
        tv_items+=f'<li><a href="{E(v["url"])}" target="_blank" rel="noopener">{E(name)}</a><span>Swarabhishekam, ETV · {when.group(1) if when else v["year"]}</span></li>'
vids=''
for v in d['videos']:
    if v['kind'] in ('song','concert') and 'Topic' not in (v.get('channel') or ''):
        t=v['title']; t=re.sub(r'\s*\|\s*Maharajapuram Ramu\s*','',t); t=t.split('|')[0].strip() if not t.startswith('SP Balasubrahmanyam') else 'SPB tribute: '+t.split('|')[2].strip()
        t=t.replace('&', ', with')
        vids+=f'<li><a href="{E(v["url"])}" target="_blank" rel="noopener">{E(t)}</a><span>{E(v.get("channel"))} · {v.get("year") or ""}</span></li>'
rows=[]
for r in cat:
    lang=r['language']; L=LANG.get(lang) if lang else ''
    tr=''.join(f'<li><span class="t">{E(disp(t["title"]))}</span><span class="chips">{chips(t["links"],"chip sm")}</span></li>' for t in r['tracks'])
    n=len(r['tracks'])
    rows.append(f'''<details class="rel" data-lang="{lang or 'other'}" data-q="{E((disp(r['title'])+' '+' '.join(t['title'] for t in r['tracks'])).lower())}">
<summary><span class="rt">{E(disp(r['title']))}</span><span class="rm">{' · '.join(x for x in [str(r['year'] or ''), L, E(r.get('label') or '')] if x)} · {n} song{'s' if n!=1 else ''}</span><span class="chips">{chips(r['links'])}</span></summary>
<ol class="tracks">{tr}</ol></details>''')
ap=d['artist_pages']
def first(pl,name=None):
    for p in ap:
        if p['platform']==pl and (name is None or p['name']==name): return p['url']
profiles=[('Spotify',first('spotify','Maharajapuram Ramu')),('Apple Music','https://music.apple.com/gb/artist/maharajapuram-ramu/1382880352'),('JioSaavn','https://www.jiosaavn.com/artist/maharajapuram-ramu-songs/CKus1x7BFic_'),('YouTube Music',first('youtube_music','MAHARAJAPURAM RAMU')),('Deezer',first('deezer','Maharajapuram Ramu')),('Gaana',first('gaana','Maharajapuram Ramu')),('Qobuz','https://www.qobuz.com/gb-en/interpreter/maharajapuram-ramu/5656664')]
prof=''.join(f'<a class="btn quiet small" href="{E(u)}" target="_blank" rel="noopener">{n} ↗</a>' for n,u in profiles if u)
filters=''.join(f'<button type="button" class="filter" data-f="{k}" aria-pressed="false">{LANG.get(k if k!="other" else None)} <span>{cnt.get(None if k=="other" else k,0)}</span></button>' for k in ['telugu','tamil','kannada','sanskrit','other'])
# The catalogue is now the Albums tab of the Listen page. This writes the panel it loads on demand
# (docs/listen/albums.html) and the album list for Listen's structured data (data/albums_ld.json).
ld_items=[{"@type":"ListItem","position":i+1,"item":{"@type":"MusicAlbum","name":disp(r['title']),**({"datePublished":str(r['year'])} if r['year'] else {}),"url":next((r['links'][k] for k,_ in P if r['links'].get(k)),None)}} for i,r in enumerate(rel)]
json.dump(ld_items,open(D+'/albums_ld.json','w'),ensure_ascii=False)
langs=''.join(f'<option value="{k}">{LANG.get(k if k!="other" else None)} ({cnt.get(None if k=="other" else k,0)})</option>' for k in ['telugu','tamil','kannada','sanskrit','other'] if cnt.get(None if k=="other" else k))
panel=f'''<div class="albums-head">
  <p class="lead">{len(rel)} albums and singles, {ntracks} songs, {min(years)}–{max(years)}. Tap a release to see its songs and where to stream them.</p>
</div>
<div class="toolbar" style="margin-top:14px">
  <label class="search"><span class="sr">Search albums and songs</span><input type="search" id="aq" placeholder="Search an album or song" autocomplete="off"></label>
</div>
<div class="pickers"><label class="pick"><span class="sr">Language</span><select id="alang"><option value="">All languages</option>{langs}</select></label></div>
<p class="count" id="acount" aria-live="polite">{len(cat)} releases</p>
<div class="rels" id="rels">
{chr(10).join(rows)}
</div>
<p class="empty" id="aempty" hidden>No releases match. Try another word or clear the filter.</p>
<div class="profiles" style="margin-top:28px"><span>Follow Ramu on</span>{prof}</div>
'''
open(OUT,'w').write(panel)
print('build_music: albums panel', len(panel)//1024,'KB,', len(cat), 'releases,', ntracks, 'songs')
