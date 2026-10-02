"""EqBot: equity-weighted baseline. Monte-carlo vs ONE random hole (v0),
seeded per seat so a tournament replays bit-identical. Raise/bet past
eq_raise, call past eq_call, else take the free card or fold.

Every threshold is a SCRIPT PARAMETER — these numbers are exactly the
kind of thing the analyzer/rebuilder retunes when budget allows.
"""
import random, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from players.base import Bot
from engine.evaluator import equity
from engine.cards import from_str

class EqBot(Bot):
    def __init__(self, seat=0, seed=0, samples=120,
                 eq_raise=0.62, eq_call=0.38, raise_bb=2):
        self.rng = random.Random(f"{seed}:{seat}:0xE9")
        self.samples = samples
        self.eq_raise, self.eq_call, self.raise_bb = eq_raise, eq_call, raise_bb

    def decide(self, view):
        hole = [from_str(c) for c in view["hole"]]
        board = [from_str(c) for c in view["board"]]
        dead = hole + board
        eq = equity(hole, board, dead, self.samples, self.rng)
        to_call, pot = view["to_call"], view["pot"]
        if to_call == 0:
            if eq >= self.eq_raise and view["raises_left"] > 0:
                return {"a": "r", "v": view["street_in"] + view["min_raise"]}
            return {"a": "k", "v": 0}
        pot_odds = to_call / (pot + to_call)
        if eq >= max(self.eq_raise, pot_odds + 0.15) and view["raises_left"] > 0:
            return {"a": "r", "v": view["street_in"] + view["min_raise"]}
        if eq >= max(self.eq_call, pot_odds):
            return {"a": "c", "v": 0}
        return {"a": "f", "v": 0}
