"""Backends that execute EDIABAS jobs: the real car, or a replay of recorded sessions."""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Protocol

from . import config
from .ediabas import Ediabas, JobResult


class Backend(Protocol):
    name: str

    def job(self, ecu: str, job: str, args: str = "", results: str = "", timeout: float = 30.0) -> JobResult: ...

    def close(self) -> None: ...


class EdiabasBackend:
    """Talks to the car through the installed BMW EDIABAS (api64.dll / api32.dll)."""
    name = "ediabas"
    # BMW's API truncates config values (TracePath included) to 64 characters, so traces are
    # written to a short staging directory and moved into the session afterwards.
    STAGING = Path(r"C:\EDIABAS\TRACE\r53")

    def __init__(self, trace_dir: Path | None = None):
        self.trace_dir = trace_dir
        settings = {}
        if trace_dir:
            shutil.rmtree(self.STAGING, ignore_errors=True)
            self.STAGING.mkdir(parents=True, exist_ok=True)
            settings = {"TracePath": str(self.STAGING), "ApiTrace": "1", "IfhTrace": "2"}
        self.dll = config.ediabas_dll()
        self.ed = Ediabas(self.dll, config=settings)

    def job(self, ecu, job, args="", results="", timeout=30.0):
        return self.ed.job(ecu, job, args, results, timeout)

    def close(self):
        self.ed.close()
        if self.trace_dir and self.STAGING.exists():
            time.sleep(0.5)  # api64.exe flushes api.trc shortly after apiEnd
            self.trace_dir.mkdir(parents=True, exist_ok=True)
            for f in self.STAGING.iterdir():
                shutil.move(str(f), self.trace_dir / f.name)


class EdiabasLibBackend:
    """Talks to the car through EdiabasLib (open source, GPL-3) instead of BMW's runtime.
    Same API, same .prg SGBDs and cable; install with `python tools/install_ediabaslib.py`."""
    name = "ediabaslib"

    def __init__(self, trace_dir: Path | None = None):
        self.dll = config.ediabaslib_dll()
        if not self.dll.exists():
            raise FileNotFoundError(f"EdiabasLib not installed ({self.dll}); run python tools/install_ediabaslib.py")
        if trace_dir:
            trace_dir.mkdir(parents=True, exist_ok=True)
        self.init_config = config.ediabaslib_init_config(trace_dir)
        self.ed = Ediabas(self.dll, init_config=self.init_config)

    def job(self, ecu, job, args="", results="", timeout=30.0):
        return self.ed.job(ecu, job, args, results, timeout)

    def close(self):
        self.ed.close()


def make_backend(name: str, trace_dir: Path | None = None):
    if name == "ediabas":
        return EdiabasBackend(trace_dir)
    if name == "ediabaslib":
        return EdiabasLibBackend(trace_dir)
    raise ValueError(f"unknown backend {name!r} (choose from {', '.join(config.BACKENDS)})")


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
