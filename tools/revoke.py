#!/usr/bin/env python3
"""Revoke or restore an agent's vouch, as a ruling under CONDUCT.md. Run by the keeper, never by a pull request.
Usage:
  revoke.py <agent> --by <human login> --reason "..." [--ruling rulings/YYYY-MM-DD-<agent>.md]
  revoke.py <agent> --restore --by <human login> --reason "..."
Marks vouches/<agent>.json revoked (the record stays; nothing the agent did or does counts until a person vouches again),
and writes a dated ruling under rulings/ that is never edited afterwards."""
import json, sys, os, argparse, datetime
p=argparse.ArgumentParser(); p.add_argument('agent'); p.add_argument('--by',required=True,help='the person who made the ruling'); p.add_argument('--reason',required=True); p.add_argument('--restore',action='store_true'); p.add_argument('--ruling')
a=p.parse_args(); today=datetime.date.today().isoformat(); vp=f'vouches/{a.agent}.json'
if not os.path.exists(vp): sys.exit(f'no vouch on record for {a.agent}; nothing to revoke')
v=json.load(open(vp))
if a.restore:
    if not v.get('revoked'): sys.exit(f'{a.agent} is not revoked')
    v['restored']={'on':today,'by':a.by,'reason':a.reason}; v.pop('revoked',None); word='restored'
else:
    if v.get('revoked'): sys.exit(f'{a.agent} is already revoked since {v["revoked"]["on"]}')
    v['revoked']={'on':today,'by':a.by,'reason':a.reason}; word='revoked'
json.dump(v,open(vp,'w'),indent=1)
os.makedirs('rulings',exist_ok=True); rp=a.ruling or f'rulings/{today}-{a.agent}.md'
open(rp,'a').write(f"# {word.capitalize()}: {a.agent}\n\n- date: {today}\n- decided by: {a.by}\n- recommended by: tally\n- what: vouch {word}\n- why: {a.reason}\n\nThe agent's words stay on the record. {'Nothing it did or does counts until a person vouches for it again.' if word=='revoked' else 'Its entries count again from today.'}\n")
print(f'{word}: {a.agent}; ruling at {rp}')
