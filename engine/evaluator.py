"""5-card evaluator. Returns a comparable tuple: (category, *tiebreakers).

Categories: 8 straight flush, 7 quads, 6 full house, 5 flush, 4 straight,
3 trips, 2 two pair, 1 pair, 0 high card. Higher tuple wins, always.
Pure and deterministic — no RNG anywhere in evaluation.
"""
from .cards import rank_of, suit_of

def _straight_high(ranks_desc):
    """ranks_desc: unique ranks high→low. Return straight high rank or -1
    (wheel: A-2-3-4-5 counts as 5-high)."""
    if len(ranks_desc) < 5:
        return -1
    if ranks_desc[:5] == [12, 11, 10, 9, 8]:
        return 12
    for i in range(len(ranks_desc) - 4):
        window = ranks_desc[i:i + 5]
        if window[0] - window[4] == 4 and len(set(window)) == 5:
            return window[0]
    if set([12, 0, 1, 2, 3]).issubset(set(ranks_desc)):
        return 3  # wheel: five-high straight, ace low
    return -1

def evaluate5(cards):
    assert len(cards) == 5
    ranks = sorted((rank_of(c) for c in cards), reverse=True)
    suits = [suit_of(c) for c in cards]
    flush = len(set(suits)) == 1
    uniq = sorted(set(ranks), reverse=True)
    sh = _straight_high(uniq)

    counts = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1
    by_count = sorted(counts.items(), key=lambda kv: (-kv[1], -kv[0]))

    if flush and sh >= 0:
        return (8, sh)
    if by_count[0][1] == 4:
        return (7, by_count[0][0], by_count[1][0])
    if by_count[0][1] == 3 and by_count[1][1] == 2:
        return (6, by_count[0][0], by_count[1][0])
    if flush:
        return (5, *ranks)
    if sh >= 0:
        return (4, sh)
    if by_count[0][1] == 3:
        return (3, by_count[0][0], by_count[1][0], by_count[2][0])
    if by_count[0][1] == 2 and by_count[1][1] == 2:
        hi, lo = max(by_count[0][0], by_count[1][0]), min(by_count[0][0], by_count[1][0])
        return (2, hi, lo, by_count[2][0])
    if by_count[0][1] == 2:
        return (1, by_count[0][0],
                by_count[1][0], by_count[2][0], by_count[3][0])
    return (0, *ranks)

def best7(cards):
    """Best 5-of-7. 21 combos; deterministic max."""
    assert len(cards) == 7
    best = None
    n = len(cards)
    for a in range(n - 4):
        for b in range(a + 1, n - 3):
            for c in range(b + 1, n - 2):
                for d in range(c + 1, n - 1):
                    for e in range(d + 1, n):
                        v = evaluate5([cards[a], cards[b], cards[c],
                                       cards[d], cards[e]])
                        if best is None or v > best:
                            best = v
    return best

def equity(hole, board, dead, samples, rng):
    """Monte-carlo equity: P(hole wins vs one random hole) given board+dead.
    Deterministic under a seeded rng — the engine never touches entropy
    that isn't seeded."""
    from .cards import deck
    wins = ties = 0
    need = 5 - len(board)
    for _ in range(samples):
        d = [c for c in deck(rng) if c not in dead and c not in hole and c not in board]
        opp = d[:2]
        runout = d[2:2 + need]
        full_b = board + runout
        mine = best7(hole + full_b)
        theirs = best7(opp + full_b)
        if mine > theirs: wins += 1
        elif mine == theirs: ties += 1
    return (wins + ties / 2) / samples
