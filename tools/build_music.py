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
ld_items=[{"@type":"ListItem","position":i+1,"item":{"@type":"MusicAlbum","name":disp(r['title']),**({"datePublished":str(r['year'])} if r['year'] else {}),"byArtist":{"@id":"https://kvsista.github.io/ramu-maharajapuram/#ramu"},"url":next((r['links'][k] for k,_ in P if r['links'].get(k)),None)}} for i,r in enumerate(rel)]
ld={"@context":"https://schema.org","@graph":[
 {"@type":"CollectionPage","@id":"https://kvsista.github.io/ramu-maharajapuram/music/#page","url":"https://kvsista.github.io/ramu-maharajapuram/music/","name":"Discography · Ramu Maharajapuram","isPartOf":{"@id":"https://kvsista.github.io/ramu-maharajapuram/#website"},"about":{"@id":"https://kvsista.github.io/ramu-maharajapuram/#ramu"},"mainEntity":{"@type":"ItemList","numberOfItems":len(rel),"itemListElement":ld_items}},
 {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Ramu Maharajapuram","item":"https://kvsista.github.io/ramu-maharajapuram/"},{"@type":"ListItem","position":2,"name":"Discography","item":"https://kvsista.github.io/ramu-maharajapuram/music/"}]},
 {"@type":"Person","@id":"https://kvsista.github.io/ramu-maharajapuram/#ramu","name":"Ramu Maharajapuram","alternateName":["Maharajapuram Ramu","SPB Ramu"],"url":"https://kvsista.github.io/ramu-maharajapuram/"}]}
page=f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Discography · Ramu Maharajapuram (SPB Ramu) · Songs, Albums &amp; Films</title>
<meta name="description" content="Complete discography of singer Ramu Maharajapuram (SPB Ramu): {len(rel)} albums and singles, {ntracks} songs in Telugu, Tamil, Kannada and Sanskrit from {min(years)} to {max(years)}, including film songs from Partner and Kasthuri Veedu, with links to Spotify, Apple Music, JioSaavn, YouTube and Deezer.">
<link rel="canonical" href="https://kvsista.github.io/ramu-maharajapuram/music/">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta property="og:title" content="Discography · Ramu Maharajapuram (SPB Ramu)">
<meta property="og:description" content="{len(rel)} albums and singles, {ntracks} songs, {min(years)}–{max(years)}. Film songs, devotional albums and TV performances, with links to every platform.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://kvsista.github.io/ramu-maharajapuram/music/">
<meta property="og:site_name" content="Ramu Maharajapuram">
<meta property="og:image" content="https://kvsista.github.io/ramu-maharajapuram/media/stage-orange.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#11101a">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%2311101a'/%3E%3Ctext x='32' y='43' font-family='Georgia,serif' font-size='30' text-anchor='middle' fill='%23d2a95e'%3ERM%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;1,9..144,400&family=Manrope:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../site.css">
<script type="application/ld+json">{json.dumps(ld,ensure_ascii=False)}</script>
</head>
<body>
<header class="bar">
  <div class="wrap bar-inner">
    <a class="mark" href="../">Ramu Maharajapuram</a>
    <nav class="tabs" aria-label="Main">
      <a href="../">Home</a>
      <a href="../life-story/">Story</a>
      <a href="../listen/">Listen</a>
      <a href="../music/" aria-current="page">Music</a>
      <a href="../watch/">Watch</a>
      <a href="../press/">Press</a>
    </nav>
    <a class="btn primary small invite-btn" href="../invite/">Invite</a>
  </div>
</header>
<main>
  <section class="story-hero">
    <div class="wrap">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="../">Home</a> <span>/</span> Discography</nav>
      <p class="label">Discography</p>
      <h1>Songs, albums <em>and films</em></h1>
      <p class="lead">Every recording by Ramu Maharajapuram that is available on music platforms, from his first devotional albums to his latest film songs. Tap any release to see its songs.</p>
      <div class="stats disco-stats">
        <div><strong>{len(rel)}</strong><span>Albums and singles</span></div>
        <div><strong>{ntracks}</strong><span>Songs</span></div>
        <div><strong>{min(years)}–{max(years)}</strong><span>Years of recording</span></div>
        <div><strong>4</strong><span>Languages</span></div>
      </div>
      <div class="profiles"><span>Follow Ramu on</span>{prof}</div>
    </div>
  </section>

  <section class="alt">
    <div class="wrap">
      <p class="label">Film songs</p>
      <h2>On the <em>big screen</em></h2>
      <div class="film-grid">
{film_cards}      </div>
    </div>
  </section>

  <section>
    <div class="wrap split">
      <div>
        <p class="label">Television</p>
        <h2>On <em>TV</em></h2>
        <ul class="vlist">
          <li><span class="award-pill">Nandi TV Award</span><a href="https://apsftvtdc.in/pdf/TV-Awards-GOs-and-Results/Nandi%20tv%20Awards%202001.pdf" target="_blank" rel="noopener"><i>Mano Yagnam</i>, ETV serial</a><span>Best Male Playback Singer, award-year 2001 · <a href="https://www.youtube.com/watch?v=jWrTe7eHEhc" target="_blank" rel="noopener">title song</a></span></li>
          <li><span class="award-pill">Nandi TV Award</span><a href="https://apsftvtdc.in/pdf/TV-Awards-GOs-and-Results/Nandi%20tv%20Awards%202007.pdf" target="_blank" rel="noopener">Title song, <i>Thrisoolam</i></a><span>Best Male Playback Singer, award-year 2007</span></li>
          {tv_items}
        </ul>
      </div>
      <div>
        <p class="label">Videos</p>
        <h2>Songs and <em>concerts</em></h2>
        <ul class="vlist">{vids}</ul>
      </div>
    </div>
  </section>

  <section class="alt" id="catalogue">
    <div class="wrap">
      <p class="label">Albums &amp; singles</p>
      <h2>The <em>catalogue</em></h2>
      <div class="toolbar">
        <label class="search"><span class="sr">Search songs and albums</span><input type="search" id="q" placeholder="Search a song or album" autocomplete="off"></label>
        <div class="filters" role="group" aria-label="Filter by language">{filters}</div>
      </div>
      <p class="count" id="count" aria-live="polite">Showing all {len(cat)} releases</p>
      <div class="rels" id="rels">
{chr(10).join(rows)}
      </div>
      <p class="empty" id="empty" hidden>No releases match. Try another word or clear the filter.</p>
    </div>
  </section>
</main>
<footer>
  <div class="wrap">
    <span>© <span id="yr">2026</span> Ramu Maharajapuram</span>
    <span><a href="mailto:ramusinger@gmail.com">ramusinger@gmail.com</a> · <a href="tel:+919841038926">+91 98410 38926</a></span>
    <span><a href="../">Home</a> · <a href="../life-story/">Story</a> · <a href="../watch/">Watch</a> · <a href="../press/">Press</a> · <a href="../invite/">Invite</a></span>
    <span class="disamb">Ramu Maharajapuram, “SPB Ramu”, playback and concert singer. Not to be confused with the Carnatic vocalist Maharajapuram S. Ramachandran.</span>
  </div>
</footer>
<script src="../app.js"></script>
<script>
document.getElementById('yr').textContent = new Date().getFullYear();
const rels=[...document.querySelectorAll('.rel')], q=document.getElementById('q'), count=document.getElementById('count'), empty=document.getElementById('empty');
let lang=null;
function apply(){{
  const s=q.value.trim().toLowerCase(); let n=0;
  rels.forEach(r=>{{ const ok=(!lang||r.dataset.lang===lang)&&(!s||r.dataset.q.includes(s)); r.hidden=!ok; if(ok) n++; }});
  count.textContent = (n===rels.length) ? 'Showing all '+n+' releases' : 'Showing '+n+' of '+rels.length+' releases';
  empty.hidden = n>0;
}}
q.addEventListener('input', apply);
document.querySelectorAll('.filter').forEach(b=>b.addEventListener('click',()=>{{
  const on=b.getAttribute('aria-pressed')==='true';
  document.querySelectorAll('.filter').forEach(x=>x.setAttribute('aria-pressed','false'));
  if(!on){{ b.setAttribute('aria-pressed','true'); lang=b.dataset.f; }} else lang=null;
  apply();
}}));
</script>
</body>
</html>
'''
open(OUT,'w').write(page)
print(len(page)//1024,'KB', len(rel), ntracks, cnt)
