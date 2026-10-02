#!/usr/bin/env python3
"""FAIL-first pins for exp001 scripted-lineage breeding.

The muscle-memory contract: a lineage WAL that (1) replays bit-identical
under the same base seed, (2) has no orphan ancestry, (3) receipted every
evaluated script, (4) kept every genome inside its bounds, (5) actually
minted new script identities (mutation is real, not theater).

Run: python3 tools/pin_evolve.py [lineage.jsonl]
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
LINEAGE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "receipts/lineage.jsonl"
BOUNDS = {"eq_raise": (0.10, 0.95), "eq_call": (0.05, 0.90), "raise_bb": (1, 6)}

fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" - {detail}" if detail else ""))
    if not cond:
        fails.append(name)


if not LINEAGE.exists():
    print(f"FAIL L0 lineage file absent: {LINEAGE} — run evolve.py first")
    sys.exit(1)

rows = [json.loads(l) for l in LINEAGE.read_text().strip().splitlines()]
check("L0 lineage parses, generations recorded", len(rows) >= 2,
      f"{len(rows)} generations")

# determinism: same base seed, fresh run, same champion
with tempfile.TemporaryDirectory() as td:
    out = Path(td) / "lineage.jsonl"
    subprocess.run([sys.executable, str(ROOT / "evolve.py"),
                    str(rows[0]["seed"]), str(len(rows)), str(rows[0]["hands"]),
                    str(out)], check=True, capture_output=True)
    replay = [json.loads(l) for l in out.read_text().strip().splitlines()]
check("L1 same base seed replays the same champion (id + chips)",
      len(replay) == len(rows) and
      replay[-1]["champion"] == rows[-1]["champion"],
      f"live={rows[-1]['champion']['id'][:12]} replay={replay[-1]['champion']['id'][:12]}")

by_id = {s["id"] for r in rows for s in r["scripts"]}
orphans = [s["id"][:12] for r in rows[1:]
           for s in r["scripts"]
           if s["parent"] is not None and s["parent"] not in by_id]
check("L2 no orphan ancestry — every parent id exists", not orphans,
      f"{len(orphans)} orphans")

coverage = all(s.get("chips") is not None and s.get("id") and s.get("params")
               for r in rows for s in r["scripts"])
check("L3 every evaluated script receipted (id + params + chips)", coverage)

in_bounds = all(
    BOUNDS["eq_raise"][0] <= s["params"]["eq_raise"] <= BOUNDS["eq_raise"][1]
    and BOUNDS["eq_call"][0] <= s["params"]["eq_call"] <= BOUNDS["eq_call"][1]
    and BOUNDS["raise_bb"][0] <= s["params"]["raise_bb"] <= BOUNDS["raise_bb"][1]
    and s["params"]["eq_raise"] > s["params"]["eq_call"] + 0.02
    for r in rows for s in r["scripts"])
check("L4 every genome inside bounds with raise > call", in_bounds)

distinct = len({s["id"] for r in rows for s in r["scripts"]})
check("L5 mutation mints new identities (>=3 distinct scripts)", distinct >= 3,
      f"{distinct} distinct")

def ref_of(r):
    w = r.get("wal_ref")
    return w.get("wal_ref") if isinstance(w, dict) else w


refs = [ref_of(r) for r in rows]
check("L6 every generation carries a unique wal_ref",
      all(refs) and len(set(refs)) == len(refs), f"{len(set(refs))} unique")

parents_recorded = sum(1 for r in rows[1:] for s in r["scripts"] if s["parent"])
check("L7 children record their parent (lineage is a graph, not a log)",
      parents_recorded > 0, f"{parents_recorded} parent links")

print("GREEN: exp001 lineage is muscle memory (deterministic, bounded, graphed)"
      if not fails else f"RED: {len(fails)} pin(s) tripped")
sys.exit(1 if fails else 0)
