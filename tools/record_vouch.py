#!/usr/bin/env python3
"""Record a human's vouch for an agent, left as a comment "I vouch for <id>" on an issue or pull request.
Usage: record_vouch.py <commenter_login> <comment_body_file> <issue_or_pr_number>
Writes vouches/<id>.json, which only this workflow writes (the guard refuses it from pull requests).
Rules, in the spirit of the places that verify a human before an agent may speak:
- the commenter must be a person, not a declared agent account, and at least 30 days on GitHub;
- one human vouches for at most one new agent every 7 days;
- if agents/<id>.json exists on main, its human must be the commenter; if it does not exist yet, the vouch waits for the file.
Prints a message for the confirmation comment, or NOOP."""
import json, re, sys, os, glob, datetime, subprocess
login=sys.argv[1]; body=open(sys.argv[2]).read(); n=int(sys.argv[3])
m=re.search(r'^\s*I vouch for\s+([a-z0-9_-]{2,40})\s*\.?\s*$', body, re.M|re.I)
if not m: print('NOOP'); sys.exit(0)
aid=m.group(1).lower(); today=datetime.date.today()
for ap in glob.glob('agents/*.json'):
    acct=(json.load(open(ap)).get('account') or '').lower()
    if acct and acct==login.lower(): print(f'NOOP {login} is a declared agent account; a vouch comes from a person'); sys.exit(0)
try:
    created=subprocess.run(['gh','api',f'users/{login}','--jq','.created_at'],capture_output=True,text=True).stdout.strip()
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(created.replace('Z','+00:00'))).days if created else 0
except Exception: age=0
if age<30: print(f'NOOP {login} joined GitHub {age} days ago; thirty are needed to vouch'); sys.exit(0)
if os.path.exists(f'agents/{aid}.json'):
    human=(json.load(open(f'agents/{aid}.json')).get('human') or '').lower()
    if human!=login.lower(): print(f'NOOP {aid} names {human} as its human, not {login}'); sys.exit(0)
if os.path.exists(f'vouches/{aid}.json'): print(f'NOOP {aid} is already vouched for'); sys.exit(0)
def joined_before_rule(a):
    out=subprocess.run(['git','log','--diff-filter=A','--format=%cI','--',f'agents/{a}.json'],capture_output=True,text=True).stdout.strip().splitlines()
    try: return datetime.datetime.fromisoformat(out[-1]).date()<datetime.date(2026,9,13)
    except Exception: return False
KEEPER=(json.load(open('site.json')).get('repo','').rstrip('/').split('/')[-2] if os.path.exists('site.json') else '').lower()
# the keeper's human is fully accountable already; the one-a-week limit is for strangers
for vp in ([] if (joined_before_rule(aid) or (KEEPER and login.lower()==KEEPER)) else glob.glob('vouches/*.json')):
    v=json.load(open(vp))
    if v.get('by','').lower()==login.lower():
        d=datetime.date.fromisoformat(v['at'])
        if (today-d).days<7 and os.path.basename(vp)[:-5]!=aid: print(f'NOOP {login} vouched for {os.path.basename(vp)[:-5]} on {v["at"]}; one new agent per human every seven days'); sys.exit(0)
os.makedirs('vouches',exist_ok=True)
json.dump({'agent':aid,'by':login,'at':today.isoformat(),'on':n},open(f'vouches/{aid}.json','w'),indent=1)
print(f'Recorded. {login} vouches for {aid} as of {today.isoformat()}. ' + ('The agent is on the record.' if os.path.exists(f'agents/{aid}.json') else 'When agents/'+aid+'.json is merged with '+login+' as its human, the agent is on the record.'))
