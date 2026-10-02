"""Tick memory: perfect session memory in minimal language.

Every event in a tournament is one JSON object on one line. The schema is
STRICT: the parser rejects unknown kinds and wrong field types. Ticks are
what a bot's advisor reads, what the analyzer loops on, what the receipt
chain hashes. Minimal language, type-safe, no library needed to parse.
"""
KINDS = {"seat", "hand", "deal", "board", "act", "pot", "show", "stack", "end"}

_FIELDS = {
    "seat":  {"s": int, "name": str, "script": str, "chips": int},
    "hand":  {"n": int, "button": int},
    "deal":  {"s": int, "hole": str},           # hole: "AhKd" (hidden in receiptless play)
    "board": {"cards": str},                    # "Kd7c2h"
    "act":   {"s": int, "a": str, "v": int},    # a in f/c/k/r/a ; v = chips put in
    "pot":   {"to": int, "amt": int},
    "show":  {"s": int, "best": str, "val": int},
    "pot":   {"to": int, "amt": int},
    "stack": {"s": int, "chips": int},
    "end":   {"hands": int, "winner": int},
}

def emit(kind, **kw):
    spec = _FIELDS[kind]
    t = {"k": kind}
    for f, ty in spec.items():
        if f not in kw:
            raise ValueError(f"tick {kind}: missing field {f}")
        if not isinstance(kw[f], ty) or (ty is int and isinstance(kw[f], bool)):
            raise ValueError(f"tick {kind}: field {f} must be {ty.__name__}")
        t[f] = kw[f]
    extra = set(kw) - set(spec) - {"k"}
    if extra:
        raise ValueError(f"tick {kind}: unknown fields {sorted(extra)}")
    return t

def parse(obj):
    if not isinstance(obj, dict) or "k" not in obj or obj["k"] not in KINDS:
        raise ValueError(f"not a tick: {obj!r}"[:80])
    kind = obj["k"]
    spec = _FIELDS[kind]
    for f, ty in spec.items():
        if f not in obj or not isinstance(obj[f], ty) or (ty is int and isinstance(obj[f], bool)):
            raise ValueError(f"tick {kind}: bad field {f}")
    extra = set(obj) - set(spec) - {"k"}
    if extra:
        raise ValueError(f"tick {kind}: unknown fields {sorted(extra)}")
    return obj
