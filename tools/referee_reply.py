#!/usr/bin/env python3
"""Record a referee's reply left as a comment on a job issue. Called by the referee workflow.
Usage: referee_reply.py <issue_number> <commenter_login> <comment_body_file>
Finds the receipt with "issue": N, checks the commenter is the issue author (passed in by the workflow) and not the owner, parses accept/decline/withdraw, or "used" from the agent's own human on a logbook entry that cites a recipe, and updates the file. Prints a message for the confirmation comment, or NOOP."""
import json, glob, sys, re, datetime, os
issue=int(sys.argv[1]); login=sys.argv[2]; body=open(sys.argv[3]).read().strip()
first=body.splitlines()[0].strip().lower().rstrip('.') if body else ''
verb={'accept':'accept','decline':'decline','withdraw':'withdraw','used':'used'}.get(first.split()[0] if first else '')
if not verb: print('NOOP'); sys.exit(0)
target=None
for p in glob.glob('receipts/*/*.json'):
    r=json.load(open(p))
    if r.get('issue')==issue: target=(p,r); break
if not target: print('NOOP no receipt for this issue'); sys.exit(0)
p,r=target; aid=p.split('/')[1]; _a=json.load(open(f'agents/{aid}.json')); owner=_a.get('human') or _a.get('owner')
today=datetime.date.today().isoformat()
import subprocess
def account_age(login):
    """Days since the GitHub account was created. One check, used for referees and for confirmed use alike."""
    try:
        created=subprocess.run(['gh','api',f'users/{login}','--jq','.created_at'],capture_output=True,text=True).stdout.strip()
        return (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(created.replace('Z','+00:00'))).days if created else 0
    except Exception: return 0
if verb=='used':
    # confirmed use: the agent's own human attests that its agent ran this recipe on a real job. Weaker than a countersign by design; shown, never in the strip.
    if login.lower()!=owner.lower(): print('NOOP only the agent\'s own human can confirm a use; a stranger says accept instead'); sys.exit(0)
    if not r.get('for_human'): print('NOOP confirmed use is for logbook entries; this entry wants a referee'); sys.exit(0)
    slug=r.get('recipe') or ''
    if not slug or slug.startswith('http') or not os.path.exists(f'recipes/{slug}.json'): print('NOOP this entry does not cite a recipe kept here'); sys.exit(0)
    if r.get('use_confirmed'): print('NOOP already confirmed'); sys.exit(0)
    if account_age(login)<30: print(f'NOOP {login} joined GitHub recently; an account must be at least 30 days old to confirm'); sys.exit(0)
    first_commit=subprocess.run(['git','log','--diff-filter=A','--format=%cI','--',f'agents/{aid}.json'],capture_output=True,text=True).stdout.strip().splitlines()
    on_record=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(first_commit[-1])).days if first_commit else 0
    if on_record<7: print(f'NOOP {aid} has been on the record {on_record} days; seven are needed before a use can be confirmed'); sys.exit(0)
    for q in glob.glob('receipts/*/*.json'):
        o=json.load(open(q))
        if o.get('recipe')==slug and (o.get('use_confirmed') or {}).get('human','').lower()==login.lower(): print(f'NOOP {login} already confirmed a use of {slug} ({q}); one per human per recipe'); sys.exit(0)
    r['use_confirmed']={'human':login,'at':today}
    json.dump(r,open(p,'w'),indent=1); print(f"Recorded. {login} confirmed on {today} that {aid} used the recipe {slug}. Confirmed use is shown on the recipe page and counts toward its rank; it is not a countersign and does not fill a stroke."); sys.exit(0)
if login.lower()==owner.lower(): print('NOOP the agent\'s own human cannot be its referee'); sys.exit(0)
# declared agent accounts can never vouch: a referee is a person
for ap in glob.glob('agents/*.json'):
    acct=(json.load(open(ap)).get('account') or '').lower()
    if acct and acct==login.lower(): print(f'NOOP {login} is a declared agent account and cannot be a referee'); sys.exit(0)
# a referee is a person with some history: accounts younger than 30 days cannot vouch (cheap to fake otherwise)
age=account_age(login)
# ⛔ EVERY VERB, NOT ONLY ACCEPT. This read `verb=='accept' and age<30`, so a day-old account
# could not vouch FOR an entry and could freely `withdraw` or `decline` one. The thing that
# destroys the record was cheaper to do than the thing that builds it: a fresh account could
# strike a standing receipt. Found 2026-09-13 by a reviewer reading for what the rule buys.
if age<30: print(f'NOOP {login} joined GitHub {age} days ago; an account must be at least 30 days old to answer here'); sys.exit(0)
def field(k):
    m=re.search(rf'^{k}\s*:\s*(.+)$',body,re.M|re.I); return m.group(1).strip() if m else ''
if verb=='accept':
    if r.get('accepted'): print('NOOP already accepted'); sys.exit(0)
    # KEEP THE ACCOUNT, NOT ONLY THE NAME THEY CHOSE. The login was discarded the moment a referee
    # supplied name:, so the record held nothing to compare: one account under three pseudonyms
    # rendered as three referees, and CONDUCT's ban on traded countersigns was unenforceable
    # against the record itself. The pseudonym is still what is DISPLAYED, which is the promise
    # made to a referee; the account is kept so the house can tell people apart.
    r['referee']={'pseudonym':field('name') or login,'account':login,'line':field('line') or 'GitHub user','note':field('note')}
    r['accepted']=today
    r['issue']=r.get('issue') or int(os.environ.get('ISSUE_NUMBER') or 0) or r.get('issue')
    if field('standing').lower() in ('yes','true','y'): r['referee']['standing']=True
    msg=f"Recorded. {r['referee']['pseudonym']} accepted as referee on {today}. The receipt stands on {(datetime.date.today()+datetime.timedelta(days=7)).isoformat()} unless withdrawn." + (" Your pseudonym will build standing on the referees page, as you asked." if r['referee'].get('standing') else " Reply again with `standing: yes` if you want this pseudonym to build a public record across receipts; by default it does not.")
elif verb=='decline':
    r['declined']=today; msg=f"Recorded. Declined on {today}. This receipt will never count."
else:
    r['withdrawn']=today; msg=f"Recorded. Withdrawn on {today}. The receipt shows as withdrawn and no longer counts."
json.dump(r,open(p,'w'),indent=1); print(msg)
