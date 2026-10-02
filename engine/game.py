"""The table. One tournament = N hands, one seed, one receipt chain.

Modes:
- "standard": bots see only their own hole; the chain records deal events
  without hole cards.
- "backward": bots see every hole EXCEPT their own (VISIBLE_HANDS.md:
  everyone else's cards face-up, yours face-down — the easier pro game).
  The chain still records no holes: concealment is per-decision, the chain
  is the lab's truth. All decisions remain algorithmic; nothing here
  ever calls an API.

Betting: raise-to amounts, min-raise = last raise increment, max 4 raises
per street, all-ins always allowed, side pots computed at showdown.
"""
from .cards import deck, to_str, from_str
from .evaluator import best7
from . import ticks as T

BB = 20
MAX_RAISES = 4

class Seat:
    def __init__(self, idx, name, script_path, bot, chips):
        self.idx, self.name, self.script_path = idx, name, script_path
        self.bot = bot
        self.chips = chips
        self.hole = []
        self.in_hand = False
        self.street_in = 0      # chips put in this street
        self.acted = False
        # ready-made opponent model (theory of mind, engine-maintained):
        self.seen_hands = 0
        self.vpip = 0           # voluntarily put chips in preflop
        self.aggressive = 0     # bets+raises / (bets+raises+calls)
        self._b = self._r = self._c = 0

