"""Backends that execute EDIABAS jobs: the real car, or a replay of recorded sessions."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .ediabas import Ediabas, JobResult


class Backend(Protocol):
    name: str

    def job(self, ecu: str, job: str, args: str = "", results: str = "", timeout: float = 30.0) -> JobResult: ...

    def close(self) -> None: ...


class EdiabasBackend:
    """Talks to the car through the installed BMW EDIABAS."""
    name = "ediabas"

    def __init__(self, trace_dir: Path | None = None):
        config = {}
        if trace_dir:
            trace_dir.mkdir(parents=True, exist_ok=True)
            config = {"TracePath": str(trace_dir), "ApiTrace": "1", "IfhTrace": "2"}
        self.ed = Ediabas(config=config)

    def job(self, ecu, job, args="", results="", timeout=30.0):
        return self.ed.job(ecu, job, args, results, timeout)

    def close(self):
        self.ed.close()


class ReplayBackend:
    """Answers jobs from recorded session files (sessions/**/*.jsonl or a single file).
    Lookup key is (ECU, JOB, ARGS); the most recent recording wins. Unknown jobs return
    an IFH-0009-style 'no response' so callers exercise their failure paths."""
    name = "replay"

    def __init__(self, source: Path):
        self.index: dict[tuple[str, str, str], dict] = {}
        files = sorted(source.rglob("*.jsonl")) if source.is_dir() else [source]
        for f in files:
            for line in f.read_text(encoding="utf-8").splitlines():
                rec = json.loads(line)
                if rec.get("kind") == "job":
                    r = rec["result"]
                    self.index[(r["ecu"].upper(), r["job"].upper(), r.get("args", ""))] = r
        if not self.index:
            raise ValueError(f"no recorded jobs found in {source}")

    def job(self, ecu, job, args="", results="", timeout=30.0):
        r = self.index.get((ecu.upper(), job.upper(), args))
        if r is None:
            return JobResult(ecu, job, args, error_code=19,
                             error_text="IFH-0009: NO RESPONSE FROM CONTROLUNIT (not in replay data)")
        return JobResult.from_dict(r)

    def close(self):
        pass
