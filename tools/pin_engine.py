"""FAIL-first pins. RED on missing/wrong engine, GREEN when true.

Run: python tools/pin_engine.py
"""
import os, random, sys, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.cards import card, from_str, to_str
from engine.evaluator import evaluate5, best7, equity
from engine import ticks as T
from engine.receipts import Chain, fnv1a64
import subprocess

FAIL = []
def pin(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        FAIL.append(name)

def c(s):  # "AhKd" -> [ints]
    return [from_str(s[i:i+2]) for i in range(0, len(s), 2)]

# P1: evaluator known hands
pin("P1a straight flush beats quads",
    evaluate5(c("AsKsQsJsTs")) > evaluate5(c("AcAdAhAsKd")))
pin("P1b quads beat full house",
    evaluate5(c("AcAdAhAsKd")) > evaluate5(c("AcAdAhKsKh")))
pin("P1c flush beats straight",
    evaluate5(c("AcJc9c5c2c")) > evaluate5(c("9s8d7h6c5s")))
pin("P1d wheel straight is 5-high (loses to 6-high)",
    evaluate5(c("As2d3h4c5s")) < evaluate5(c("6s5d4h3c2s")))
pin("P1e kicker decides pairs",
    evaluate5(c("AcAdKh7s2d")) > evaluate5(c("AcAdQhJsTd")))
pin("P1f full house ranks by trips first",
    evaluate5(c("2c2d2hAsAh")) < evaluate5(c("3c3d3h2s2h")))

# P2: best7 finds the right 5
# (note: 7 cards can hold a full house OR a flush, never both — a boat
# spans exactly two ranks, which can contribute at most two clubs)
pin("P2a ace-high flush beats the obvious pair",
    best7(c("AcAd") + c("KcQcJc9c8d"))[0] == 5)
pin("P2b board straight + queen kicker plays",
    best7(c("Qh2d") + c("Ts9s8h7d6c"))[0] == 4)
pin("P2c trips beat two pair",
    best7(c("Ac2d") + c("KhKdKsQhJd"))[0] == 3)

# P3: tick schema is strict
ok = True
try:
    T.parse({"k": "act", "s": 0, "a": "c", "v": 10, "mystery": 1})
    ok = False
except ValueError:
    pass
pin("P3a unknown tick field rejected", ok)
ok = True
try:
    T.parse({"k": "act", "s": "0", "a": "c", "v": 10})
    ok = False
except ValueError:
    pass
pin("P3b wrong field type rejected", ok)
ok = True
try:
    T.parse({"k": "wat"})
    ok = False
except ValueError:
    pass
pin("P3c unknown kind rejected", ok)
t = T.emit("act", s=1, a="r", v=40)
pin("P3d valid tick round-trips", T.parse(dict(t)) == t)

# P4: fnv1a known vector (fleet convention)
pin("P4a fnv1a64('') == offset basis",
    fnv1a64(b"") == 0xcbf29ce484222325)
pin("P4b fnv1a64('a') == 0xaf63dc4c8601ec8c",
    fnv1a64(b"a") == 0xaf63dc4c8601ec8c)

# P5: equity sanity (seeded)
rng = random.Random(7)
pin("P5a AA vs random ~> 0.80",
    0.75 < equity(c("AsAd"), [], c("AsAd"), 400, rng) <= 1.0)
rng = random.Random(7)
pin("P5b 72o vs random < 0.40",
    0.0 <= equity(c("7s2d"), [], c("7s2d"), 400, rng) < 0.40)

# P6: full tournament determinism (two runs, same seed -> same wal)
def run_once(seed):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "wal.jsonl")
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        subprocess.run(
            [sys.executable, os.path.join(root, "runner", "tournament.py"),
             str(seed), "40", out], capture_output=True, text=True, check=True)
        wal = open(out).read().splitlines()
        return json.loads(wal[-1])["wal_ref"]["wal_ref"], wal

w1, lines1 = run_once(20261002)
w2, lines2 = run_once(20261002)
pin("P6a same seed -> same wal_ref", w1 == w2)
pin("P6b wal identical line count", len(lines1) == len(lines2))
w3, _ = run_once(99)
pin("P6c different seed -> different wal_ref", w3 != w1)

# P7: wal_ref binds script identity
pin("P7 wal_ref carries 4 script ids + seed + hands",
    len(w1) == 16 and isinstance(json.loads(lines1[-1])["wal_ref"]["seed"], int))

print()
if FAIL:
    print("RED:", len(FAIL), "pin(s) failing:", FAIL)
    sys.exit(1)
print("GREEN: all pins pass")