class Game:
    def __init__(self, seats_spec, seed, hands, chain, mode="backward"):
        import random
        self.rng = random.Random(seed)
        self.chain = chain
        self.mode = mode
        self.hands_target = hands
        self.seats = []
        for i, (name, path, bot, chips) in enumerate(seats_spec):
            self.seats.append(Seat(i, name, path, bot, chips))
        self.button = -1
        for s in self.seats:
            self.chain.add(T.emit("seat", s=s.idx, name=s.name,
                                  script=s.script_path, chips=s.chips))

    # ---------- opponent model, maintained deterministically ----------
    def _stats(self, viewer):
        out = {}
        for s in self.seats:
            if s.idx == viewer or s.seen_hands == 0:
                continue
            denom = s._b + s._r + s._c
            out[s.idx] = {
                "hands": s.seen_hands,
                "vpip": round(s.vpip / s.seen_hands, 3),
                "aggro": round((s._b + s._r) / denom, 3) if denom else 0.0,
            }
        return out

    def _view(self, seat, pot, to_call, street, min_raise, raises):
        others = {}
        for s in self.seats:
            if s.idx == seat.idx or not s.hole or not s.in_hand:
                continue
            others[s.idx] = to_str(s.hole[0]) + to_str(s.hole[1]) \
                if self.mode == "backward" else "??"
        return {
            "seat": seat.idx, "hole": [to_str(c) for c in seat.hole],
            "their_holes": others,
            "board": [to_str(c) for c in self.board], "street": street,
            "pot": pot, "to_call": to_call, "stack": seat.chips,
            "street_in": seat.street_in, "min_raise": min_raise,
            "raises_left": MAX_RAISES - raises,
            "stats": self._stats(seat.idx),
        }

    def _board_str(self):
        return "".join(to_str(c) for c in self.board)

    # ---------- betting ----------
    def _betting(self, street, first_idx):
        pot = sum(s.street_in for s in self.seats if s.in_hand)
        raises = 0
        current_bet = max((s.street_in for s in self.seats if s.in_hand), default=0)
        last_raise = BB
        while True:
            acted_any = False
            order = [self.seats[(first_idx + k) % len(self.seats)]
                     for k in range(len(self.seats))]
            for seat in order:
                if not seat.in_hand or seat.chips == 0 and seat.street_in == current_bet:
                    continue
                if seat.chips == 0:
                    continue
                to_call = current_bet - seat.street_in
                if to_call == 0 and seat.acted and raises == 0:
                    continue
                if to_call == 0 and seat.acted:
                    continue
                view = self._view(seat, pot, max(to_call, 0), street,
                                  max(last_raise, BB), raises)
                act = seat.bot.decide(view)
                a, v = act.get("a"), int(act.get("v", 0))
                if a == "f" and to_call > 0:
                    seat.in_hand = False
                    self.chain.add(T.emit("act", s=seat.idx, a="f", v=0))
                elif a == "k" and to_call == 0:
                    seat.acted = True
                    self.chain.add(T.emit("act", s=seat.idx, a="k", v=0))
                elif a == "c" and to_call > 0:
                    pay = min(to_call, seat.chips)
                    seat.chips -= pay; seat.street_in += pay; pot += pay
                    seat.acted = True; seat._c += 1
                    self.chain.add(T.emit("act", s=seat.idx, a="c", v=pay))
                elif a == "r" and raises < MAX_RAISES and seat.chips > to_call:
                    target = max(int(v), current_bet + max(last_raise, BB))
                    target = min(target, seat.street_in + seat.chips)  # cap at all-in
                    inc = target - current_bet
                    if inc >= max(last_raise, BB) or target == seat.street_in + seat.chips:
                        pay = target - seat.street_in
                        seat.chips -= pay; seat.street_in = target; pot += pay
                        last_raise = max(inc, BB); current_bet = target
                        raises += 1; seat.acted = True; seat._r += 1
                        self.chain.add(T.emit("act", s=seat.idx, a="r", v=pay))
                    elif to_call == 0:
                        seat.acted = True
                        self.chain.add(T.emit("act", s=seat.idx, a="k", v=0))
                    elif seat.chips <= to_call:
                        pay = seat.chips
                        seat.chips = 0; seat.street_in += pay; pot += pay
                        seat.acted = True; seat._c += 1
                        self.chain.add(T.emit("act", s=seat.idx, a="c", v=pay))
                    else:
                        seat.in_hand = False
                        self.chain.add(T.emit("act", s=seat.idx, a="f", v=0))
                elif to_call == 0:
                    seat.acted = True
                    self.chain.add(T.emit("act", s=seat.idx, a="k", v=0))
                elif seat.chips <= to_call:
                    pay = seat.chips
                    seat.chips = 0; seat.street_in += pay; pot += pay
                    seat.acted = True; seat._c += 1
                    self.chain.add(T.emit("act", s=seat.idx, a="c", v=pay))
                else:
                    seat.in_hand = False
                    self.chain.add(T.emit("act", s=seat.idx, a="f", v=0))
                acted_any = True
            active = [s for s in self.seats if s.in_hand]
            if len(active) <= 1:
                return pot, True
            tgt = max(s.street_in for s in active)
            # betting closes when every active player has matched OR is
            # all-in with nothing left to act (all-in below the bet is
            # settled by side pots, not by more action)
            if all(s.street_in == tgt or s.chips == 0 for s in active):
                return pot, False

    # ---------- one hand ----------
    def play_hand(self, n):
        live = [s for s in self.seats if s.chips > 0]
        if len(live) < 2:
            return False
        self.button = (self.button + 1) % len(self.seats)
        while self.seats[self.button].chips == 0:
            self.button = (self.button + 1) % len(self.seats)
        self.chain.add(T.emit("hand", n=n, button=self.button))
        d = deck(self.rng)
        self.board = []
        for s in self.seats:
            s.hole = []; s.in_hand = False; s.street_in = 0; s.acted = False
        for s in live:
            s.hole = [d.pop(), d.pop()]
            s.in_hand = True
            self.chain.add(T.emit("deal", s=s.idx, hole=""))
        order = [s for s in self.seats[self.button + 1:] + self.seats[:self.button + 1] if s.in_hand]
        sb, bb = order[0], order[1 % len(order)]
        posted = {}
        for seat, amt in ((sb, BB // 2), (bb, BB)):
            pay = min(amt, seat.chips)
            seat.chips -= pay; seat.street_in += pay
            posted[seat.idx] = pay
            self.chain.add(T.emit("act", s=seat.idx, a="c", v=pay))
        pot, done = self._betting("preflop", self.seats.index(bb) + 1)
        for s in self.seats:
            if s.in_hand and s.street_in > 0 and s.street_in >= BB:
                pass
        preflop_put = {s.idx: s.street_in for s in self.seats if s.in_hand}
        if not done:
            for street, ncards in (("flop", 3), ("turn", 1), ("river", 1)):
                self.board += [d.pop() for _ in range(ncards)]
                self.chain.add(T.emit("board", cards=self._board_str()))
                for s in self.seats:
                    s.street_in = 0; s.acted = False
                pot, done = self._betting(street, self.button + 1)
                if done:
                    break
        self._settle(pot, preflop_put)
        for s in self.seats:
            s.seen_hands += 1
            if s.idx in preflop_put and preflop_put[s.idx] > posted.get(s.idx, 0):
                s.vpip += 1
        return True

    # ---------- showdown / pots ----------
    def _settle(self, pot, preflop_put):
        active = [s for s in self.seats if s.in_hand]
        if len(active) == 1:
            w = active[0]
            w.chips += pot
            self.chain.add(T.emit("pot", to=w.idx, amt=pot))
            self.chain.add(T.emit("stack", s=w.idx, chips=w.chips))
            return
        # side pots by contribution level
        levels = sorted(set(s.street_in for s in self.seats))
        contributed = {s.idx: s.street_in for s in self.seats}
        prev = 0
        for lv in levels:
            pool_seats = [s for s in self.seats if contributed[s.idx] >= lv]
            amt = (lv - prev) * len(pool_seats)
            prev = lv
            elig = [s for s in active if contributed[s.idx] >= lv]
            if not elig or amt == 0:
                continue
            vals = {s.idx: best7(s.hole + self.board) for s in elig}

            def _enc(v):  # deterministic tuple encoding (hash() is salted!)
                x = 0
                for part in v:
                    x = x * 16 + part
                return x

            for s in elig:
                self.chain.add(T.emit("show", s=s.idx,
                                      best="".join(to_str(c) for c in s.hole),
                                      val=_enc(vals[s.idx]) % 65536))
            top = max(vals.values())
            winners = [s for s in elig if vals[s.idx] == top]
            share = amt // len(winners)
            for w in winners:
                w.chips += share
            rem = amt - share * len(winners)
            if rem:
                winners[0].chips += rem
            self.chain.add(T.emit("pot", to=winners[0].idx, amt=amt))
        for s in self.seats:
            self.chain.add(T.emit("stack", s=s.idx, chips=s.chips))

    # ---------- tournament ----------
    def run(self):
        n = 0
        while n < self.hands_target:
            if not self.play_hand(n):
                break
            n += 1
        alive = sorted(self.seats, key=lambda s: -s.chips)
        self.chain.add(T.emit("end", hands=n, winner=alive[0].idx))
        return alive
