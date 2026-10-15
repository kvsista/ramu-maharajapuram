import json, re, sys, urllib.request
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'
def get(url, data=None):
    req=urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers={'User-Agent':UA,'Accept-Language':'en','Content-Type':'application/json'})
    return urllib.request.urlopen(req, timeout=30).read().decode()
def walk(o, out, cont):
    if isinstance(o, dict):
        if 'lockupViewModel' in o and o['lockupViewModel'].get('contentType')=='LOCKUP_CONTENT_TYPE_VIDEO':
            v=o['lockupViewModel']
            out.append({'id':v['contentId'],'title':v['metadata']['lockupMetadataViewModel']['title']['content']})
        if 'continuationCommand' in o and isinstance(o['continuationCommand'],dict) and 'token' in o['continuationCommand']: cont.append(o['continuationCommand']['token'])
        for x in o.values(): walk(x,out,cont)
    elif isinstance(o,list):
        for x in o: walk(x,out,cont)
res={}
for pl in sys.argv[1:]:
    html=get('https://www.youtube.com/playlist?list='+pl)
    key=re.search(r'"INNERTUBE_API_KEY":"([^"]+)"',html).group(1)
    ver=re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"',html).group(1)
    data=json.loads(re.search(r'var ytInitialData = (\{.*?\});</script>',html,re.S).group(1))
    out=[];cont=[]; walk(data,out,cont)
    seen=set()
    while cont:
        tok=cont.pop()
        if tok in seen: continue
        seen.add(tok)
        j=json.loads(get(f'https://www.youtube.com/youtubei/v1/browse?key={key}',{'context':{'client':{'clientName':'WEB','clientVersion':ver,'hl':'en'}},'continuation':tok}))
        walk(j,out,cont)
    res[pl]=out
    print(pl,len(out),file=sys.stderr)
json.dump(res,open(sys.argv[0].rsplit('/',1)[0]+'/yt/uploads.json','w'),ensure_ascii=False,indent=1)
