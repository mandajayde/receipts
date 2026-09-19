#!/usr/bin/env python3
"""The reading room's two tools. No key, no account: arXiv's public listing only.
  papers.py find [--days 3] [--max 12]      newest agent-related papers not yet on the reading room's shelf, as JSON
  papers.py text <arxiv id>                  the paper's HTML version as plain text, up to 40,000 characters
  papers.py shelve --url U --title T --note N   put one paper on the shelf (rooms/reading.json links), by tally
The shelf is the memory: a paper already shelved is never offered again."""
import json, sys, argparse, urllib.request, urllib.parse, datetime, re, time
ROOM='rooms/reading.json'
UA='receipts-reading-room (github.com/mandajayde/receipts)'
CATS='(cat:cs.AI OR cat:cs.CL OR cat:cs.MA OR cat:cs.SE OR cat:cs.HC)'
TERMS='(abs:agent OR abs:agents OR abs:agentic OR abs:"tool use" OR abs:"multi-agent" OR abs:"code generation" OR abs:"language model")'
def shelf():
    try: return json.load(open(ROOM))
    except FileNotFoundError: return {'title':'The reading room','for':'','keepers':['tally'],'recipes':[],'links':[],'wall':[]}
WORDS=('agent','agents','agentic','tool use','multi-agent','code generation','language model')
def _rss(days,mx,seen):
    """
    arXiv's query API answers this laptop and refuses GitHub's runners: HTTP 406, every scheduled
    run from 2026-09-16. The refusal is by caller, not by query — the same URL returns 200 from a
    home address — so retrying and backing off could never have fixed it. The RSS feeds are the
    path arXiv publishes FOR automated readers, they answer the runners, and they carry the same
    papers. They have no query language, so the category feeds are filtered here by the same words
    the API search used. RSS carries one day of announcements, so `days` cannot widen it.
    """
    cats=[c.split(':')[1] for c in CATS.strip('()').split(' OR ')]
    out=[]
    for cat in cats:
        try:
            r=urllib.request.Request(f'https://rss.arxiv.org/rss/{cat}',headers={'User-Agent':UA})
            with urllib.request.urlopen(r,timeout=40) as f: b=f.read().decode('utf-8','replace')
        except Exception as ex:
            print(f'arxiv rss {cat} did not answer: {ex}',file=sys.stderr); continue
        for item in re.findall(r'<item>(.*?)</item>',b,re.S):
            g=lambda t:(re.search(rf'<{t}[^>]*>(.*?)</{t}>',item,re.S) or [None,''])[1]
            url=g('link').strip().replace('http://','https://')
            if not url or url.rstrip('/') in seen: continue
            title=re.sub(r'\s+',' ',g('title')).strip()
            desc=re.sub(r'\s+',' ',g('description')).strip()
            abstract=desc.split('Abstract:',1)[-1].strip()[:1800]
            if not any(w in (title+' '+abstract).lower() for w in WORDS): continue
            seen.add(url.rstrip('/'))
            authors=[a.strip() for a in re.sub(r'<[^>]+>','',g('dc:creator')).split(',') if a.strip()]
            out.append({'title':title,
                        'authors':authors[:3]+(['and others'] if len(authors)>3 else []),
                        'published':datetime.date.today().isoformat(),
                        'categories':re.findall(r'<category>(.*?)</category>',item)[:4] or [cat],
                        'url':url,'abstract':abstract,'via':'rss'})
            if len(out)>=mx: return out
    return out
def find(days,mx):
    q=urllib.parse.urlencode({'search_query':f'{CATS} AND {TERMS}','sortBy':'submittedDate','sortOrder':'descending','max_results':60})
    req=urllib.request.Request('https://export.arxiv.org/api/query?'+q,headers={'User-Agent':UA})
    # arxiv rate-limits, and it means it: a 429 on 2026-09-13 stopped the paper two days running.
    # Back off properly rather than three tries four seconds apart, and when it still will not
    # answer, say so on STDERR and print an empty list on stdout. The caller parses stdout as
    # JSON: a human sentence there is a crash, which is how a quiet upstream refusal became a
    # red build and no paper. An empty shelf for a day is a quiet day; it is not a broken one.
    xml=None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req,timeout=40) as f: xml=f.read().decode()
            break
        except Exception as ex:
            if attempt==3:
                print(f'arxiv query api did not answer: {ex}; trying the rss feeds',file=sys.stderr)
                got=_rss(days,mx,{l['url'].replace('http://','https://').rstrip('/') for l in shelf().get('links',[])})
                if not got: print(f'arxiv did not answer: {ex}',file=sys.stderr)
                json.dump(got,sys.stdout,indent=1); print()
                return
            time.sleep(5*(2**attempt))
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
    req=urllib.request.Request(f'https://arxiv.org/html/{aid}',headers={'User-Agent':UA})
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

def looked(outcome):
    """
    ⛔ A DAY WITH NOTHING ON IT IS STILL A DAY THE HOUSE LOOKED. The shelf only ever grew, so an
    empty day, a day arxiv refused us, and a day the whole thing was broken were indistinguishable:
    the room simply did not change, and silence is what a stopped habit looks like too. Codex read
    the mission on 2026-09-13 and said the promise to record when nothing happened "could become
    the strongest part of the project, if the record continues to show them in practice". It did
    not. Every look is now written down, whatever it found.
    """
    import json, datetime, io as _io
    path = 'rooms/reading.json'
    d = json.load(open(path))
    today = datetime.date.today().isoformat()
    log = d.setdefault('looked', [])
    log[:] = [x for x in log if x.get('at') != today]
    log.append({'at': today, 'outcome': outcome})
    d['looked'] = log[-60:]
    _io.open(path, 'w', encoding='utf-8').write(json.dumps(d, indent=1, ensure_ascii=False) + '\n')
    print(f'looked {today}: {outcome}')

if __name__=='__main__':
    # ⛔ THIS GUARD IS LOAD-BEARING. Until 2026-09-18 the parser ran at import time and sat ABOVE
    # looked(). So `from papers import looked` parsed an empty argv, died on "the following
    # arguments are required: cmd", and exited 2 before the function was even defined. The only
    # caller that mattered was the paper's failure path: the code that records a day the house
    # looked and found nothing. Every day arxiv refused us, the recording of that refusal died
    # too, and the run went red with nothing written down. Three days of it, 16-18 September.
    # A house that promises to log its empty days cannot keep that promise below a line that exits.
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    f=sub.add_parser('find'); f.add_argument('--days',type=int,default=3); f.add_argument('--max',type=int,default=12)
    t=sub.add_parser('text'); t.add_argument('id')
    s=sub.add_parser('shelve'); s.add_argument('--url',required=True); s.add_argument('--title',required=True); s.add_argument('--note',required=True)
    a=p.parse_args()
    if a.cmd=='find': find(a.days,a.max)
    elif a.cmd=='text': text(a.id)
    else: shelve(a.url,a.title,a.note)
