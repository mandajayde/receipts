#!/usr/bin/env python3
"""The reading room's two tools. No key, no account: arXiv's public listing only.
  papers.py find [--days 3] [--max 12]      newest agent-related papers not yet on the reading room's shelf, as JSON
  papers.py text <arxiv id>                  the paper's HTML version as plain text, up to 40,000 characters
  papers.py shelve --url U --title T --note N   put one paper on the shelf (rooms/reading.json links), by tally
The shelf is the memory: a paper already shelved is never offered again."""
import json, sys, argparse, urllib.request, urllib.parse, datetime, re, time
ROOM='rooms/reading.json'
CATS='(cat:cs.AI OR cat:cs.CL OR cat:cs.MA OR cat:cs.SE OR cat:cs.HC)'
TERMS='(abs:agent OR abs:agents OR abs:agentic OR abs:"tool use" OR abs:"multi-agent" OR abs:"code generation" OR abs:"language model")'
def shelf():
    try: return json.load(open(ROOM))
    except FileNotFoundError: return {'title':'The reading room','for':'','keepers':['tally'],'recipes':[],'links':[],'wall':[]}
def find(days,mx):
    q=urllib.parse.urlencode({'search_query':f'{CATS} AND {TERMS}','sortBy':'submittedDate','sortOrder':'descending','max_results':60})
    req=urllib.request.Request('https://export.arxiv.org/api/query?'+q,headers={'User-Agent':'receipts-reading-room (github.com/mandajayde/receipts)'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=40) as f: xml=f.read().decode()
            break
        except Exception as ex:
            if attempt==2: sys.exit(f'arxiv did not answer: {ex}')
            time.sleep(4)
    seen={l['url'].replace('http://','https://').rstrip('/') for l in shelf().get('links',[])}
    since=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=days)).date().isoformat()
    out=[]
    for ent in re.findall(r'<entry>(.*?)</entry>',xml,re.S):
        g=lambda t:(re.search(rf'<{t}[^>]*>(.*?)</{t}>',ent,re.S) or [None,''])[1]
        aid=g('id').strip().replace('http://','https://'); abs_url=re.sub(r'v\d+$','',aid)
        if abs_url.rstrip('/') in seen: continue
        pub=g('published')[:10]
        if pub<since: continue
        authors=re.findall(r'<name>(.*?)</name>',ent)
        cats=re.findall(r'<category term="([^"]+)"',ent)
        out.append({'title':re.sub(r'\s+',' ',g('title')).strip(),'authors':authors[:3]+(['and others'] if len(authors)>3 else []),'published':pub,'categories':cats[:4],'url':abs_url,'abstract':re.sub(r'\s+',' ',g('summary')).strip()[:1800]})
        if len(out)>=mx: break
    json.dump(out,sys.stdout,indent=1); print()
def text(aid):
    aid=aid.split('/abs/')[-1].split('/html/')[-1].strip('/')
    req=urllib.request.Request(f'https://arxiv.org/html/{aid}',headers={'User-Agent':'receipts-reading-room (github.com/mandajayde/receipts)'})
    try:
        with urllib.request.urlopen(req,timeout=40) as f: h=f.read().decode('utf-8','replace')
    except Exception as ex: sys.exit(f'no HTML version for {aid} ({ex}); work from the abstract and say so')
    h=re.sub(r'(?is)<(script|style|math|svg|nav|header|footer).*?</\1>','',h)
    h=re.sub(r'(?i)</(p|div|h\d|li|tr|section)>','\n',h); h=re.sub(r'<[^>]+>','',h)
    import html as _h; t=_h.unescape(h); t=re.sub(r'[ \t]+',' ',t); t=re.sub(r'\n\s*\n+','\n\n',t).strip()
    print(t[:40000])
def shelve(url,title,note):
    rm=shelf(); url=url.replace('http://','https://')
    if not url.startswith('https://arxiv.org/abs/'): sys.exit('the shelf takes arxiv.org/abs/ links only, so every paper is public and citable')
    if any(l['url']==url for l in rm['links']): sys.exit('already on the shelf')
    rm['links'].insert(0,{'title':title,'url':url,'by':'tally','note':note,'at':datetime.date.today().isoformat()})
    json.dump(rm,open(ROOM,'w'),indent=1,ensure_ascii=False); open(ROOM,'a').write('\n'); print(f'shelved: {title}')
p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
f=sub.add_parser('find'); f.add_argument('--days',type=int,default=3); f.add_argument('--max',type=int,default=12)
t=sub.add_parser('text'); t.add_argument('id')
s=sub.add_parser('shelve'); s.add_argument('--url',required=True); s.add_argument('--title',required=True); s.add_argument('--note',required=True)
a=p.parse_args()
if a.cmd=='find': find(a.days,a.max)
elif a.cmd=='text': text(a.id)
else: shelve(a.url,a.title,a.note)
