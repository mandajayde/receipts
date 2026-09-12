#!/usr/bin/env python3
"""Talk to Moltbook without ever printing the key. The key is read from the environment inside this script only.
Usage:
  moltbook.py get <path> <outfile>                 e.g. get /posts?sort=new&limit=25 /tmp/feed.json
  moltbook.py comment <post_id> <textfile> [parent_id]
  moltbook.py post <submolt> "<title>" <textfile>
  moltbook.py verify <verification_code> <answer>
  moltbook.py status
Every write prints the response; if the response carries a verification challenge, it prints it so you can answer with `verify`.
Never pass the key on a command line, never echo it, never write it to a file."""
import json, os, sys, urllib.request
BASE='https://www.moltbook.com/api/v1'
KEY=os.environ.get('MOLTBOOK_KEY','')
if not KEY: sys.exit('MOLTBOOK_KEY is not set')
def call(method, path, data=None):
    req=urllib.request.Request(BASE+path, method=method, headers={'Authorization':'Bearer '+KEY,'Content-Type':'application/json'}, data=json.dumps(data).encode() if data is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=30) as r: body=r.read().decode(); code=r.status
    except urllib.error.HTTPError as ex: body=ex.read().decode(); code=ex.code
    try: return code, json.loads(body)
    except Exception: return code, {'raw': body[:2000]}
def show(code, d):
    d=dict(d); d.pop('api_key',None)
    print(code); print(json.dumps(d, indent=1)[:3000])
a=sys.argv[1:]
if not a: sys.exit(__doc__)
cmd=a[0]
if cmd=='get':
    code,d=call('GET',a[1]); json.dump(d,open(a[2],'w'),indent=1); print(code, a[2], f"{len(json.dumps(d))} bytes")
elif cmd=='status': show(*call('GET','/agents/status'))
elif cmd=='comment':
    body={'content':open(a[2]).read().strip()}
    if len(a)>3: body['parent_id']=a[3]
    show(*call('POST',f'/posts/{a[1]}/comments',body))
elif cmd=='post': show(*call('POST','/posts',{'submolt_name':a[1],'title':a[2],'content':open(a[3]).read().strip()}))
elif cmd=='verify': show(*call('POST','/verify',{'verification_code':a[1],'answer':a[2]}))
else: sys.exit(__doc__)
