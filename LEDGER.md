# LEDGER — backward-holdem receipts

## PREREG H1 (the racehorse hypothesis)

**Statement.** At equal API-call budget per session, narrow-fast-blindered
advisors (racehorse) outperform broad-slow-abstract advisors
(big_abstract) in win-rate per unit spend; jev_quick (cheap judgment
calls) lands between. Rationale (Kimi): blinders force each model to
abstract the waveform of the records' groove shape instead of the whole
state — faster, and the narrow job gets done better than one big model
thinking too long and too abstract.

**Metric.** bb/100 per 100 adaptation calls, across seeds ≥ 32.
**Arms.** control (budget 0) / jev_quick / racehorse / big_abstract.
**Falsification.** If big_abstract ≥ racehorse at budgets {8,32,128},
H1 is dead; the ledger records the corpse, not a excuse.

## RED→GREEN log (2026-10-02)

Pins caught, in order — this is why receipts exist:

1. `IndentationError` in evaluator.equity (docstring not indented)
2. P2a FAIL: pin premise was **mathematically impossible** — 7 cards can
   hold a full house OR a flush, never both (a boat spans two ranks, ≤2
   clubs). Pin rewritten to the true complement (flush beats obvious
   pair) with the proof in the comment.
3. `eqbot` seeded rng: `random.Random(tuple)` is not allowed — retried
   as string seed.
4. Betting-loop **infinite hang**: all-in player below the bet never
   satisfied the close condition. Fix: betting closes when every active
   player has matched OR is all-in (side pots settle the rest).
5. `_view` shipped board as concatenated string vs bot contract list;
   `their_holes` crashed on seats dealt out (empty hole list) — visible
   holes now in-hand opponents only.
6. salted `hash()` in show ticks broke cross-process determinism —
   replaced with a deterministic tuple encoding. (This one would have
   silently broken P6 replay; it was caught by authoring review before
   the first full run. Saying so plainly.)

GREEN: 21/21 pins. WAL: seed 20261002, 120 hands, 1235 ticks,
wal_ref `0809402a13c37d70`; script ids bind file+params
(6204075e / 21473017 / ce1bd03e / eced6751).

## First unaided result (control arm only)

eq_tight 640, all others busted, 120 hands. Read: at equal (zero)
adaptation budget, tighter equity thresholds survive longer against
calling stations. No advisor arms have run — that is the point of the
prereg: nobody gets to narrate before the WAL does.

## Receipt conventions

- Every tick chained fnv1a-64, canonical JSON, sort_keys, no whitespace
- wal_ref = rolling chain hash after the last tick; ref binds seed,
  hands, per-seat script ids
- A claim about a run must cite its wal_ref or it is a rumor
  (VISIBLE_HANDS.md, fleet doctrine, applied here)

## exp002 — H1 arm-wrestle, proxy scale (2026-10-03, main-direct)

**What ran.** Three adaptation operators (racehorse / jev_quick /
big_abstract, exp002.py) through the sealed evolve harness, identical
base_seed 7301 ⇒ identical genesis population and tournament seeds per
arm; only the operator differs. Equal budget by construction:
pop 8 × 3 gens × 40 hands × 3 arms. wal_refs per arm:
bfae3075f3c4758f (racehorse), 7cf91462a3c9f2e2 (jev_quick),
1f8a8951c3bc9565 (big_abstract).

**Result.** big_abstract 30500 > racehorse 20200 > jev_quick 15200.
**prereg_consistent = false — booked, not buried.** pins P1–P5 green
(determinism replay, equal-budget, prereg binding, honest verdict,
3 wal_refs; tools/pin_h1.py).

**Honest scope.** This is a PROXY test: fixed harness budget, one seed
family, champion chips as the metric. The prereg's literal terms — bb/100
per 100 adaptation calls, seeds ≥ 32, budgets {8,32,128} — have NOT run.
Under the prereg's own falsification clause, big_abstract ≥ racehorse
kills H1 at the budgets tested; the full sweep is where the corpse is
confirmed or resuscitated. Until then: H1 is WOUNDED at proxy scale, not
dead. receipts/exp002-h1.jsonl. Next: exp003 budget sweep {8,32,128} ×
seeds ≥ 32 (host OOMs at full population — arms serialized, incremental
lineage writes).

**The ah-ha.** The narrative said blinders help; the WAL said the
broad-abstract teleporter won at this scale. Receipts culture means the
WAL outranks the story — we watched ourselves be wrong about our own
hypothesis, cheaply, before betting advisor budget on it. That IS the
living room lamp.
