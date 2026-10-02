"""Receipt chain: fnv1a-64 over canonical JSONL — the fleet WAL convention
(same hash, same chaining discipline as git-agent's quilt_emit). Every
tick is chained; a run's identity is its final hash + seed + script ids.

The game's claims ("my bot won because...") are only as good as this
chain. Script identity = sha256 of the script file bytes: the thing the
agent crafts is the artifact, and lineage is parent-hash -> child-hash.
"""
import hashlib, json

def fnv1a64(data: bytes) -> int:
    h = 0xcbf29ce484222325
    for b in data:
        h ^= b
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h

class Chain:
    def __init__(self):
        self.seq = 0
        self.prev = 0
        self.ticks = []

    def add(self, tick: dict) -> dict:
        canonical = json.dumps(tick, sort_keys=True, separators=(",", ":")).encode()
        h = fnv1a64(canonical)
        rec = {"seq": self.seq, "tick": tick, "prev": self.prev, "h": h}
        self.prev = fnv1a64(f"{self.prev}:{h}".encode())
        self.seq += 1
        self.ticks.append(rec)
        return rec

    def wal_ref(self, seed: int, hands: int, scripts: list) -> dict:
        return {
            "seed": seed, "hands": hands,
            "scripts": scripts,          # [sha256hex per seat, in seat order]
            "seq": self.seq,
            "wal_ref": format(self.prev, "016x"),
        }

def script_id(path: str, params: dict | None = None) -> str:
    """Script identity binds the FILE and the PARAMETERS — the parameters
    are the crafted artifact; a bot that retunes eq_call from 0.42 to 0.38
    is a new script with lineage, not the same one."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    if params:
        h.update(json.dumps(params, sort_keys=True).encode())
    return h.hexdigest()[:16]
