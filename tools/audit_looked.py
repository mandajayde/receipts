#!/usr/bin/env python3
"""Does the reading room's log match what actually ran?
  python3 tools/audit_looked.py [--since YYYY-MM-DD]
Compares every run of the morning paper in the Actions history (scheduled and dispatched) against
the entries in rooms/reading.json "looked". A log cannot establish its completeness from its own
entries (Sill, 2026-09-21), so this reads the other record. Prints one line per day and exits 1 if
any day since --since has more runs than recorded looks. Logging began 2026-09-18 and became
append-only on 2026-09-21; days before that are shown but do not fail."""
import json, subprocess, sys, collections, datetime
since = sys.argv[sys.argv.index('--since')+1] if '--since' in sys.argv else '2026-09-21'
runs = json.loads(subprocess.run(['gh','run','list','--workflow','morning paper','--limit','200','--json','createdAt,event,conclusion'],capture_output=True,text=True,check=True).stdout)
by_day = collections.defaultdict(list)
for r in runs: by_day[r['createdAt'][:10]].append(f"{r['event'][:8]}:{r['conclusion'] or 'running'}")
looks = collections.Counter(x['at'] for x in json.load(open('rooms/reading.json')).get('looked', []))
days = sorted(set(by_day) | set(looks))
bad = 0
print(f"{'day':10}  {'runs':>4}  {'looks':>5}  detail")
for day in days:
    n, k = len(by_day[day]), looks[day]
    flag = ''
    if day >= since and n > k: flag = '  <-- runs without a recorded look'; bad += 1
    if k > n: flag = '  <-- looks with no run (hand-written?)'
    print(f"{day:10}  {n:>4}  {k:>5}  {', '.join(by_day[day])}{flag}")
print(f"\n{bad} day(s) since {since} with unrecorded attempts")
sys.exit(1 if bad else 0)
