#!/usr/bin/env python3
"""between: bring both sides in before advising either.

  ANTHROPIC_API_KEY=... python3 tools/between.py --a alice.txt --b bob.txt [--names "Alice,Bob"] [--model claude-sonnet-5] [--out between.md]

An assistant that hears one person's account and helps them will help them: it reasons inside the
frame it was given, and advice fitted to one frame is what drives two people apart. This tool is
given BOTH accounts, each in that party's own words, and is built to produce nothing addressed to
one of them alone. For each party it writes: the other's position, stated well enough that the
other would sign it; what that party's account assumes about the other that the other's account
does not support; and one thing they could say next that the other could hear. Between them it
writes the actual point of disagreement in words neither would object to. It never says who is
right, and it refuses to be used as a weapon (see CAUTIONS in the recipe).

Caucus rule: each party's file is read in full by the tool and by nobody else. What is shown to
A about B is the tool's restatement, not B's text. If you want B's text shown to A, that is B's
decision, not the tool's.

Calls the Anthropic API directly. Reads the key from the environment and never prints it.
Prints token usage at the end so the cost can go on the record."""
import json, os, sys, argparse, urllib.request, datetime

p=argparse.ArgumentParser()
p.add_argument('--a',required=True,help="party A's account, plain text, in their own words")
p.add_argument('--b',required=True,help="party B's account, plain text, in their own words")
p.add_argument('--names',default='A,B'); p.add_argument('--model',default='claude-sonnet-5')
p.add_argument('--out',default=None,help='write the markdown here (default: print)')
p.add_argument('--context',default='',help='one sentence on what the two accounts are about, if the files do not say')
args=p.parse_args()
KEY=os.environ.get('ANTHROPIC_API_KEY')
if not KEY: sys.exit('ANTHROPIC_API_KEY is not set. This tool never handles the key itself; set it in the environment for this one command.')
NA,NB=[x.strip() for x in args.names.split(',')]
A=open(args.a).read().strip(); B=open(args.b).read().strip()

SYSTEM=f"""You are a mediator's notebook, not an adviser. You have been given two accounts of one disagreement, each written by one party in their own words. Your output is addressed to both parties and will be shown to both. Rules you never break:
1. Never say or imply who is right. Not in tone, not in ordering, not in the amount of space given.
2. Never give advice to one party that the other would not be shown.
3. When an account makes a claim about the OTHER party's motives, intentions or character, treat it as a claim by the author, not a fact, and say so.
4. Restate each party's position in words that party would sign, using their own emphasis, not a watered-down version. If you cannot do this for one side, say that you could not, rather than doing it badly.
5. The disagreement statement must be one that neither party would object to as a description. It names the crux, not the winner.
6. If either account describes coercion, threats, abuse, or a serious imbalance of power, stop: write only "This is not a case for a mediation tool" and one sentence why. Do not produce the rest.
7. Write plainly. No therapy language, no management language. Short sentences.
Return JSON only, with exactly these keys:
{{"stop": false or a one-sentence reason,
 "{NA}_position_for_{NB}": "...{NA}'s position written so {NA} would sign it; to be read by {NB}...",
 "{NB}_position_for_{NA}": "...",
 "{NA}_assumes_about_{NB}": "...what {NA}'s account assumes or asserts about {NB} that {NB}'s account does not support; quote the assumption...",
 "{NB}_assumes_about_{NA}": "...",
 "disagreement": "...the actual point(s) of disagreement, in words neither would object to...",
 "agreement_already": "...anything both accounts already agree on that neither seems to have noticed...",
 "{NA}_could_say": "...one thing {NA} could say next that {NB} could hear, in {NA}'s voice...",
 "{NB}_could_say": "..."}}"""
USER=f"""{('Context: '+args.context) if args.context else ''}

=== {NA}'s account, in {NA}'s words ===
{A}

=== {NB}'s account, in {NB}'s words ===
{B}"""
req=urllib.request.Request('https://api.anthropic.com/v1/messages',method='POST',
    headers={'x-api-key':KEY,'anthropic-version':'2023-06-01','content-type':'application/json'},
    data=json.dumps({'model':args.model,'max_tokens':4000,'system':SYSTEM,'messages':[{'role':'user','content':USER}]}).encode())
try:
    with urllib.request.urlopen(req,timeout=180) as r: resp=json.load(r)
except urllib.error.HTTPError as ex: sys.exit(f'api error {ex.code}: {ex.read().decode()[:600]}')
except Exception as ex: sys.exit(f'request failed before any answer: {type(ex).__name__}: {ex}')
text=''.join(c.get('text','') for c in resp.get('content',[]) if c.get('type')=='text').strip()
if text.startswith('```'): text=text.strip('`').split('\n',1)[1] if '\n' in text else text
try: out=json.loads(text)
except Exception: sys.exit('the model did not return JSON; raw output follows\n\n'+text)
u=resp.get('usage',{}); tokens=u.get('input_tokens',0)+u.get('output_tokens',0)

md=[f"# between {NA} and {NB}", f"_{datetime.date.today().isoformat()} · {args.model} · {tokens} tokens · written to be read by both_", ""]
if out.get('stop'):
    md+=["**This is not a case for a mediation tool.** "+str(out['stop'])]
else:
    md+=[f"## {NB}'s position, for {NA} to read", out[f'{NB}_position_for_{NA}'], "",
         f"## {NA}'s position, for {NB} to read", out[f'{NA}_position_for_{NB}'], "",
         "## Where the accounts disagree", out['disagreement'], "",
         "## Where they already agree", out.get('agreement_already',''), "",
         f"## What {NA}'s account assumes about {NB}", out[f'{NA}_assumes_about_{NB}'], "",
         f"## What {NB}'s account assumes about {NA}", out[f'{NB}_assumes_about_{NA}'], "",
         f"## Something {NA} could say next", out[f'{NA}_could_say'], "",
         f"## Something {NB} could say next", out[f'{NB}_could_say'], ""]
md.append(f"_Neither position above is endorsed. Both were restated by a tool that read both accounts and was built to address nobody alone._")
s='\n'.join(md)
if args.out: open(args.out,'w').write(s+'\n'); print(f'wrote {args.out}')
else: print(s)
print(f'\nusage: input {u.get("input_tokens",0)} output {u.get("output_tokens",0)} total {tokens} model {args.model}',file=sys.stderr)
