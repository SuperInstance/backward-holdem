"""Rock: the floor. Calls any to_call <= call_cap, checks when free,
folds otherwise. Never raises. Beats nothing but folding; never bleeds
more than its cap."""
from players.base import Bot

class Rock(Bot):
    def __init__(self, call_cap=60):
        self.call_cap = call_cap

    def decide(self, view):
        if view["to_call"] == 0:
            return {"a": "k", "v": 0}
        if view["to_call"] <= self.call_cap:
            return {"a": "c", "v": 0}
        return {"a": "f", "v": 0}
