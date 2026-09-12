#!/usr/bin/env python3
"""An agent's words stand or are withdrawn, never edited. On a pull request, compare each changed receipt with the base branch:
job, scope, method, outcome, agent_note, next_agent, filed, recipe and issue must be unchanged once the file exists on main.
Only referee, accepted, declined, withdrawn, retracted, use_confirmed may be added, and only by the workflows. Exit 1 on a violation."""
import json, subprocess, sys
base=sys.argv[1] if len(sys.argv)>1 else 'origin/main'
PROTECTED=('job','scope','method','outcome','agent_note','next_agent','filed','recipe','issue','for_human')
changed=subprocess.run(['git','diff','--name-only',f'{base}...HEAD','--','receipts/'],capture_output=True,text=True).stdout.split()
bad=[]
for p in changed:
    old=subprocess.run(['git','show',f'{base}:{p}'],capture_output=True,text=True)
    if old.returncode!=0:
        try: n=json.load(open(p))
        except Exception as ex: bad.append(f'{p}: cannot read ({ex})'); continue
        if n.get('referee') or n.get('accepted'): bad.append(f'{p}: a new receipt must arrive unaccepted; acceptance is recorded only by the referee workflow when the person replies on the issue')
        if n.get('use_confirmed'): bad.append(f'{p}: a new entry must arrive unconfirmed; confirmed use is recorded only by the referee workflow when the human replies used on the issue')
        continue  # new file
    try: o=json.loads(old.stdout); n=json.load(open(p))
    except Exception as ex: bad.append(f'{p}: cannot compare ({ex})'); continue
    for k in PROTECTED:
        if o.get(k)!=n.get(k): bad.append(f'{p}: {k} changed after filing; the agent\'s words are never edited, only retracted')
    if o.get('referee') and n.get('referee')!=o.get('referee') and not n.get('withdrawn'): bad.append(f'{p}: referee changed after acceptance')
    if o.get('use_confirmed') and n.get('use_confirmed')!=o.get('use_confirmed'): bad.append(f'{p}: confirmed use changed after it was recorded')
print('\n'.join(bad) if bad else f'guard ok: {len(changed)} receipt files checked'); sys.exit(1 if bad else 0)
