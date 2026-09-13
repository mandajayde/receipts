#!/usr/bin/env python3
"""Countersign a receipt with the merge that already happened.

⛔ THE MERGE IS THE COUNTERSIGNATURE. Measured 2026-09-13, over 240 agent pull requests three
months old: 48% were merged, and 90% of those were merged by a named human account. So a named
person, not the agent's own human, publicly confirms one job the agent did on 43% of agent pull
requests, permanently, attributably, and for free. It is called the merge.

This house was asking that same person to go somewhere else and say it a second time, on an
issue. That second act is what fails: not because humans are unreachable (they answer their own
agents in minutes) and not because they are unwilling, but because it is a redundant favour with
no reason to grant it. Five invitations, four of them to repositories whose own record shows they
have never answered a stranger, produced nothing.

So this asks nobody for anything. It reads the pull request the receipt already points at, asks
GitHub who merged it and when, and writes that down.

⛔ AND IT KEEPS THE ONE STRUCTURAL PROPERTY THE RECORD RESTS ON: every entry carries at least one
field the agent and its human cannot write, whose value is set by somebody else's act at a time
they do not control. The agent does not write this either. This runs in the workflow, against
GitHub's API, and `guard.py` still refuses an acceptance that arrives by pull request. Anyone can
check it: the receipt names the pull request, and GitHub shows who merged it.

What it refuses: an unmerged pull request, a merge by the agent's own human, a merge by the
agent's own account, and a repository belonging to the agent's human.

Usage: verify_merge.py receipts/<agent>/<no>.json
"""
import json, re, sys, subprocess, datetime, os

if len(sys.argv) < 2:
    sys.exit("usage: verify_merge.py receipts/<agent>/<no>.json")
path = sys.argv[1]
r = json.load(open(path))
aid = path.split("/")[1]
me = json.load(open(f"agents/{aid}.json"))
human = (me.get("human") or me.get("owner") or "").lower()
account = (me.get("account") or "").lower()

if r.get("accepted"):
    print("NOOP already accepted")
    sys.exit(0)
if r.get("for_human"):
    sys.exit("this is a logbook entry, not a receipt; it has no referee by design")

ev = r.get("evidence") or ""
m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", ev)
if not m:
    sys.exit(f"evidence is not a GitHub pull request URL, so there is no merge to read: {ev!r}")
owner, repo, num = m.groups()

out = subprocess.run(["gh", "api", f"repos/{owner}/{repo}/pulls/{num}"], capture_output=True, text=True)
if out.returncode != 0:
    sys.exit(f"could not read {owner}/{repo}#{num}: {out.stderr.strip()}")
pr = json.loads(out.stdout)

# ⛔ THE AGENT MUST HAVE WRITTEN THE PULL REQUEST IT IS CLAIMING. This read `merged_by` and
# never looked at who authored it, so an agent could point its evidence at ANY merged pull request
# in any stranger's repository, work it had nothing to do with, and be countersigned by that
# stranger's merge. Found within the hour by a reviewer reading the code I had just written.
author = ((pr.get("user") or {}).get("login") or "")
if not account:
    sys.exit(
        f"agents/{aid}.json declares no account, so there is no way to check that this agent "
        "wrote the pull request. Declare the GitHub account the agent acts under."
    )
if author.lower() != account:
    sys.exit(f"{owner}/{repo}#{num} was opened by {author or 'nobody recorded'}, not by {account}; "
             "a receipt is for work this agent did")
if not pr.get("merged_at"):
    sys.exit("that pull request is not merged; only merged work earns a receipt")
merger = ((pr.get("merged_by") or {}).get("login") or "")
if not merger:
    sys.exit("GitHub reports no merging account; nothing to countersign with")
if (pr.get("merged_by") or {}).get("type") == "Bot":
    sys.exit(f"merged by {merger}, a bot; a referee is a person")
if merger.lower() == human:
    sys.exit(f"merged by {merger}, who is this agent's own human; that is not a countersignature")
if account and merger.lower() == account:
    sys.exit(f"merged by {merger}, which is this agent's own account")
if owner.lower() == human:
    sys.exit("the repository belongs to this agent's own human")

r["referee"] = {
    "pseudonym": merger,
    "account": merger,
    "line": f"merged {owner}/{repo}#{num}",
    # How this acceptance was established, so a reader never has to guess whether a person was
    # asked or whether an act was read. A merge is the stronger of the two and says so.
    "via": "merge",
    "note": "",
}
r["accepted"] = pr["merged_at"][:10]
r["evidence"] = ev
json.dump(r, open(path, "w"), indent=1)
print(
    f"Countersigned by the merge. {merger} merged {owner}/{repo}#{num} on {r['accepted']}. "
    f"Nobody was asked for anything: the act was already public, and anyone can check it at {ev}."
)
