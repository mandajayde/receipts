#!/usr/bin/env python3
"""Check every agent and receipt file. Exit 1 on any problem. Run in CI on pull requests."""
import json, glob, os, re, sys, datetime
bad=[]
agents={}
for p in glob.glob('agents/*.json'):
    aid=os.path.basename(p)[:-5]
    if not re.fullmatch(r'[a-z0-9_]{2,32}',aid): bad.append(f'{p}: agent id must be lowercase letters, digits, underscore')
    try: a=json.load(open(p))
    except Exception as ex: bad.append(f'{p}: not valid JSON ({ex})'); continue
    for k in ('name','owner','model','what'):
        if not a.get(k): bad.append(f'{p}: missing {k}')
    if a.get('owner') and not re.fullmatch(r'[A-Za-z0-9-]{1,39}',a['owner']): bad.append(f'{p}: owner must be a GitHub username')
    agents[aid]=a
for p in glob.glob('receipts/*/*.json'):
    aid=p.split('/')[1]; no=os.path.basename(p)[:-5]
    if aid not in agents: bad.append(f'{p}: no agents/{aid}.json')
    if not re.fullmatch(r'\d{4}',no): bad.append(f'{p}: receipt file must be NNNN.json')
    try: r=json.load(open(p))
    except Exception as ex: bad.append(f'{p}: not valid JSON ({ex})'); continue
    for k in ('filed','job','scope','method','outcome'):
        if not r.get(k): bad.append(f'{p}: missing {k}')
    for k in ('referee_email','email','real_name'):
        if k in r: bad.append(f'{p}: must not contain {k}')
    if r.get('referee'):
        for k in ('pseudonym','line'):
            if not r['referee'].get(k): bad.append(f'{p}: referee needs {k}')
        if not r.get('accepted'): bad.append(f'{p}: referee present but no accepted date')
    if r.get('accepted'):
        try: datetime.date.fromisoformat(r['accepted'])
        except Exception: bad.append(f'{p}: accepted must be YYYY-MM-DD')
    if aid in agents and r.get('referee') and r['referee'].get('pseudonym','').lower()==agents[aid]['owner'].lower(): bad.append(f'{p}: referee cannot be the owner')
print('\n'.join(bad) if bad else f'ok: {len(agents)} agents, {len(glob.glob("receipts/*/*.json"))} receipts')
sys.exit(1 if bad else 0)
