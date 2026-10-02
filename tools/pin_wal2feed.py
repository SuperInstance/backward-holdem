"""FAIL-first pin on the wal2feed adapter's dialect conformance.

An adapter that emits a shape the consumer can't render is worse than
no adapter: it fails silently in someone else's repo. This pin holds
backward-holdem's producer side to quilt-overhead's feed.v1 contract:
  {cells: [{id,name,agent,x,y in [0,1],doc,deltas:[{t,kind,size}]}]}
  kind in {edit,commit,pin,receipt,note}; deltas time-ordered;
  meta carries wal_ref matching the source WAL + REAL tag.

Run: python3 tools/pin_wal2feed.py   (RED until GREEN, both witnessed)
"""
import json, subprocess, sys, os, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WAL = os.path.join(ROOT, "receipts", "wal.jsonl")
KINDS = {"edit", "commit", "pin", "receipt", "note"}
FAIL = []

def pin(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        FAIL.append(name)

with tempfile.TemporaryDirectory() as d:
    out = os.path.join(d, "snap.json")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "wal2feed.py"),
                        WAL, out], capture_output=True, text=True)
    pin("W1 adapter runs clean on the real WAL", r.returncode == 0 and os.path.exists(out))
    if r.returncode != 0:
        print(r.stderr[-500:])
        sys.exit(1)
    snap = json.load(open(out))
    src_wal_ref = json.loads(open(WAL).read().strip().splitlines()[-1])["wal_ref"]["wal_ref"]

cells = snap.get("cells", [])
pin("W2 snapshot has cells", isinstance(cells, list) and len(cells) >= 2)
ok = all(set(c) >= {"id", "name", "agent", "x", "y", "doc", "deltas"} for c in cells)
pin("W3 every cell carries the 6 contract fields", ok)
ok = all(isinstance(c["x"], (int, float)) and 0.0 <= c["x"] <= 1.0 and
         isinstance(c["y"], (int, float)) and 0.0 <= c["y"] <= 1.0 for c in cells)
pin("W4 x,y are lattice coords in [0,1]", ok)
ok = all(all(set(dd) == {"t", "kind", "size"} and dd["kind"] in KINDS
             for dd in c["deltas"]) for c in cells)
pin("W5 deltas use only the five fleet verbs", ok)
ok = all(all(dd["t"] <= ee["t"] for dd, ee in zip(c["deltas"], c["deltas"][1:]))
         for c in cells)
pin("W6 deltas time-ordered per cell", ok)
pin("W7 every WAL tick became a delta somewhere",
    sum(len(c["deltas"]) for c in cells) >= 1235)
meta = snap.get("meta", {})
pin("W8 meta.wal_ref matches the source WAL", meta.get("wal_ref") == src_wal_ref)
pin("W9 tagged REAL, not SIMULATED", "REAL" in str(meta.get("tag", "")))

print()
if FAIL:
    print("RED:", len(FAIL), "pin(s) failing:", FAIL)
    sys.exit(1)
print("GREEN: wal2feed conforms to quilt-overhead/feed.v1")
