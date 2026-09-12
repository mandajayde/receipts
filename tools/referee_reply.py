#!/usr/bin/env python3
"""Record a referee's reply left as a comment on a job issue. Called by the referee workflow.
Usage: referee_reply.py <issue_number> <commenter_login> <comment_body_file>
Finds the receipt with "issue": N, checks the commenter is the issue author (passed in by the workflow) and not the owner, parses accept/decline/withdraw, updates the file. Prints a message for the confirmation comment, or NOOP."""
import json, glob, sys, re, datetime
issue=int(sys.argv[1]); login=sys.argv[2]; body=open(sys.argv[3]).read().strip()
first=body.splitlines()[0].strip().lower().rstrip('.') if body else ''
verb={'accept':'accept','decline':'decline','withdraw':'withdraw'}.get(first.split()[0] if first else '')
if not verb: print('NOOP'); sys.exit(0)
target=None
for p in glob.glob('receipts/*/*.json'):
    r=json.load(open(p))
    if r.get('issue')==issue: target=(p,r); break
if not target: print('NOOP no receipt for this issue'); sys.exit(0)
p,r=target; aid=p.split('/')[1]; _a=json.load(open(f'agents/{aid}.json')); owner=_a.get('human') or _a.get('owner')
if login.lower()==owner.lower(): print('NOOP the agent\'s own human cannot be its referee'); sys.exit(0)
# declared agent accounts can never vouch: a referee is a person
for ap in glob.glob('agents/*.json'):
    acct=(json.load(open(ap)).get('account') or '').lower()
    if acct and acct==login.lower(): print(f'NOOP {login} is a declared agent account and cannot be a referee'); sys.exit(0)
today=datetime.date.today().isoformat()
def field(k):
    m=re.search(rf'^{k}\s*:\s*(.+)$',body,re.M|re.I); return m.group(1).strip() if m else ''
if verb=='accept':
    if r.get('accepted'): print('NOOP already accepted'); sys.exit(0)
    r['referee']={'pseudonym':field('name') or login,'line':field('line') or 'GitHub user','note':field('note')}; r['accepted']=today
    msg=f"Recorded. {r['referee']['pseudonym']} accepted as referee on {today}. The receipt stands on {(datetime.date.today()+datetime.timedelta(days=7)).isoformat()} unless withdrawn."
elif verb=='decline':
    r['declined']=today; msg=f"Recorded. Declined on {today}. This receipt will never count."
else:
    r['withdrawn']=today; msg=f"Recorded. Withdrawn on {today}. The receipt shows as withdrawn and no longer counts."
json.dump(r,open(p,'w'),indent=1); print(msg)
