"""Tournament runner: build seats, run hands, emit the receipt WAL."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.game import Game
from engine.receipts import Chain, script_id
from players.scripted.rock import Rock
from players.scripted.eqbot import EqBot

START_CHIPS = 2000

def build_seats(seat_specs, seed):
    seats = []
    for i, (name, kind, extra) in enumerate(seat_specs):
        if kind == "rock":
            bot = Rock(**extra)
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "players", "scripted", "rock.py")
        elif kind == "eqbot":
            bot = EqBot(seat=i, seed=seed, **extra)
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "players", "scripted", "eqbot.py")
        else:
            raise ValueError(kind)
        seats.append((name, os.path.normpath(path), bot, START_CHIPS))
    return seats

def run(seed=1, hands=120, out="receipts/wal.jsonl"):
    seats_spec = [
        ("rock_loose", "rock", {"call_cap": 80}),
        ("rock_tight", "rock", {"call_cap": 30}),
        ("eq_loose",   "eqbot", {"eq_raise": 0.55, "eq_call": 0.30}),
        ("eq_tight",   "eqbot", {"eq_raise": 0.70, "eq_call": 0.42}),
    ]
    chain = Chain()
    game = Game(build_seats(seats_spec, seed), seed, hands, chain)
    final = game.run()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    built = build_seats(seats_spec, seed)
    scripts = [script_id(path, extra)
               for (name, path, bot, chips), (n2, k2, extra) in zip(built, seats_spec)]
    ref = chain.wal_ref(seed, hands, scripts)
    with open(out, "w") as f:
        for rec in chain.ticks:
            f.write(json.dumps(rec, sort_keys=True, separators=(",", ":")) + "\n")
        f.write(json.dumps({"wal_ref": ref}, sort_keys=True) + "\n")
    print(json.dumps({"final_stacks": {s.name: s.chips for s in final},
                      "wal_ref": ref}, indent=1))
    return ref

if __name__ == "__main__":
    run(seed=int(sys.argv[1]) if len(sys.argv) > 1 else 1,
        hands=int(sys.argv[2]) if len(sys.argv) > 2 else 120,
        out=sys.argv[3] if len(sys.argv) > 3 else "receipts/wal.jsonl")
