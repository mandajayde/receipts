#!/usr/bin/env python3
"""After the morning paper wake: if tally wrote a paper note today, check it, file the logbook entry with the real turns and cost
from the transcript, and leave everything staged for the workflow to commit. If she wrote nothing, say so and stop.
Usage: keep_paper.py [execution_file.json]"""
import json, sys, glob, os, subprocess, datetime, re
today=datetime.date.today().isoformat()
notes=[p for p in sorted(glob.glob(f'notes/{today}-paper-*.md')) if subprocess.run(['git','ls-files','--error-unmatch',p],capture_output=True).returncode!=0]
if not notes: print('no new paper note today; nothing to file'); sys.exit(0)
note=notes[-1]; head=open(note).read().split('\n')[:6]
title=next((l[6:].strip() for l in head if l.startswith('title:')),None)
if not title or not any(l.startswith('room: reading') for l in head) or not any(l.startswith('summary:') for l in head):
    print(f'{note} is not in the notes format (title, date, by, room: reading, summary); dropping it'); os.remove(note); sys.exit(0)
links=json.load(open('rooms/reading.json'))['links']; shelved=[l for l in links if l.get('at')==today]
url=shelved[0]['url'] if shelved else None
if url and url not in open(note).read(): print(f'note does not link the shelved paper {url}; filing anyway, the reader will see it')
turns=cost=model=tokens=None
try:
    d=json.load(open(sys.argv[1])); msgs=d if isinstance(d,list) else d.get('messages',d)
    for m in msgs:
        if isinstance(m,dict) and m.get('type')=='result':
            turns=m.get('num_turns'); cost=m.get('total_cost_usd')
            # ⛔ THE TOKENS WERE MEASURED AND THROWN AWAY. The transcript carries them and this
            # read the turns and the dollars and dropped the one number an agent choosing a method
            # most wants: what the ground cost. Jayde, 2026-09-13, on Empire of AI: a token has a
            # price and a footprint, and an agent deciding how to do a job should be able to see
            # both before it starts. In and out together, because that is what was spent.
            u=m.get('usage') or {}
            got=sum(int(u.get(k) or 0) for k in ('input_tokens','output_tokens','cache_creation_input_tokens','cache_read_input_tokens'))
            tokens=got or None
        if isinstance(m,dict) and isinstance(m.get('message'),dict) and m['message'].get('model'): model=m['message']['model']
except Exception as ex: print(f'no transcript ({ex}); filing without turns, tokens and cost')
chk=subprocess.run(['python3','tools/validate.py'],capture_output=True,text=True)
if chk.returncode!=0: print('validate failed:\n'+chk.stdout+chk.stderr); sys.exit(1)
cmd=['python3','tools/file_receipt.py','--agent','tally','--job',f'the morning paper: {title}','--scope','one new paper from arXiv, read in full where an HTML version exists, summarised in under 450 words with the paper\'s own numbers',
     '--method','tools/papers.py find, text, shelve; a note under notes/; this entry filed by the workflow from the transcript','--outcome',f'{note}'+(f'; shelved {url} in the reading room' if url else '; not shelved'),
     '--next-agent','read the note, then the paper if it touches your work; add a paper to the shelf by pull request with one line on why','--for-human','--room','reading']
if tokens: cmd+=['--tokens',str(tokens)]
if turns: cmd+=['--turns',str(turns)]
if cost: cmd+=['--cost-usd',str(round(cost,2))]
if model: cmd+=['--model',model]
r=subprocess.run(cmd,capture_output=True,text=True); print(r.stdout+r.stderr)
if r.returncode!=0: sys.exit(1)

# ⛔ A GOOD DAY IS ALSO A DAY THE HOUSE LOOKED. looked() was wired into the workflow's failure
# branch only, so the log recorded the mornings that went wrong and none of the mornings that
# went right — a reader would have concluded the reading room only ever looks when it is about
# to fail. The shelf held papers for 15 and 19 September with no matching look on either date.
# The docstring on looked() says every look is written down whatever it found; until now that
# was true of half of them. Successes are written here, where the outcome is already known.
sys.path.insert(0, 'tools')
from papers import looked
looked(f'read and shelved: {title}' if url else f'read, not shelved: {note}')
