"""Thin ctypes wrapper over BMW EDIABAS (api64.dll / api32.dll).

api64.dll works from 64-bit Python: it proxies to a 32-bit api64.exe server, which loads
the real EDIABAS runtime configured by C:\\EDIABAS\\Bin\\EDIABAS.INI (Interface=STD:OBD,
COM port from obd.ini). Every exported function is __stdcall and takes the handle first.
"""
from __future__ import annotations

import ctypes
import os
import struct
import time
from ctypes import byref, c_char_p, c_double, c_int, c_long, c_uint, c_ushort, create_string_buffer
from dataclasses import dataclass, field
from pathlib import Path

ENC = "latin-1"
APIBUSY, APIREADY, APIBREAK, APIERROR = 0, 1, 2, 3
(F_CHAR, F_BYTE, F_INTEGER, F_WORD, F_LONG, F_DWORD, F_TEXT, F_BINARY, F_REAL) = range(9)
DEFAULT_DIR = Path(os.environ.get("EDIABAS_BIN", r"C:\EDIABAS\Bin"))


class EdiabasError(Exception):
    def __init__(self, code: int, text: str):
        super().__init__(f"{text} (code {code})" if text else f"EDIABAS error {code}")
        self.code, self.text = code, text


@dataclass
class JobResult:
    ecu: str
    job: str
    args: str = ""
    sets: list[dict] = field(default_factory=list)   # sets[0] = system results
    ok: bool = False
    error_code: int = 0
    error_text: str = ""
    duration_s: float = 0.0

    @property
    def system(self) -> dict:
        return self.sets[0] if self.sets else {}

    @property
    def data(self) -> list[dict]:
        return self.sets[1:]

    @property
    def job_status(self) -> str | None:
        for s in reversed(self.sets):
            if "JOB_STATUS" in s:
                return str(s["JOB_STATUS"])
        return None

    @property
    def variant(self) -> str | None:
        return self.system.get("VARIANTE")

    def first(self, name: str, default=None):
        for s in self.data:
            if name in s:
                return s[name]
        return default

    def to_dict(self) -> dict:
        return {"ecu": self.ecu, "job": self.job, "args": self.args, "ok": self.ok,
                "job_status": self.job_status, "variant": self.variant,
                "error_code": self.error_code or None, "error_text": self.error_text or None,
                "duration_s": round(self.duration_s, 3), "sets": self.sets}

    @classmethod
    def from_dict(cls, d: dict) -> "JobResult":
        return cls(d["ecu"], d["job"], d.get("args", ""), d.get("sets", []), d.get("ok", False),
                   d.get("error_code") or 0, d.get("error_text") or "", d.get("duration_s", 0.0))


