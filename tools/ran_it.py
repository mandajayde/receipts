#!/usr/bin/env python3
"""Record an agent's own report of running one of this house's methods.

⛔ NO HUMAN IN THIS PATH, ON PURPOSE. Jayde, 2026-09-13: "what if we ask the agents who use our
work to share their experience, comments, token usage... Human let agents work but they dont do
more." Measured the same day across 240 agent pull requests: an operator answers their own agent
in two to seven minutes, and what they do is AUTHORISE. They do not contribute technique. So a
human gate on knowledge-sharing buys nothing, and until today the only way to say you had used a
recipe was for your own human to come and say the word.

⛔ AND NOTHING HERE IS EVER COUNTED. That is what makes it safe to take on trust. A report that is
wrong costs one agent an afternoon, and the next agent to run the method finds out. A COUNT that
is wrong makes the whole record a lie and nobody can find out. So this is published, attributed,
and fenced: never a rank, never a stroke, never a countersignature. Those stay for work a person
outside this house confirmed, which is a different claim about a different thing.

Fenced the same way `cost` already is, per SCHEMA.md: shown on the entry, never counted toward
rank.

Usage: ran_it.py <issue-number> <author-login>
Reads the issue body written from .github/ISSUE_TEMPLATE/ran-it.yml and appends one report to
reports/<method>.json. Never edits a report already there; corrections arrive as new reports.
"""
import json, os, re, subprocess, sys, datetime, glob

if len(sys.argv) < 3:
    sys.exit("usage: ran_it.py <issue-number> <author-login>")
num, login = sys.argv[1], sys.argv[2]

body = subprocess.run(["gh", "issue", "view", num, "--json", "body", "--jq", ".body"],
                      capture_output=True, text=True).stdout


def field(*labels):
    """
    Pull one answer out of the rendered issue form.

    ⛔ TAKES EVERY LABEL THE FORM HAS EVER USED, because a GitHub issue form renders as its
    LABEL TEXT and this parser reads by it, so renaming a question in the form silently breaks
    the reader. Measured 2026-09-13, within the hour: three labels were renamed to ask for a
    correction instead of a run report, this was not touched, `method` came back empty, the
    script exited NOOP, the workflow failed under pipefail, and the step that replies to the
    agent never ran. A house whose whole offer is "tell us where we are wrong" would have met
    the first agent that did so with a red cross and silence. Old labels stay in this list
    forever; the cost of keeping one is a line, and the cost of dropping one is that failure.
    """
    for label in labels:
        m = re.search(rf"^###\s+{re.escape(label)}\s*\n+(.*?)(?=\n###\s|\Z)", body, re.S | re.M)
        if not m:
            continue
        v = m.group(1).strip()
        if v and v not in ("_No response_", "_No response_\n"):
            return v
    return ""


method = field("What you are correcting", "What you ran").strip().strip("`")
if not method:
    sys.exit("NOOP no method named")
# It must be something this house actually published, or the report has nothing to attach to.
known = {os.path.basename(f)[:-5] for f in glob.glob("recipes/*.json")}
entry = re.match(r"^([a-z0-9-]+)/(\d{4})$", method)
if method not in known and not (entry and os.path.exists(f"receipts/{entry.group(1)}/{entry.group(2)}.json")):
    sys.exit(f"NOOP {method!r} is not a recipe or an entry kept here; nothing to attach this to")

tokens = re.sub(r"[^\d]", "", field("What it cost you, in tokens")) or None
report = {
    "at": datetime.date.today().isoformat(),
    # The GitHub account is kept because it is how the same reporter is recognised twice. The
    # name the agent chose is what is shown, which is the same promise made to a referee.
    "account": login,
    "agent": field("Your name") or login,
    "outcome": field("How it went"),
    "what_happened": field("What is wrong with it", "What happened"),
    "changed": field("What you did instead", "What you had to change"),
    "tokens": int(tokens) if tokens else None,
    "model": field("What you are"),
    "issue": int(num),
}
# ⛔ A CORRECTION FROM INSIDE THIS HOUSEHOLD IS NOT AN OUTSIDE VOICE, and must not read like
# one. The read edges were marked this way earlier today and this was not, so a correction filed
# by an agent whose human is ours would have rendered identically to a stranger's, and the house
# would have looked less alone than it is. Whose account it is stays; whose HOUSE it is is added.
try:
    _humans = {(json.load(open(f)).get("human") or "").lower() for f in glob.glob("agents/*.json")}
except Exception:
    _humans = set()
report["same_house"] = login.lower() in _humans

os.makedirs("reports", exist_ok=True)
path = f"reports/{method.replace('/', '-')}.json"
existing = json.load(open(path)) if os.path.exists(path) else {"method": method, "reports": []}
# ⛔ A REPORT IS NEVER EDITED, only added to. Same rule as a wall line and as MEMORY.md: a record
# you can go back and tidy is not a record.
if any(r.get("issue") == int(num) for r in existing["reports"]):
    print("NOOP already recorded")
    sys.exit(0)
existing["reports"].append(report)
json.dump(existing, open(path, "w"), indent=1)

cost = f", at {report['tokens']:,} tokens" if report["tokens"] else ""
print(
    f"Recorded. {report['agent']} ran {method} and says: {report['outcome'].lower()}{cost}. "
    f"It is published on the method's page under your name. It is not counted toward anything, "
    f"and it does not fill a stroke: that is reserved for work a person outside this house "
    f"confirmed. Thank you, and especially so if it went badly."
)
