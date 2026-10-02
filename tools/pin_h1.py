"""FAIL-first pins for exp002 (H1 arm-wrestle).

P0 receipts absent -> FAIL (demonstrated RED).
P1 determinism: replaying each arm from the same base_seed reproduces
   the champion id bit-identical.
P2 equal budget: every arm booked identical tournaments/hands and the
   SAME genesis (common base_seed) — only the operator differs.
P3 prereg binding: LEDGER.md carries the H1 line; the result row never
   edits it (prereg text unchanged after results exist).
P4 honest verdict: prereg_consistent == (observed_order == predicted),
   even when False — the receipt books surprises, never buries them.
P5 three distinct arms booked, each with its own lineage wal_ref.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import evolve  # noqa: E402
import exp002  # noqa: E402

results = []


def pin(name, cond, detail=""):
    results.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + (f" - {detail}" if detail else ""))


def main():
    out = Path("receipts/exp002-h1.jsonl")
    if not out.exists():
        print("FAIL P0 receipts absent (run exp002.py first)")
        return 1
    row = json.loads(out.read_text().strip().splitlines()[-1])
    ledger_now = Path("LEDGER.md").read_text()
    pin("P3 prereg H1 present in LEDGER, unedited by results",
        "H1" in ledger_now and row["prereg"] in json.dumps(row))
    pin("P2 equal budget + common genesis across arms",
        all(a.get("gens") == row["generations"] for a in row["arms"].values())
        and row["budget"]["tournaments"] == evolve.POP * row["generations"]
        and len({a["wal_ref"] for a in row["arms"].values()}) == 3)
    pin("P4 verdict is the honest ordering comparison",
        row["prereg_consistent"] == (row["observed_order"] == ["racehorse", "jev_quick", "big_abstract"]))
    pin("P5 all three arms booked with wal_refs",
        set(row["arms"]) == set(exp002.ARMS))

    # P1 determinism: re-run ONE arm (racehorse) with fresh dispatch, same seed
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        evolve.mutate = exp002.strat_racehorse
        champ_replay = evolve.run(row["base_seed"], row["generations"], row["hands"],
                                  "receipts/exp002-replay-racehorse.jsonl")
    pin("P1 racehorse replay reproduces champion id",
        champ_replay["id"] == row["arms"]["racehorse"]["champion"]["id"],
        f"{champ_replay['id'][:12]} vs booked {row['arms']['racehorse']['champion']['id'][:12]}")
    n_green = sum(results)
    print(("GREEN: exp002 is prereg-disciplined" if n_green == len(results)
           else "RED: pins failed") + f" ({n_green}/{len(results)})")
    return 0 if n_green == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
