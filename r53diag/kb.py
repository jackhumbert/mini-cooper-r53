"""Access to the knowledge base in ../kb (module map, safety policy, catalogs, translations)."""
from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "kb"

READ, CONFIRM, BLOCKED = "read", "confirm", "blocked"


@dataclass(frozen=True)
class Module:
    key: str
    name: str
    sgbds: tuple[str, ...]
    group: str | None
    address: int | None
    line: str
    fitted: str
    scan: bool


@cache
def modules() -> dict[str, Module]:
    raw = tomllib.loads((KB / "modules.toml").read_text(encoding="utf-8"))
    return {
        k: Module(k, v["name"], tuple(s.upper() for s in v["sgbds"]), v.get("group"),
                  v.get("address"), v.get("line", ""), v.get("fitted", "unknown"), v.get("scan", True))
        for k, v in raw.items()
    }


def profile() -> dict:
    """This car's resolved module variants, written by `r53 scan --save-profile`."""
    p = KB / "vehicle-profile.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def resolve(target: str) -> tuple[Module | None, str]:
    """Map a module key ('dme') or SGBD name ('EMS2K') to (module, sgbd to call)."""
    mods = modules()
    t = target.lower()
    if t in mods:
        m = mods[t]
        found = profile().get("modules", {}).get(m.key, {}).get("sgbd")
        return m, (found or m.sgbds[0]).upper()
    for m in mods.values():
        if target.upper() in m.sgbds or target.upper() == (m.group or "").upper():
            return m, target.upper()
    return None, target.upper()


# ---------------------------------------------------------------- safety

@cache
def _policy():
    raw = tomllib.loads((KB / "safety.toml").read_text(encoding="utf-8"))
    comp = lambda pats: [re.compile(p, re.I) for p in pats]
    t = raw["tiers"]
    overrides = {k.upper(): v for k, v in raw.get("overrides", {}).items()}
    for v in overrides.values():
        if v not in (READ, CONFIRM, BLOCKED):
            raise ValueError(f"bad override tier {v!r} in safety.toml")
    return comp(t["blocked"]), overrides, comp(t["confirm"]), comp(t["read"]), raw.get("actuation", {})


def classify(sgbd: str, job: str) -> tuple[str, str]:
    """Return (tier, reason) for running `job` on `sgbd`. Unknown jobs are blocked."""
    blocked, overrides, confirm, read, _ = _policy()
    job_u = job.upper()
    for p in blocked:
        if p.fullmatch(job_u):
            return BLOCKED, f"matches blocked pattern {p.pattern!r}"
    key = f"{sgbd.upper()}.{job_u}"
    if key in overrides:
        return overrides[key], f"override {key}"
    for p in confirm:
        if p.fullmatch(job_u):
            return CONFIRM, f"matches confirm pattern {p.pattern!r}"
    for p in read:
        if p.fullmatch(job_u):
            return READ, f"matches read pattern {p.pattern!r}"
    return BLOCKED, "unclassified job (not in any allow-list) — add it to kb/safety.toml after review"


def actuation_defaults() -> dict:
    return _policy()[4]


# ---------------------------------------------------------------- catalogs & translations

@cache
def catalog(sgbd: str) -> dict | None:
    p = KB / "catalog" / f"{sgbd.upper()}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


@cache
def translations() -> dict[str, str]:
    p = KB / "translations" / "de-en.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def en(text: str) -> str | None:
    """English for a German SGBD string, if the KB has one."""
    if not text:
        return None
    return translations().get(text.strip())
