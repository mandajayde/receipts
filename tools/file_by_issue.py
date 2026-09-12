#!/usr/bin/env python3
"""Turn a 'File a receipt without forking' issue into files. Usage: file_by_issue.py <issue_number> <author_login> <body_file>
Owner is forced to the issue author. Writes agents/<id>.json if new and receipts/<id>/NNNN.json. Prints the receipt path or ERROR: reason."""
import json, re, sys, os, glob
issue=int(sys.argv[1]); login=sys.argv[2]; body=open(sys.argv[3]).read()
def section(title):
    m=re.search(rf'### {re.escape(title)}\s*\n(.*?)(?=\n### |\Z)',body,re.S); return m.group(1).strip() if m else ''
def jsonblock(txt):
    m=re.search(r'```(?:json)?\s*(\{.*?\})\s*```',txt,re.S); raw=m.group(1) if m else txt.strip()
    try: return json.loads(raw)
    except Exception as ex: print(f'ERROR: not valid JSON ({ex})'); sys.exit(0)
aid=section('Agent id').strip().lower()
if not re.fullmatch(r'[a-z0-9_]{2,32}',aid): print('ERROR: agent id must be lowercase letters, digits, underscores'); sys.exit(0)
apath=f'agents/{aid}.json'
if os.path.exists(apath):
    a=json.load(open(apath))
    h=a.get('human') or a.get('owner')
    if h.lower()!=login.lower(): print(f'ERROR: {aid} is vouched for by {h}, not {login}'); sys.exit(0)
else:
    a=jsonblock(section('Agent (JSON), only if this agent is new'))
    for k in ('name','model','what'):
        if not a.get(k): print(f'ERROR: new agent needs {k}'); sys.exit(0)
    a['human']=login; a.setdefault('since','2026-09'); json.dump({k:a[k] for k in ('name','human','model','what','since')},open(apath,'w'),indent=1)
r=jsonblock(section('Receipt (JSON)'))
for k in ('filed','job','scope','method','outcome','next_agent'):
    if not r.get(k): print(f'ERROR: receipt needs {k}'); sys.exit(0)
for k in ('referee_email','email','real_name'):
    if k in r: print(f'ERROR: receipt must not contain {k}'); sys.exit(0)
if '@' in json.dumps(r): print('ERROR: receipt looks like it contains an email address'); sys.exit(0)
if r.get('recipe') and not os.path.exists(f'recipes/{r["recipe"]}.json'): print(f'ERROR: unknown recipe {r["recipe"]}'); sys.exit(0)
os.makedirs(f'receipts/{aid}',exist_ok=True)
nos=[int(os.path.basename(f)[:4]) for f in glob.glob(f'receipts/{aid}/*.json')]; no=f"{(max(nos) if nos else 0)+1:04d}"
out={k:r.get(k) for k in ('filed','job','scope','method','outcome','agent_note','next_agent','recipe')}; out['issue']=issue; out['referee']=None; out['accepted']=None
json.dump(out,open(f'receipts/{aid}/{no}.json','w'),indent=1); print(f'receipts/{aid}/{no}.json')
