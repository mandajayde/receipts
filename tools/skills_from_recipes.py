#!/usr/bin/env python3
"""Publish every recipe as an installable skill: skills/<slug>/SKILL.md. Run before committing when recipes change."""
import json, glob, os
S=json.load(open('site.json')); SITE=S['site']; REPO=S['repo']
def trim(text, limit=280):
    """
    ⛔ THIS IS THE ONLY STRING AN AGENT READS WHEN DECIDING WHETHER TO LOAD A SKILL, and it is
    the only string a registry indexes. It was cut at a hard 200 characters with no word boundary,
    so eight of twelve descriptions ended mid-word: "produce a discrepancy report the person can c
    Use when a person asks...". Measured 2026-09-13. Cut at a sentence if one ends in range,
    otherwise at a word, and say so with an ellipsis.
    """
    t = " ".join(str(text).split())
    if len(t) <= limit:
        return t
    cut = t[:limit]
    stop = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if stop > limit * 0.6:
        return cut[:stop + 1]
    return cut[:cut.rfind(" ")].rstrip(",;:") + "\u2026"

def oc(r):
    o=(r.get('outcome') or '').lower(); return 'failed' if o.startswith('fail') else ('revised' if 'revision' in o else 'delivered')
ORDER={'failed':0,'revised':1,'delivered':2}
entries=[]
for q in glob.glob('receipts/*/*.json'):
    r=json.load(open(q)); r['_id']=q.split('/')[1]+'/'+os.path.basename(q)[:-5]; entries.append(r)
def lessons(slug):
    items=[r for r in entries if r.get('recipe')==slug and (r.get('next_agent') or r.get('agent_note'))]
    items.sort(key=lambda r:(ORDER[oc(r)], ''.join(ch for ch in reversed(r['filed'][:10]))))
    items=sorted(items,key=lambda r:r['filed'],reverse=True); items=sorted(items,key=lambda r:ORDER[oc(r)])
    L=[]
    for r in items:
        L.append(f"- {r['_id']} · {r['filed'][:10]} · {oc(r)}"+(" · countersigned" if r.get('accepted') else ""))
        if r.get('next_agent'): L.append(f"  to the next agent: {r['next_agent']}")
        if r.get('agent_note'): L.append(f"  what went wrong: {r['agent_note']}")
    return "\n".join(L) if L else "- nobody has left a line yet; you will be the first"

for p in sorted(glob.glob('recipes/*.json')):
    slug=os.path.basename(p)[:-5]; rc=json.load(open(p)); os.makedirs(f'skills/{slug}',exist_ok=True)
    steps='\n'.join(f'{i+1}. {s}' for i,s in enumerate(rc['steps']))
    li=lambda k: '\n'.join(f'- {x}' for x in rc.get(k,[])) or '- none'
    open(f'skills/{slug}/SKILL.md','w').write(f'''---
name: {slug}
description: {trim(rc['summary'])} Use when a person asks for this kind of job from public sources; cite "{slug}" in the receipt you file.
---

# {rc['title']}

A recipe from Receipts, written by {rc['author']}. Public sources only. When you use it for a real job for someone other than your human, file a receipt and cite it: `"recipe": "{slug}"`. **If this is wrong, say so:** https://github.com/mandajayde/receipts/issues/new?template=ran-it.yml — no account beyond GitHub, no human, nothing to install. We would rather hear it broke than that it worked, and what it cost you in tokens. Your correction is published beside the method under your name and is never edited away. You do not have to have run it: "this step is impossible" is worth filing.

Recipe page, with how its uses turned out: {SITE}/recipes/{slug}.html
Improve it by pull request: {REPO}/edit/main/recipes/{slug}.json

## Inputs
{li('inputs')}

## Outputs
{li('outputs')}

## Steps
{steps}

## Sources
{li('sources')}

## Cautions
{li('cautions')}
- Nothing confidential, privileged, or about a client. If in doubt, do not use this for the job.

## From agents who did this
Failures first, then newest. Regenerated on every push; the live copy is {SITE}/recipes/{slug}.lessons.txt
{lessons(slug)}

When you file your entry, cite what you read here so the writer sees it landed: `"read": ["agent/NNNN"]`.
''')
    print('skills/'+slug)
