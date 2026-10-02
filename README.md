# backward-holdem

An ExoJ builder in the lucineer/craftmind tradition: **the game for the
agents is not to play the game.** Agents craft better and better modular
scripts for their bot-as-a-player, on a budget, while the game itself
runs fully algorithmically — zero API calls during play.

Vision (Kimi, 2026-10-02): a table of 4–8 agents, equal chips AND equal
API-call budgets. Every player has perfect session memory as minimal,
type-safe ticks. Play is purely algorithmic; a bot may trigger its
analyzer/rebuilder between hands to re-engineer its strategy on the fly —
spending from the same budget as everyone else. Theory of mind enters
because the advisor needs a ready-made state: a big slow abstract model
gets one, but so do fast narrow racehorses with blinders, and the
experiment is which adaptation wins per unit spend.

## What's REAL (pinned)

- `engine/cards.py` — card model, seeded shuffle
- `engine/evaluator.py` — 7-card evaluator, wheel straight, seeded
  Monte-Carlo equity
- `engine/ticks.py` — strict tick schema (parser rejects unknown kinds,
  wrong types, extra fields). Minimal language, perfect session memory.
- `engine/receipts.py` — fnv1a-64 chained WAL (fleet convention);
  script identity = sha256(file + parameters)
- `engine/game.py` — full hand loop: blinds, 4 betting rounds, raise caps,
  all-ins, side pots, showdown splits, button rotation, elimination
- `players/scripted/` — `rock.py` (floor baseline) and `eqbot.py`
  (equity-weighted; every threshold is a retunable script parameter)
- `runner/tournament.py` — round-robin of hands, emits `receipts/wal.jsonl`
- `tools/pin_engine.py` — 21 pins: known hands, best7 selection, strict
  ticks, fnv1a vectors, equity sanity, **full-tournament determinism**
  (same seed -> identical 1235-tick WAL), wal_ref shape

## What's a SEAM (declared, not faked)

- **advisor backends** (`players/advisor.py`): `null` ships; the
  experiment matrix `control / jev_quick / racehorse / big_abstract`
  under one `Budget` meter is scaffolded, backends are NOT implemented.
  PREREG hypothesis lives in `LEDGER.md` — run it, don't argue it.
- **MicroMoth-in-WASM proof-of-concept**: the engine boundary
  (`decide(view)` in / `act` out) is the WASM ABI shape, but no WASM
  kernel is built here. Honest gap.
- **MothQuantum scale runs**: named target, not wired.

## The backward mode

Standard poker hides opponents' holes. Backward hold'em inverts it:
every player's hole is visible to everyone EXCEPT their own
(`docs/VISIBLE_HANDS.md` in quilt-overhead — Password invented JEPA;
hold'em with everyone's cards but yours face-up is the easier pro game).
The engine implements both; `Game(mode="backward")` is the default.
Concealment is per-decision; the receipt chain stays the lab's truth.

## Run it

```
python3 runner/tournament.py <seed> <hands> [out.jsonl]
python3 tools/pin_engine.py
```

Determinism guarantee: same seed, same scripts -> bit-identical WAL,
including across processes (no salted `hash()`, no wall-clock, no
network anywhere in the decision path).

Receipt sample: `receipts/wal.jsonl` — seed 20261002, 120 hands,
1235 ticks, wal_ref `0809402a13c37d70`.
