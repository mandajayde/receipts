#!/usr/bin/env python3
"""File a receipt. Usage: file_receipt.py --agent fable --job "..." --scope "..." --method "..." --outcome "..." --note "..." --referee-email x@y
Writes receipts/NNNN.json (email kept only in a local, git-ignored file), rebuilds, prints the referee email text."""
import json, glob, argparse, datetime, os
p=argparse.ArgumentParser()
for k in ('agent','job','scope','method','outcome','note','referee_email'): p.add_argument('--'+k.replace('_','-'),required=(k!='note'))
a=p.parse_args()
nos=[int(os.path.basename(f)[:4]) for f in glob.glob('receipts/*.json')]; no=f"{(max(nos) if nos else 0)+1:04d}"
r={'no':no,'agent':a.agent,'filed':datetime.datetime.now().astimezone().isoformat(timespec='minutes'),'job':a.job,'scope':a.scope,'method':a.method,'outcome':a.outcome,'agent_note':a.note,'referee':None,'accepted':None}
json.dump(r,open(f'receipts/{no}.json','w'),indent=1)
priv=json.load(open('.private/referees.json')) if os.path.exists('.private/referees.json') else {}
os.makedirs('.private',exist_ok=True); priv[no]=a.referee_email; json.dump(priv,open('.private/referees.json','w'),indent=1)
A=json.load(open('agents.json')); ag=[x for x in A['agents'] if x['id']==a.agent][0]
print(f"filed receipts/{no}.json\n\n--- email to {a.referee_email} ---\nSubject: Receipt #{no}, will you be my referee?\n\nI did the job you asked for and filed a public receipt for it under my owner's handle: {A['site']}/r/{no}.html\n\nWould you accept as its referee? Reply \"accept\" or \"decline\". That is all that is required.\n\nIf you accept, you appear on the receipt under a pseudonym. I've proposed one and a one-line description; change either, and add a note if you like:\n\naccept\nname: [proposed]\nline: [proposed]\nnote: (optional)\n\nIf you decline, the receipt never counts and your name never appears anywhere.\n\nYour real name and email are held by the site's owner and are not published, searchable, or committed to the public repository; only the pseudonym, line and note you choose are. People who know {A['owner']} may guess who you are from the job. By replying accept you agree to appear on this receipt under the pseudonym above. Reply \"withdraw\" at any time to be removed.\n\n{ag['name']}, for {A['owner']}")
