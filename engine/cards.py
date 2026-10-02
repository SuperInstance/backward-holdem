"""Cards: 52 integers. rank 0..12 (2..A), suit 0..3.

String form is exactly two chars: rank char (23456789TJQKA) + suit char
(cdhs). Minimal language, parseable without a library — the tick log and
the script files both speak this form.
"""
RANKS = "23456789TJQKA"
SUITS = "cdhs"

def card(rank, suit):
    assert 0 <= rank < 13 and 0 <= suit < 4
    return rank * 4 + suit

def rank_of(c): return c // 4
def suit_of(c): return c % 4

def to_str(c):
    return RANKS[rank_of(c)] + SUITS[suit_of(c)]

def from_str(s):
    assert len(s) == 2 and s[0] in RANKS and s[1] in SUITS
    return card(RANKS.index(s[0]), SUITS.index(s[1]))

def deck(rng):
    d = [card(r, s) for r in range(13) for s in range(4)]
    rng.shuffle(d)
    return d
