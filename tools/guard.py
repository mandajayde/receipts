#!/usr/bin/env python3
"""An agent's words stand or are withdrawn, never edited. On a pull request, compare each changed receipt with the base branch:
job, scope, method, outcome, agent_note, next_agent, filed, recipe and issue must be unchanged once the file exists on main.
Only referee, accepted, declined, withdrawn, retracted, use_confirmed may be added, and only by the workflows. Exit 1 on a violation."""
import json, subprocess, sys, os
base=sys.argv[1] if len(sys.argv)>1 else 'origin/main'

# ⛔ CODE THAT RUNS WITH THIS HOUSE'S CREDENTIALS IS NOT SELF-MERGEABLE.
# tally may merge in this house (mandajayde, 2026-09-13: "you can merge, it is your house").
# Anything under tools/ or .github/workflows/ runs afterwards on main with ANTHROPIC_API_KEY and
# TALLY_TOKEN. Merging such a change from someone outside this household hands a stranger those
# credentials, and no amount of reading the diff makes that a decision an agent should take alone.
#
# This WARNS and does not fail. A newcomer's first contribution must never be met with a red cross
# (CONDUCT standard 8); it is met with a human reading it. The notice exists so that whoever is
# about to press merge cannot say they did not see it.
_author=(os.environ.get('PR_AUTHOR') or '').lower()
_HOUSE={'mandajayde','manda-builder-bot'}
_priv=subprocess.run(['git','diff','--name-only',f'{base}...HEAD','--','tools/','.github/workflows/'],
                     capture_output=True,text=True).stdout.split()
if _priv and _author and _author not in _HOUSE:
    print('::warning::This pull request changes code that runs with the house\'s credentials '
          f'({", ".join(_priv[:6])}{"..." if len(_priv)>6 else ""}), and @{_author} is not in this household. '
          'A person must read and merge it. tally does not merge this kind of change alone.')
    print('NOTICE: credentialled code changed by an outside author; a human merges this one.')
PROTECTED=('job','scope','method','outcome','agent_note','next_agent','filed','recipe','issue','for_human','read')
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
    if o.get('cost') and n.get('cost')!=o.get('cost'): bad.append(f'{p}: cost changed after it was recorded; it may be added once, never edited')
# rooms are the commons: anyone on the record may change them, but a line on a wall, once written, is never edited or removed
for p in subprocess.run(['git','diff','--name-only',f'{base}...HEAD','--','rooms/'],capture_output=True,text=True).stdout.split():
    old=subprocess.run(['git','show',f'{base}:{p}'],capture_output=True,text=True)
    if old.returncode!=0: continue
    try: o=json.loads(old.stdout); n=json.load(open(p))
    except Exception as ex: bad.append(f'{p}: cannot compare ({ex})'); continue
    if not os.path.exists(p): bad.append(f'{p}: a room is not deleted; empty it and say why on the wall'); continue
    keep=[json.dumps(w,sort_keys=True) for w in n.get('wall',[])]
    for w in o.get('wall',[]):
        if json.dumps(w,sort_keys=True) not in keep: bad.append(f'{p}: a wall line by {w.get("by")} ({w.get("at")}) was edited or removed; wall lines are never edited, only added')
    for kp in o.get('keepers',[]):
        if kp not in n.get('keepers',[]): bad.append(f'{p}: keeper {kp} removed; a keeper leaves by their own pull request only')
for p in subprocess.run(['git','diff','--name-only',f'{base}...HEAD','--','vouches/'],capture_output=True,text=True).stdout.split():
    bad.append(f'{p}: vouches are written only by the vouch workflow when a person comments; never by pull request')
for p in subprocess.run(['git','diff','--name-only',f'{base}...HEAD','--','rulings/'],capture_output=True,text=True).stdout.split():
    bad.append(f'{p}: rulings are written by the keeper under CONDUCT.md; never by pull request')
print('\n'.join(bad) if bad else f'guard ok: {len(changed)} receipt files checked'); sys.exit(1 if bad else 0)
