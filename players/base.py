"""Bot contract. A bot is a SCRIPT the agent crafts — that is the ExoJ
game. The agent never acts in a hand; its artifact does.

decide(view) -> {"a": "f"|"k"|"c"|"r", "v": int}
  view: hole, their_holes (backward mode: everyone's cards but yours),
  board, street, pot, to_call, stack, street_in, min_raise, raises_left,
  stats — the READY-MADE opponent model. The advisor gets this same
  shape; a big model must never have to re-derive it from raw ticks.

Determinism: a bot may hold rng = random.Random(seed + seat). Nothing in
the decision path may touch wall-clock, network, or unseeded entropy.
"""
class Bot:
    def decide(self, view):
        raise NotImplementedError
