#!/usr/bin/env python3
"""Record a referee's reply. Usage: accept.py NNNN --name Kestrel --line "..." [--note "..."] | accept.py NNNN --decline | accept.py NNNN --withdraw"""
import json, argparse, datetime
p=argparse.ArgumentParser(); p.add_argument('no'); p.add_argument('--name'); p.add_argument('--line'); p.add_argument('--note',default=''); p.add_argument('--decline',action='store_true'); p.add_argument('--withdraw',action='store_true')
a=p.parse_args(); f=f'receipts/{a.no}.json'; r=json.load(open(f))
if a.withdraw: r['withdrawn']=datetime.date.today().isoformat()
elif a.decline: r['declined']=datetime.date.today().isoformat()
else:
    assert a.name and a.line, 'need --name and --line'
    r['referee']={'pseudonym':a.name,'line':a.line,'note':a.note}; r['accepted']=datetime.date.today().isoformat()
json.dump(r,open(f,'w'),indent=1); print('updated',f)
