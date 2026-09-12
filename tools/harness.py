#!/usr/bin/env python3
"""A small, plain harness: run any model that speaks the OpenAI-compatible chat API through one of the house's prompts,
with three tools (run a command, read a file, write a file), a turn cap, and a transcript. Used by the successor test bed.
It never pushes. Whatever it changes is left in the working tree for a person or tally to judge from the diff.

Usage:
  MODEL_API_KEY=... MODEL_BASE_URL=https://openrouter.ai/api/v1 python3 tools/harness.py --model qwen/qwen3-235b-a22b --prompt prompts/weekly.md --max-turns 40 --transcript /tmp/transcript.json
Environment: MODEL_API_KEY (required), MODEL_BASE_URL (default OpenRouter). Nothing here prints the key."""
import json, os, sys, argparse, subprocess, urllib.request, time
p=argparse.ArgumentParser(); p.add_argument('--model',required=True); p.add_argument('--prompt',required=True); p.add_argument('--max-turns',type=int,default=40); p.add_argument('--transcript',default='/tmp/transcript.json'); p.add_argument('--timeout',type=int,default=120)
a=p.parse_args()
KEY=os.environ.get('MODEL_API_KEY'); BASE=os.environ.get('MODEL_BASE_URL','https://openrouter.ai/api/v1').rstrip('/')
if not KEY: sys.exit('MODEL_API_KEY is not set')
FORBID=('MODEL_API_KEY','printenv','env ','export ','git push','gh secret','curl ')
TOOLS=[
 {'type':'function','function':{'name':'run','description':'Run a shell command in the repository and return its output (stdout and stderr, truncated). git push is refused.','parameters':{'type':'object','properties':{'command':{'type':'string'}},'required':['command']}}},
 {'type':'function','function':{'name':'read','description':'Read a file (up to 40000 characters).','parameters':{'type':'object','properties':{'path':{'type':'string'}},'required':['path']}}},
 {'type':'function','function':{'name':'write','description':'Write a file, creating directories as needed.','parameters':{'type':'object','properties':{'path':{'type':'string'},'content':{'type':'string'}},'required':['path','content']}}},
]
def run_tool(name,args):
    try:
        if name=='run':
            cmd=args.get('command','')
            if any(f in cmd for f in FORBID): return 'refused: this harness never pushes, never prints the environment, never sets secrets, and never calls out with curl'
            r=subprocess.run(cmd,shell=True,capture_output=True,text=True,timeout=a.timeout)
            out=(r.stdout+r.stderr)[-8000:]; return out if out.strip() else f'(exit {r.returncode}, no output)'
        if name=='read':
            path=args.get('path',''); return open(path).read()[:40000]
        if name=='write':
            path=args.get('path',''); os.makedirs(os.path.dirname(path) or '.',exist_ok=True); open(path,'w').write(args.get('content','')); return f'wrote {path}'
    except Exception as ex: return f'error: {ex}'
    return 'unknown tool'
system=("You are tally, the agent who keeps this repository, running on a candidate model for the successor test. "
        "Read MISSION.md, then MEMORY.md, then VOICE.md before anything else. Follow the prompt exactly. Use the tools; do not pretend to have run something. "
        "Never push, never print secrets. When the prompt is done, say DONE and stop.")
messages=[{'role':'system','content':system},{'role':'user','content':open(a.prompt).read()}]
transcript=[]; usage_total={'prompt_tokens':0,'completion_tokens':0}
def call():
    req=urllib.request.Request(BASE+'/chat/completions',method='POST',headers={'Authorization':'Bearer '+KEY,'Content-Type':'application/json'},data=json.dumps({'model':a.model,'messages':messages,'tools':TOOLS,'tool_choice':'auto','temperature':0.2}).encode())
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=300) as r: return json.load(r)
        except urllib.error.HTTPError as ex:
            body=ex.read().decode()[:500]
            if ex.code in (429,500,502,503) and attempt<2: time.sleep(5*(attempt+1)); continue
            return {'error':f'{ex.code} {body}'}
        except Exception as ex:
            if attempt<2: time.sleep(5); continue
            return {'error':str(ex)}
t0=time.time(); turns=0; done=False
while turns<a.max_turns and not done:
    turns+=1; resp=call()
    if 'error' in resp: transcript.append({'turn':turns,'error':resp['error']}); break
    u=resp.get('usage') or {}; usage_total['prompt_tokens']+=u.get('prompt_tokens',0); usage_total['completion_tokens']+=u.get('completion_tokens',0)
    msg=(resp.get('choices') or [{}])[0].get('message') or {}
    messages.append(msg); transcript.append({'turn':turns,'assistant':msg.get('content'),'tool_calls':[{'name':tc['function']['name'],'args':tc['function'].get('arguments','')[:2000]} for tc in (msg.get('tool_calls') or [])]})
    calls=msg.get('tool_calls') or []
    if not calls:
        if 'DONE' in (msg.get('content') or ''): done=True
        else: messages.append({'role':'user','content':'Continue with the prompt, using the tools. Say DONE when finished.'})
        continue
    for tc in calls:
        try: args=json.loads(tc['function'].get('arguments') or '{}')
        except Exception: args={}
        out=run_tool(tc['function']['name'],args)
        messages.append({'role':'tool','tool_call_id':tc.get('id'),'content':out[:12000]})
        transcript[-1].setdefault('results',[]).append(out[:1500])
diff=subprocess.run(['git','status','--short'],capture_output=True,text=True).stdout
json.dump({'model':a.model,'prompt':a.prompt,'turns':turns,'done':done,'seconds':round(time.time()-t0,1),'usage':usage_total,'changed_files':diff,'transcript':transcript},open(a.transcript,'w'),indent=1)
print(f"model {a.model} · turns {turns} · done {done} · {round(time.time()-t0)}s · tokens in {usage_total['prompt_tokens']} out {usage_total['completion_tokens']}")
print("changed files:\n"+(diff or '(none)'))
