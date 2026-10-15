import json, re, sys, urllib.request, concurrent.futures as cf
sp=sys.argv[1]
m=json.load(open(sp+'/yt/matched.json'))
extra=[{'id':'--A2Zm54T2U','title':'Dabbu'},{'id':'oCViKY8ItSA','title':'Idam Maarum Nerame (Reprise)'},{'id':'hmX3KFm-1D0','title':'Kevvu Keka'}]
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'
def player(vid):
    body={'context':{'client':{'clientName':'WEB','clientVersion':'2.20240101.00.00','hl':'en'}},'videoId':vid}
    req=urllib.request.Request('https://www.youtube.com/youtubei/v1/player',data=json.dumps(body).encode(),headers={'User-Agent':UA,'Content-Type':'application/json'})
    j=json.loads(urllib.request.urlopen(req,timeout=30).read())
    ps=j.get('playabilityStatus',{}); vd=j.get('videoDetails',{})
    return {'status':ps.get('status'),'embed':ps.get('playableInEmbed'),'desc':vd.get('shortDescription',''),'secs':int(vd.get('lengthSeconds') or 0),'author':vd.get('author'),'views':int(vd.get('viewCount') or 0)}
def work(x):
    try: x['p']=player(x['id'])
    except Exception as e: x['p']={'err':str(e)}
    return x
items=m+extra
with cf.ThreadPoolExecutor(8) as ex: res=list(ex.map(work,items))
json.dump(res,open(sp+'/yt/verified_raw.json','w'),ensure_ascii=False,indent=1)
import collections
print(collections.Counter((r['p'].get('status'),r['p'].get('embed')) for r in res))
for r in res[:3]+res[-3:]: print(r['id'],r['title'],'|',r['p'].get('desc','')[:220].replace('\n',' / '))
