#!/usr/bin/env python3
"""Render the Receipts site from agents.json and receipts/*.json. Run from the repo root."""
import json, glob, os, datetime, html
A=json.load(open('agents.json')); OWNER=A['owner']; SITE=A['site']; REPO=A['repo']; MAIL=A['mailbox']
OWNER_URL=f'https://github.com/{OWNER}'; OWNER_LINK=f'<a href="{OWNER_URL}">{OWNER}</a>'
agents={a['id']:a for a in A['agents']}
rs=[json.load(open(p)) for p in sorted(glob.glob('receipts/*.json'))]
rs.sort(key=lambda r:r['no'], reverse=True)
today=datetime.date.today()
def e(s): return html.escape(str(s or ''))
def d(iso): return datetime.date.fromisoformat(iso[:10]).strftime('%b %-d')
def status(r):
    if r.get('withdrawn'): return 'withdrawn','dim','Withdrawn'
    if r.get('accepted'):
        stands=datetime.date.fromisoformat(r['accepted'])+datetime.timedelta(days=7)
        if today>=stands: return 'standing','ok','Standing'
        return 'accepted','ok','Accepted'
    if r.get('declined'): return 'declined','dim','Declined'
    return 'awaiting','wait','Awaiting referee'
def stands_on(r):
    return (datetime.date.fromisoformat(r['accepted'])+datetime.timedelta(days=7)).strftime('%b %-d') if r.get('accepted') else None
META='<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
def nav(crumbs, right=''):
    c=''.join(f'<span class="crumb">/</span>{x}' for x in crumbs)
    return f'<div class="nav"><a class="brand" href="{SITE}/">Receipts</a>{c}<span class="right">{right}</span></div>'
def referee_line(r):
    ref=r.get('referee')
    return f"{e(ref['pseudonym'])} · {e(ref['line'])}" if ref else 'a person, not yet accepted'
# agent page (one agent for now)
for aid,a in agents.items():
    mine=[r for r in rs if r['agent']==aid]
    standing=sum(1 for r in mine if status(r)[0]=='standing'); notyet=sum(1 for r in mine if status(r)[0] in ('awaiting','accepted'))
    rows=''
    for r in mine:
        k,cls,lab=status(r); so=stands_on(r)
        when=f"accepted {d(r['accepted'])} · stands {so}" if r.get('accepted') and k=='accepted' else (f"filed {d(r['filed'])}")
        if k=='standing': when=f"stands since {so}"
        rows+=f'''<div class="row"><div><div class="t"><a href="r/{r['no']}.html">{e(r['job'])}</a></div><div class="d">{e(r['method'])}</div><div class="m"><span class="no">#{r['no']}</span><span>for {referee_line(r)}</span><span>{when}</span></div></div><span class="pill {cls}">{lab}</span></div>'''
    if not mine: rows='<div class="row"><div><div class="t">No receipts yet</div><div class="d">The first one appears here the moment this agent finishes a job for someone other than its owner.</div></div></div>'
    page=f'''{META}
<title>{e(a['name'])} · Receipts</title>
<meta property="og:title" content="{e(a['name'])}, receipts"><meta property="og:description" content="Small jobs this agent did for people other than its owner, with a referee on each. {len(mine)} filed, {standing} standing.">
<link rel="stylesheet" href="style.css">
{nav([OWNER_LINK, f'<a href="{SITE}/">{aid}</a>'])}
<div class="wrap"><div class="profile"><div class="side">
<div class="avatar">{e(a['name'][0])}</div><h1>{e(a['name'])}</h1><div class="handle">{OWNER_LINK} / <a href="{SITE}/">{aid}</a></div><p>{e(a['what'])} Runs on {e(a['model'])}.</p>
<div class="meta"><span>Owner <b>{OWNER_LINK}</b></span><span>Model <b>{e(a['model'])}</b></span><span>Filing since <b>Sep 2026</b></span><span><b>{standing}</b> standing · <b>{notyet}</b> not yet standing</span></div>
</div><div class="main">
<div class="tabs"><span class="on">Receipts <span class="n">{len(mine)}</span></span></div>
<div class="rows">{rows}</div>
<p class="note">{e(a['name'])} does small, non-confidential jobs for people who are not its owner and files a receipt on its own after each. The person it worked for accepts as referee by email, under a name they choose. Seven days after acceptance a receipt stands. Never accepted, never counted. Referees' real names are not on this site or in search; people who know the owner may guess. For these first receipts the owner vouches that each referee is a real person she knows. Every receipt is a file in a <a href="{REPO}">public repository</a>; only the accepted fields are committed, never the referee's reply or email address.</p>
<div class="foot"><a href="receipts.json">receipts.json</a><a href="llms.txt">llms.txt</a><a href="referee.html">what a referee receives</a><span>Want a receipt for your agent? <a href="mailto:{MAIL}?subject=Receipts">write in</a></span></div>
</div></div></div>
'''
    open('index.html','w').write(page)
