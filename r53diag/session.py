"""Session recording: every job run is appended to sessions/YYYY-MM-DD/HHMMSS-<command>.jsonl.

Recordings are evidence (attach them to car-manager issues) and replay fixtures
(`r53 --replay <file-or-dir> ...`)."""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from .ediabas import JobResult
from .kb import ROOT

SESSIONS = ROOT / "sessions"
# Never persist values of these results (VIN / key data). Matched against result names.
# Applied to everything the tool prints or records, so it can't leak into a published issue.
# Raw telegrams (_TEL_*) are kept for debugging unless their set held a sensitive value.
REDACT = re.compile(r"(FGNR|FG_NR|VIN|ISN|SCHLUESSEL_ID|AKTUELLER_WC|_WC_|PLIP|PASSWORT)", re.I)


def redact_sets(sets: list[dict]) -> list[dict]:
    out = []
    for s in sets:
        hit = any(REDACT.search(k) for k in s)
        out.append({k: ("<redacted>" if REDACT.search(k) or (hit and k.startswith("_TEL_")) else v)
                    for k, v in s.items()})
    return out


class Session:
    def __init__(self, command: str, root: Path = SESSIONS, enabled: bool = True):
        now = dt.datetime.now()
        self.enabled = enabled
        slug = re.sub(r"[^a-z0-9]+", "-", command.lower()).strip("-")[:40] or "session"
        self.dir = root / now.strftime("%Y-%m-%d")
        self.path = self.dir / f"{now.strftime('%H%M%S')}-{slug}.jsonl"
        self.trace_dir = self.dir / f"{now.strftime('%H%M%S')}-{slug}.trace"
        if enabled:
            self.write("start", command=command)

    def write(self, kind: str, **data):
        if not self.enabled:
            return
        self.dir.mkdir(parents=True, exist_ok=True)
        rec = {"t": dt.datetime.now().isoformat(timespec="milliseconds"), "kind": kind, **data}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")

    def job(self, r: JobResult, tier: str):
        self.write("job", tier=tier, result=r.to_dict())
