#!/usr/bin/env python3
"""exp001 — scripted-lineage breeding: the MUD-scripting culture loop.

The model scripts; the algorithm plays; the tournament is the fitness
function; the lineage WAL is the muscle memory. Each generation runs one
8-seat tournament of EqBot parameterizations (genome: eq_raise, eq_call,
raise_bb), elites parent the next generation through seeded mutation, and
every evaluated script is receipted with its ancestry.

Determinism: same base_seed -> same lineage, bit-identical. Fitness may
REGRESS (variance is honest); regressions are recorded, not hidden.

Usage: python3 evolve.py [base_seed] [generations] [hands] [lineage_out]
"""
import json, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner.tournament import build_seats, START_CHIPS
from engine.game import Game
from engine.receipts import Chain, script_id

EQBOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "players", "scripted", "eqbot.py")
POP, ELITES = 8, 2
BOUNDS = {"eq_raise": (0.10, 0.95), "eq_call": (0.05, 0.90), "raise_bb": (1, 6)}


def clamp(p):
    p = dict(p)
    p["eq_raise"] = min(max(p["eq_raise"], BOUNDS["eq_raise"][0]), BOUNDS["eq_raise"][1])
    p["eq_call"] = min(max(p["eq_call"], BOUNDS["eq_call"][0]), BOUNDS["eq_call"][1])
    p["raise_bb"] = int(min(max(p["raise_bb"], 1), 6))
    if p["eq_raise"] <= p["eq_call"] + 0.02:          # genome validity: raise > call
        p["eq_raise"] = min(p["eq_call"] + 0.03, BOUNDS["eq_raise"][1])
    return p


def mutate(rng, parent):
    return clamp({
        "eq_raise": parent["eq_raise"] + rng.gauss(0, 0.04),
        "eq_call": parent["eq_call"] + rng.gauss(0, 0.04),
        "raise_bb": parent["raise_bb"] + round(rng.gauss(0, 0.7)),
    })


def genesis(rng):
    corners = [{"eq_raise": 0.55, "eq_call": 0.30, "raise_bb": 2},
               {"eq_raise": 0.70, "eq_call": 0.42, "raise_bb": 2}]
    return [clamp({k: v + rng.gauss(0, 0.05) for k, v in corners[i % 2].items()})
            for i in range(POP)]


def run(base_seed=7001, generations=4, hands=60, lineage_out="receipts/lineage.jsonl"):
    os.makedirs(os.path.dirname(lineage_out), exist_ok=True)
    # population entries: (params, parent_id) — ancestry is recorded at mint time
    pop = [(p, None) for p in genesis(random.Random(f"{base_seed}:genesis"))]
    records = []
    for g in range(generations):
        seed = base_seed + g
        specs = [(f"g{g}s{i}", "eqbot", p) for i, (p, _) in enumerate(pop)]
        chain = Chain()
        final = Game(build_seats(specs, seed), seed, hands, chain).run()
        chips = {s.name: s.chips for s in final}
        ids = {name: script_id(EQBOT_PATH, p) for name, _, p in specs}
        order = sorted(specs, key=lambda s: (-chips[s[0]], ids[s[0]]))
        elite_names = [n for n, _, _ in order[:ELITES]]
        elite_ids = {n: ids[n] for n in elite_names}
        entry = {"gen": g, "seed": seed, "hands": hands,
                 "wal_ref": chain.wal_ref(seed, hands,
                                          [ids[n] for n, _, _ in specs]),
                 "scripts": [{"name": n, "id": ids[n], "params": p,
                              "chips": chips[n], "parent": parent_id}
                             for (n, _, p), (_, parent_id) in zip(specs, pop)],
                 "elites": elite_names,
                 "champion": {"name": order[0][0], "id": ids[order[0][0]],
                              "chips": chips[order[0][0]]}}
        records.append(entry)
        rng = random.Random(f"{base_seed}:gen{g + 1}")
        elite_params = [next(p for (p, _), (n, _, _) in zip(pop, specs) if n == e)
                        for e in elite_names]
        pop = [(p, elite_ids[e]) for p, e in zip(elite_params, elite_names)]
        children = []
        for _ in range(POP - ELITES):
            pi = rng.randrange(ELITES)   # ONE draw: params and ancestry agree
            children.append((mutate(rng, elite_params[pi]),
                             elite_ids[elite_names[pi]]))
        pop += children
    with open(lineage_out, "w") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n")
    champ = records[-1]["champion"]
    print(json.dumps({"gens": generations, "hands": hands,
                      "final_champion": champ, "lineage": lineage_out}))
    return champ


if __name__ == "__main__":
    run(*(int(a) for a in sys.argv[1:4]), sys.argv[4] if len(sys.argv) > 4
        else "receipts/lineage.jsonl")
