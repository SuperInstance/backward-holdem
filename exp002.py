"""exp002 — H1 arm-wrestle: racehorse vs jev_quick vs big_abstract.

Prereg (backward-holdem LEDGER.md, launch day, NOT edited here): at equal
call budget, racehorse > jev_quick > big_abstract per unit spend.

Method: the sealed exp001 harness is reused EXACTLY — evolve.run() is
called with identical base_seed (same genesis population + tournament
seeds for every arm; only the adaptation operator differs, swapped via
module-global dispatch, evolve.py untouched). Equal budget is by
construction: same pop, elites, generations, hands, code path.
Each arm's lineage is receipted to its own file (wal_ref per arm).
The verdict is booked honestly — a surprising ordering books
prereg_consistent=false and is still committed. That is what prereg is.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evolve  # noqa: E402  (sealed exp001 module — imported, not modified)


def strat_racehorse(rng, parent):
    """narrow/fast/blindered: ONE param pushed toward aggression."""
    p = dict(parent)
    key = rng.choice(["eq_raise", "raise_bb"])
    if key == "eq_raise":
        p[key] = p[key] + rng.uniform(0.02, 0.10)
    else:
        p[key] = p[key] + rng.choice([1, 1, 2])
    return evolve.clamp(p)


def strat_jev_quick(rng, parent):
    """quick generalist: ALL params nudged small, every child."""
    return evolve.clamp({
        "eq_raise": parent["eq_raise"] + rng.gauss(0, 0.05),
        "eq_call": parent["eq_call"] + rng.gauss(0, 0.05),
        "raise_bb": parent["raise_bb"] + round(rng.gauss(0, 0.8)),
    })


def strat_big_abstract(rng, parent):
    """broad abstract: slow structural teleports, half the child slots."""
    p = dict(parent)
    if rng.random() < 0.5:
        p["raise_bb"] = rng.randint(1, 6)
    if rng.random() < 0.5:
        p["eq_raise"] = rng.uniform(0.10, 0.95)
        p["eq_call"] = rng.uniform(0.05, min(0.90, p["eq_raise"] - 0.05))
    return evolve.clamp(p)


ARMS = {"racehorse": strat_racehorse, "jev_quick": strat_jev_quick,
        "big_abstract": strat_big_abstract}


def main(base_seed=7301, generations=4, hands=60):
    ledger = Path("LEDGER.md").read_text()
    assert "H1" in ledger, "prereg H1 must exist in LEDGER before results"
    arms = {}
    for name, strategy in ARMS.items():
        evolve.mutate = strategy  # module-global dispatch inside evolve.run
        champ = evolve.run(base_seed, generations, hands,
                           f"receipts/exp002-lineage-{name}.jsonl")
        rows = [json.loads(l) for l in open(f"receipts/exp002-lineage-{name}.jsonl")]
        arms[name] = {"champion": champ,
                      "wal_ref": rows[-1]["wal_ref"], "gens": len(rows)}
    order = sorted(arms, key=lambda k: -arms[k]["champion"]["chips"])
    predicted = ["racehorse", "jev_quick", "big_abstract"]
    row = {"experiment": "exp002-h1", "base_seed": base_seed,
           "generations": generations, "hands": hands,
           "budget": {"pop": evolve.POP, "elites": evolve.ELITES,
                      "tournaments": evolve.POP * generations, "hands_each": hands,
                      "note": "identical for all arms; same genesis via same base_seed"},
           "arms": arms, "observed_order": order,
           "prereg": "racehorse > jev_quick > big_abstract at equal budget",
           "prereg_consistent": order == predicted}
    with open("receipts/exp002-h1.jsonl", "a") as f:
        f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(row, indent=1))
    return row


if __name__ == "__main__":
    args = [int(a) for a in sys.argv[1:4]]
    main(*args[:1], **({"generations": args[1]} if len(args) > 1 else {}),
         **({"hands": args[2]} if len(args) > 2 else {}))