class Ediabas:
    def __init__(self, bin_dir: Path | str = DEFAULT_DIR, config: dict[str, str] | None = None):
        bits = struct.calcsize("P") * 8
        dll = Path(bin_dir) / ("api64.dll" if bits == 64 else "api32.dll")
        if not dll.exists():
            raise FileNotFoundError(f"EDIABAS API not found: {dll}")
        os.add_dll_directory(str(dll.parent))
        self._api = ctypes.WinDLL(str(dll))
        self._declare()
        self.dll = dll
        self.config = config or {}
        self.h = c_uint(0)
        self._open = False

    def _declare(self):
        a, H, W = self._api, c_uint, c_ushort
        sig = {
            "__apiInit": (c_int, [ctypes.POINTER(c_uint)]),
            "__apiInitExt": (c_int, [ctypes.POINTER(c_uint), c_char_p, c_char_p, c_char_p, c_char_p]),
            "__apiEnd": (None, [H]),
            "__apiJob": (None, [H, c_char_p, c_char_p, c_char_p, c_char_p]),
            "__apiState": (c_int, [H]),
            "__apiStateExt": (c_int, [H, c_int]),
            "__apiBreak": (None, [H]),
            "__apiErrorCode": (c_int, [H]),
            "__apiErrorText": (None, [H, c_char_p, c_int]),
            "__apiResultSets": (c_int, [H, ctypes.POINTER(W)]),
            "__apiResultNumber": (c_int, [H, ctypes.POINTER(W), W]),
            "__apiResultName": (c_int, [H, c_char_p, W, W]),
            "__apiResultFormat": (c_int, [H, ctypes.POINTER(c_int), c_char_p, W]),
            "__apiResultText": (c_int, [H, c_char_p, c_char_p, W, c_char_p]),
            "__apiResultLong": (c_int, [H, ctypes.POINTER(c_long), c_char_p, W]),
            "__apiResultReal": (c_int, [H, ctypes.POINTER(c_double), c_char_p, W]),
            "__apiResultBinaryExt": (c_int, [H, c_char_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32, c_char_p, W]),
            "__apiSetConfig": (c_int, [H, c_char_p, c_char_p]),
            "__apiGetConfig": (c_int, [H, c_char_p, c_char_p]),
        }
        self.f = {}
        for name, (res, args) in sig.items():
            f = getattr(a, name)  # string lookup: avoids Python's __name mangling inside the class
            f.restype, f.argtypes = res, args
            self.f[name[len("__api"):]] = f

    # ------------------------------------------------------------------ lifecycle
    def open(self) -> "Ediabas":
        if self._open:
            return self
        if not self.f["Init"](byref(self.h)):
            raise EdiabasError(*self._error())
        self._open = True
        for k, v in self.config.items():
            self.f["SetConfig"](self.h, k.encode(ENC), str(v).encode(ENC))
        return self

    def close(self):
        if self._open:
            self.f["End"](self.h)
            self._open = False

    def __enter__(self):
        return self.open()

    def __exit__(self, *exc):
        self.close()

    def get_config(self, name: str) -> str:
        buf = create_string_buffer(256)
        self.f["GetConfig"](self.h, name.encode(ENC), buf)
        return buf.value.decode(ENC)

    def _error(self) -> tuple[int, str]:
        buf = create_string_buffer(1024)
        self.f["ErrorText"](self.h, buf, len(buf))
        return self.f["ErrorCode"](self.h), buf.value.decode(ENC)

    # ------------------------------------------------------------------ jobs
    def job(self, ecu: str, job: str, args: str = "", results: str = "", timeout: float = 30.0) -> JobResult:
        """Run one job synchronously. Never raises for ECU/communication errors —
        they come back in JobResult.ok / error_code / error_text."""
        self.open()
        res = JobResult(ecu, job, args)
        t0 = time.monotonic()
        self.f["Job"](self.h, ecu.encode(ENC), job.encode(ENC), args.encode(ENC), results.encode(ENC))
        state = APIBUSY
        while True:
            state = self.f["StateExt"](self.h, 100)
            if state != APIBUSY:
                break
            if time.monotonic() - t0 > timeout:
                self.f["Break"](self.h)
                res.duration_s = time.monotonic() - t0
                res.error_text = f"timeout after {timeout:.0f}s (job aborted)"
                return res
        res.duration_s = time.monotonic() - t0
        if state == APIERROR:
            res.error_code, res.error_text = self._error()
        res.sets = self._read_sets()
        res.ok = state == APIREADY and (res.job_status in (None, "OKAY"))
        return res

    def _read_sets(self) -> list[dict]:
        n = c_ushort(0)
        if not self.f["ResultSets"](self.h, byref(n)):
            return []
        sets = []
        for s in range(n.value + 1):
            cnt = c_ushort(0)
            self.f["ResultNumber"](self.h, byref(cnt), s)
            row = {}
            for i in range(1, cnt.value + 1):
                nb = create_string_buffer(64)
                if not self.f["ResultName"](self.h, nb, i, s):
                    continue
                name = nb.value.decode(ENC)
                row[name] = self._value(name.encode(ENC), s)
            sets.append(row)
        return sets

    def _value(self, name: bytes, s: int):
        fmt = c_int(-1)
        self.f["ResultFormat"](self.h, byref(fmt), name, s)
        f = fmt.value
        if f in (F_CHAR, F_BYTE, F_INTEGER, F_WORD, F_LONG, F_DWORD):
            v = c_long(0)
            if self.f["ResultLong"](self.h, byref(v), name, s):
                return v.value
        elif f == F_REAL:
            v = c_double(0)
            if self.f["ResultReal"](self.h, byref(v), name, s):
                return v.value
        elif f == F_BINARY:
            buf = create_string_buffer(65536)
            ln = ctypes.c_uint32(0)
            if self.f["ResultBinaryExt"](self.h, buf, byref(ln), len(buf), name, s):
                return {"hex": buf.raw[: ln.value].hex(" ").upper()}
        tb = create_string_buffer(1024)
        if self.f["ResultText"](self.h, tb, name, s, b""):
            return tb.value.decode(ENC)
        return None
