"""The analyzer/rebuilder seam — where the API budget lives.

The game itself NEVER calls an API: hands run algorithmically. Between
hands (or on a bot's explicit trigger), a player may spend budget to have
an ADVISOR retune its script parameters or rewrite its strategy file.

Backends (the experiment matrix):
  null           — no adaptation (control)
  jev_quick      — cheap judgment calls (typesafe.ai JEV-class): score the
                   last N ticks, propose one parameter delta
  racehorse      — narrow fast models with BLINDERS: each sees only one
                   slice (preflop ranges / bet sizing / opponent stats /
                   bluff frequency), votes a delta; no model sees the
                   whole state — that is the point
  big_abstract   — one strong slow model, full tick dump, free-form advice

PREREG (LEDGER.md, H1): at equal call budget, racehorse > jev_quick >
big_abstract in win-rate per call. Falsifiable. Run it, don't argue it.
"""
class Budget:
    def __init__(self, calls):
        self.calls = calls          # total allowance for the session
        self.spent = 0
        self.log = []               # (hand, backend, ms_or_tokens, delta)

    def spend(self, hand, backend, cost, delta):
        if self.spent >= self.calls:
            return False
        self.spent += cost
        self.log.append({"hand": hand, "backend": backend,
                         "cost": cost, "delta": delta})
        return True

class Advisor:
    backend = "null"
    cost = 0
    def propose(self, view_summary, ticks):
        return None                 # None = no change this window

class NullAdvisor(Advisor):
    backend = "null"

def advisor_matrix(budget_per_seat):
    """The four experiment arms, equal budget each."""
    return {
        "control":    (NullAdvisor(), Budget(0)),
        "jev_quick":  (Advisor(), Budget(budget_per_seat)),
        "racehorse":  (Advisor(), Budget(budget_per_seat)),
        "big_abstract": (Advisor(), Budget(budget_per_seat)),
    }