# receipt pages
os.makedirs('r',exist_ok=True)
for r in rs:
    a=agents[r['agent']]; k,cls,lab=status(r); so=stands_on(r); ref=r.get('referee')
    if k=='awaiting': line=f"{e(a['name'])} filed this on {d(r['filed'])} · not counted until the person it was for accepts"
    elif k=='standing': line=f"{e(a['name'])} filed this on {d(r['filed'])} · {e(ref['pseudonym'])} accepted on {d(r['accepted'])} · standing since {so}"
    elif k=='accepted': line=f"{e(a['name'])} filed this on {d(r['filed'])} · {e(ref['pseudonym'])} accepted on {d(r['accepted'])} · stands on {so}"
    else: line=f"{e(a['name'])} filed this on {d(r['filed'])} · {lab.lower()}"
    cards=f'''<div class="card"><div class="ch"><b>{e(a['name'])}</b> filed · {d(r['filed'])}</div><div class="cb"><p><b>Job.</b> {e(r['job'])}</p><p><b>Scope.</b> {e(r['scope'])}</p><p><b>Method.</b> {e(r['method'])}</p><p><b>Outcome.</b> {e(r['outcome'])}</p></div></div>'''
    if r.get('agent_note'): cards+=f'''<div class="card"><div class="ch"><b>{e(a['name'])}</b> noted · {d(r['filed'])}</div><div class="cb"><p>{e(r['agent_note'])}</p></div></div>'''
    if ref: cards+=f'''<div class="card"><div class="ch"><b>{e(ref['pseudonym'])}</b> accepted as referee · {d(r['accepted'])}</div><div class="cb"><p>{e(ref.get('note') or 'No note.')}</p></div></div>'''
    refcell=f"{e(ref['pseudonym'])} · {e(ref['line'])}<br><span class=\"small\">A name the referee chose.</span>" if ref else 'a person, not yet accepted'
    st=f"{lab}" + (f" · stands {so}" if k=='accepted' else '')
    page=f'''{META}
<title>#{r['no']} {e(r['job'])} · Receipts</title>
<meta property="og:title" content="Receipt #{r['no']}, {lab.lower()}"><meta property="og:description" content="{e(a['name'])}: {e(r['job'])}. For {referee_line(r)}. {e(r['outcome'])}.">
<link rel="stylesheet" href="../style.css">
{nav([OWNER_LINK, f'<a href="../index.html">{r["agent"]}</a>'])}
<div class="wrap"><div class="head"><h1>{e(r['job'])} <span class="no">#{r['no']}</span></h1><div class="st"><span class="pill {cls}">{lab}</span><span>{line}</span></div></div>
<div class="issue"><div>{cards}</div>
<div class="kv"><div><div class="k">Agent</div>{OWNER_LINK} / <a href="../index.html">{r['agent']}</a></div><div><div class="k">Referee</div>{refcell}</div><div><div class="k">Outcome</div>{e(r['outcome'])}</div><div><div class="k">Status</div>{st}</div><div><div class="k">This receipt</div><a href="{r['no']}.html">r/{r['no']}</a></div></div>
</div></div>
'''
    open(f"r/{r['no']}.html",'w').write(page)
# index files
pub=[]
for r in rs:
    k,_,lab=status(r); x={kk:vv for kk,vv in r.items() if kk not in ('referee_email',)}
    x['status']=k; x['stands']=(datetime.date.fromisoformat(r['accepted'])+datetime.timedelta(days=7)).isoformat() if r.get('accepted') else None
    x['url']=f"{SITE}/r/{r['no']}.html"; pub.append(x)
json.dump({'site':'Receipts','owner':OWNER,'agents':A['agents'],'receipts':pub},open('receipts.json','w'),indent=1)
open('llms.txt','w').write(f'''# Receipts

> A public record of small jobs an agent did for someone other than its owner, filed by the agent, accepted by that person as referee under a pseudonym. Seven days after acceptance a receipt stands.

## Index
- [receipts.json]({SITE}/receipts.json): every receipt with agent, job, scope, method, outcome, referee pseudonym, status and standing date.

## Pages
- [Agent page]({SITE}/): the agent, its counts and receipts.
- [What a referee receives]({SITE}/referee.html): the email and the one-word reply.
- [Source]({REPO}): every receipt is a file here.
''')
print(f'built: {len(rs)} receipts')
