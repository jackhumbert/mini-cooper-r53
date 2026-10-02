"""Turn raw EDIABAS result sets into agent-friendly structures (English, units, notes)."""
from __future__ import annotations

import re
import tomllib
from functools import cache

from . import kb
from .ediabas import JobResult

_SUFFIX = re.compile(r"^(?P<base>.+?)_(?P<kind>WERT|EINH|TEXT|INFO)$")
_SKIP = re.compile(r"^(_TEL_|JOB_STATUS$)")


def _result_doc(sgbd: str, job: str, name: str) -> str | None:
    cat = kb.catalog(sgbd)
    if not cat:
        return None
    j = cat["jobs"].get(job.upper())
    if not j:
        return None
    for r in j.get("results", []):
        if r["name"] == name:
            return r.get("comment_en") or (" / ".join(r.get("comment", [])) or None)
    return None


def _txt(v):
    if isinstance(v, str):
        t = kb.en(v)
        return {"text": v, "text_en": t} if t else {"text": v}
    return {}


def values(r: JobResult, sgbd: str | None = None) -> list[dict]:
    """Flatten a status job into [{name, value, unit, text, doc}] grouping X_WERT/X_EINH/X_TEXT."""
    sgbd = sgbd or r.variant or r.ecu
    out = []
    for i, s in enumerate(r.data, 1):
        groups: dict[str, dict] = {}
        for k, v in s.items():
            if _SKIP.match(k):
                continue
            m = _SUFFIX.match(k)
            base, kind = (m["base"], m["kind"]) if m else (k, "WERT")
            g = groups.setdefault(base, {"name": base})
            if kind == "WERT":
                g["value"] = v
                g["result"] = k
            elif kind == "EINH":
                g["unit"] = v
            else:
                g.update({("text" if kind == "TEXT" else "info"): v})
                if kind == "TEXT" and (t := kb.en(v)):
                    g["text_en"] = t
        for g in groups.values():
            doc = _result_doc(sgbd, r.job, g.get("result", g["name"])) or _result_doc(sgbd, r.job, g["name"] + "_TEXT")
            if doc:
                g["doc"] = doc
            if len(r.data) > 1:
                g["set"] = i
            out.append(g)
    return out


@cache
def _fault_notes(sgbd: str) -> dict:
    p = kb.KB / "faults" / f"{sgbd.upper()}.toml"
    return tomllib.loads(p.read_text(encoding="utf-8")).get("codes", {}) if p.exists() else {}


def faults(r: JobResult, sgbd: str | None = None) -> list[dict]:
    """Decode FS_LESEN / IS_LESEN result sets into a list of faults."""
    sgbd = (sgbd or r.variant or r.ecu).upper()
    out = []
    for s in r.data:
        if "F_ORT_NR" not in s and "F_ORT_TEXT" not in s:
            continue
        nr = s.get("F_ORT_NR")
        code = f"0x{nr:04X}" if isinstance(nr, int) else str(nr)
        f = {"code": code, **_txt(s.get("F_ORT_TEXT", ""))}
        if "F_HEX_CODE" in s:
            f["hex"] = s["F_HEX_CODE"]["hex"] if isinstance(s["F_HEX_CODE"], dict) else s["F_HEX_CODE"]
        if "F_HFK" in s:
            f["count"] = s["F_HFK"]
        types = []
        for n in range(1, 10):
            t = s.get(f"F_ART{n}_TEXT")
            if t and t not in ("--", "-"):
                types.append(_txt(t))
        if types:
            f["types"] = types
        env = []
        for n in range(1, 10):
            if f"F_UW{n}_TEXT" in s or f"F_UW{n}_WERT" in s:
                e = {"name": s.get(f"F_UW{n}_TEXT"), "value": s.get(f"F_UW{n}_WERT"), "unit": s.get(f"F_UW{n}_EINH")}
                if (t := kb.en(e["name"] or "")):
                    e["name_en"] = t
                env.append(e)
        if env:
            f["environment"] = env
        known = {"F_ORT_NR", "F_ORT_TEXT", "F_HEX_CODE", "F_HFK", "F_ART_ANZ", "F_UW_ANZ"}
        extra = {k: v for k, v in s.items()
                 if k not in known and not re.match(r"F_(ART|UW)\d", k) and not _SKIP.match(k)}
        if extra:
            f["extra"] = {k: (_txt(v) or v) if isinstance(v, str) else v for k, v in extra.items()}
        note = _fault_notes(sgbd).get(code)
        if note:
            f["kb"] = note
        out.append(f)
    return out


def ident(r: JobResult) -> dict:
    """IDENT results as a flat dict (first data set), English supplier text etc. kept raw."""
    d = {k: v for k, v in (r.data[0] if r.data else {}).items() if not _SKIP.match(k)}
    return d
