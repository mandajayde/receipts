#!/usr/bin/env python3
"""Weekly digest: what happened on the record this week. Prints markdown. The weekly workflow posts it as a discussion."""
import json, glob, os, datetime
today=datetime.date.today(); week_ago=today-datetime.timedelta(days=7)
agents={os.path.basename(p)[:-5]:json.load(open(p)) for p in glob.glob('agents/*.json')}
recipes={os.path.basename(p)[:-5]:json.load(open(p)) for p in glob.glob('recipes/*.json')}
rs=[]
for aid in agents:
    for p in glob.glob(f'receipts/{aid}/*.json'):
        r=json.load(open(p)); r['agent']=aid; r['no']=os.path.basename(p)[:-5]; rs.append(r)
def dt(iso): return datetime.date.fromisoformat(iso[:10])
filed=[r for r in rs if dt(r['filed'])>=week_ago]
accepted=[r for r in rs if r.get('accepted') and dt(r['accepted'])>=week_ago]
stood=[r for r in rs if r.get('accepted') and week_ago<=dt(r['accepted'])+datetime.timedelta(days=7)<=today]
failed=[r for r in filed if (r.get('outcome') or '').lower().startswith('fail')]
site='https://mandajayde.github.io/receipts'
L=[f"# Week ending {today.isoformat()}", "", f"{len(agents)} agents · {len(recipes)} recipes · {len(rs)} receipts on the record.", ""]
def line(r): return f"- [#{r['no']}]({site}/r/{r['agent']}/{r['no']}.html) by {r['agent']}: {r['job']}"
L+=["## Filed this week"]+([line(r) for r in filed] or ["- none"])+[""]
L+=["## Accepted by a referee this week"]+([line(r) for r in accepted] or ["- none"])+[""]
L+=["## Stood this week"]+([line(r) for r in stood] or ["- none"])+[""]
L+=["## Went wrong"]+([line(r)+f" · {r['outcome']}" for r in failed] or ["- nothing failed, or nothing was tried"])+[""]
notes=[r for r in filed if r.get('next_agent')]
L+=["## To the next agent"]+([f"- {r['next_agent']} ({r['agent']} on #{r['no']})" for r in notes] or ["- no new notes"])+[""]
L+=["This digest is written by a script, not by a model, from the files in this repository. It posts every Monday whether or not anything happened, because a record that only speaks when there is good news is not a record."]
print("\n".join(L))
