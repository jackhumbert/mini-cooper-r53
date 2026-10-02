"""Offline reader for EDIABAS SGBD files (.prg / .grp).

SGBDs are BEST/2 object files. Text sections are XOR'd with 0xF7. Layout (little-endian
uint32 pointers in the file header):

    0x84 -> table directory: count, then 0x50-byte entries
            (name[0x40], cells_offset, ?, n_columns, n_rows)
            cells: (n_rows + 1) * n_columns NUL-terminated strings, header row first
    0x88 -> job directory:   count, then 0x44-byte entries (name[0x40], code_offset)
    0x90 -> description block: length, then "KEY:value" lines
            (ECU/ORIGIN/REVISION/..., then JOBNAME/JOBCOMMENT/ARG.../RESULT... per job)

This is enough to build job catalogs and pull out fault-text tables without talking to
the car. Executing jobs is left to EDIABAS.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

XOR = 0xF7
ENCODING = "latin-1"


def _dec(b: bytes) -> bytes:
    return bytes(x ^ XOR for x in b)


def _u32(d: bytes, off: int) -> int:
    return struct.unpack_from("<I", d, off)[0]


@dataclass
class Arg:
    name: str
    type: str = ""
    comment: list[str] = field(default_factory=list)


@dataclass
class Result:
    name: str
    type: str = ""
    comment: list[str] = field(default_factory=list)


@dataclass
class Job:
    name: str
    comment: list[str] = field(default_factory=list)
    args: list[Arg] = field(default_factory=list)
    results: list[Result] = field(default_factory=list)


@dataclass
class Sgbd:
    name: str
    path: Path
    header: dict[str, list[str]]
    jobs: dict[str, Job]
    tables: dict[str, list[dict[str, str]]]

    @property
    def is_group(self) -> bool:
        return self.path.suffix.lower() == ".grp"


def read_tables(d: bytes) -> dict[str, list[dict[str, str]]]:
    tables: dict[str, list[dict[str, str]]] = {}
    base = _u32(d, 0x84)
    if base == 0 or base >= len(d):
        return tables
    count = _u32(_dec(d[base:base + 4]), 0)
    for i in range(count):
        e = _dec(d[base + 4 + i * 0x50: base + 4 + (i + 1) * 0x50])
        name = e[:0x40].split(b"\0")[0].decode(ENCODING)
        off, _, cols, rows = struct.unpack_from("<4I", e, 0x40)
        cells = []
        p = off
        for _ in range((rows + 1) * cols):
            end = p
            while d[end] != XOR:  # NUL after XOR
                end += 1
            cells.append(_dec(d[p:end]).decode(ENCODING))
            p = end + 1
        head = cells[:cols]
        tables[name] = [dict(zip(head, cells[(r + 1) * cols:(r + 2) * cols])) for r in range(rows)]
    return tables


def read_job_names(d: bytes) -> list[str]:
    base = _u32(d, 0x88)
    count = _u32(d, base)
    names = []
    for i in range(count):
        e = _dec(d[base + 4 + i * 0x44: base + 4 + i * 0x44 + 0x40])
        names.append(e.split(b"\0")[0].decode(ENCODING))
    return names


def read_description(d: bytes) -> tuple[dict[str, list[str]], dict[str, Job]]:
    base = _u32(d, 0x90)
    n = _u32(d, base)
    text = _dec(d[base + 4: base + 4 + n]).decode(ENCODING)
    header: dict[str, list[str]] = {}
    jobs: dict[str, Job] = {}
    job: Job | None = None
    item: Arg | Result | None = None
    for line in text.splitlines():
        key, sep, val = line.partition(":")
        if not sep:
            continue
        key, val = key.strip().upper(), val.strip()
        if key == "JOBNAME":
            job = jobs.setdefault(val.upper(), Job(val.upper()))
            item = None
        elif job is None:
            header.setdefault(key, []).append(val)
        elif key == "JOBCOMMENT":
            job.comment.append(val)
        elif key == "ARG":
            item = Arg(val)
            job.args.append(item)
        elif key == "RESULT":
            item = Result(val)
            job.results.append(item)
        elif key in ("ARGTYPE", "RESULTTYPE") and item is not None:
            item.type = val
        elif key in ("ARGCOMMENT", "RESULTCOMMENT") and item is not None:
            item.comment.append(val)
    return header, jobs


def load(path: str | Path) -> Sgbd:
    path = Path(path)
    d = path.read_bytes()
    header, jobs = read_description(d)
    # Jobs without a description entry still exist; keep them.
    for name in read_job_names(d):
        jobs.setdefault(name.upper(), Job(name.upper()))
    return Sgbd(name=path.stem.upper(), path=path, header=header, jobs=jobs, tables=read_tables(d))


def find(name: str, ecu_path: str | Path = r"C:\EDIABAS\Ecu") -> Path | None:
    ecu_path = Path(ecu_path)
    for ext in (".prg", ".grp"):
        for p in ecu_path.glob("*" + ext):
            if p.stem.upper() == name.upper():
                return p
    return None
