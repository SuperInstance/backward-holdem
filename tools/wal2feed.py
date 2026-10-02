"""wal2feed: backward-holdem's receipt WAL -> quilt-overhead's feed dialect.

The dance of growth, edge #1 wired today: one repo's receipts become
another repo's live board. The producer owns the adapter (this file);
the consumer owns the dialect contract (quilt-overhead docs/FEED.md).
Both sides carry conformance pins; an edge without a verify pair on
both sides is hearsay, not wiring.

Usage:
  python3 tools/wal2feed.py receipts/wal.jsonl feed.snapshot.json

Dialect (quilt-overhead feed.js adapter contract):
  {"cells": [{"id","name","agent","x","y","doc",
              "deltas": [{"t","kind","size"}]}]}
  kind in {edit, commit, pin, receipt, note}
"""
import json, sys, os

KIND_MAP = {"seat": "note", "hand": "note", "deal": "note", "board": "note",
            "act": "edit", "pot": "receipt", "show": "note", "stack": "receipt",
            "end": "pin"}

def convert(wal_path, out_path):
    ticks = []
    with open(wal_path) as f:
        for line in f:
            line = line.strip()
            if line:
                ticks.append(json.loads(line))
    ref = ticks[-1].get("wal_ref", {})
    recs = [t for t in ticks if "tick" in t]
    # group into cells: one cell per seat + the table itself
    cells = {}
    def cell(cid, name, agent, x, y, doc):
        return {"id": cid, "name": name, "agent": agent, "x": x, "y": y,
                "doc": doc, "deltas": []}
    table = cell("table", "the table", "backward-holdem engine", 0, 0,
                 f"seed {ref.get('seed')} hands {ref.get('hands')} "
                 f"wal_ref {ref.get('wal_ref','')}")
    for r in recs:
        t = r["tick"]
        k = t.get("k")
        seat = t.get("s")
        if seat is not None:
            cid = f"seat{seat}"
            if cid not in cells:
                # ring layout on the unit lattice (feed.v1: x,y in [0,1])
                import math
                ang = (seat / 8) * 6.28318
                cells[cid] = cell(cid, f"seat {seat}", "bot script",
                                  round(0.5 + 0.35 * math.cos(ang), 4),
                                  round(0.5 + 0.35 * math.sin(ang), 4),
                                  "scripted player")
            size = len(json.dumps(t, sort_keys=True))
            cells[cid]["deltas"].append(
                {"t": r["seq"], "kind": KIND_MAP.get(k, "note"), "size": size})
        size = len(json.dumps(t, sort_keys=True))
        table["deltas"].append({"t": r["seq"], "kind": KIND_MAP.get(k, "note"),
                                "size": size})
    all_cells = [table] + list(cells.values())
    snap = {"cells": all_cells,
            "meta": {"source": "backward-holdem/receipts/wal.jsonl",
                     "dialect": "quilt-overhead/feed.v1",
                     "wal_ref": ref.get("wal_ref", ""),
                     "tag": "REAL RECEIPTS (not simulated)"}}
    with open(out_path, "w") as f:
        json.dump(snap, f, indent=1)
    return {"cells": len(all_cells), "deltas": sum(len(c["deltas"]) for c in all_cells),
            "wal_ref": ref.get("wal_ref", "")}

if __name__ == "__main__":
    wal = sys.argv[1] if len(sys.argv) > 1 else "receipts/wal.jsonl"
    out = sys.argv[2] if len(sys.argv) > 2 else "receipts/feed.snapshot.json"
    print(json.dumps(convert(wal, out)))
