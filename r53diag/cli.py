"""r53 — diagnostics for a 2006 MINI Cooper S (R53) over EDIABAS.

Output is JSON on stdout (for agents); progress/warnings go to stderr.
Exit codes: 0 ok · 1 communication/job failure · 2 refused by safety policy · 3 bad usage.
"""
from __future__ import annotations

import argparse
import configparser
import csv
import datetime as dt
import json
import struct
import sys
import time
from pathlib import Path

from . import decode, kb
from .backends import EdiabasBackend, ReplayBackend
from .ediabas import DEFAULT_DIR, JobResult
from .session import Session, redact_sets


class Refused(Exception):
    pass


def eprint(*a):
    print(*a, file=sys.stderr, flush=True)


class Runner:
    """Executes jobs through a backend, enforcing the safety policy and recording the session."""

    def __init__(self, args, command: str):
        self.session = Session(command, enabled=not args.no_record)
        if args.replay:
            self.backend = ReplayBackend(Path(args.replay))
        else:
            self.backend = EdiabasBackend(self.session.trace_dir if args.trace else None)
        self.timeout = args.timeout
        self.session.write("backend", backend=self.backend.name)

    def run(self, sgbd: str, job: str, args: str = "", confirm: bool = False) -> JobResult:
        tier, why = kb.classify(sgbd, job)
        if tier == kb.BLOCKED:
            self.session.write("refused", sgbd=sgbd, job=job, args=args, reason=why)
            raise Refused(f"{sgbd}.{job} is blocked: {why}")
        if tier == kb.CONFIRM and not confirm:
            self.session.write("refused", sgbd=sgbd, job=job, args=args, reason="needs --confirm")
            raise Refused(f"{sgbd}.{job} changes the car's state and needs --confirm "
                          f"(a human must approve this specific action)")
        r = self.backend.job(sgbd, job, args, "", self.timeout)
        r.sets = redact_sets(r.sets)
        self.session.job(r, tier)
        if not r.ok:
            eprint(f"  {sgbd}.{job}: {r.error_text or r.job_status}")
        return r

    def close(self):
        self.backend.close()
        self.session.write("end")


def out(obj, args):
    print(json.dumps(obj, ensure_ascii=False, indent=None if args.compact else 1, default=str))


def summary(r: JobResult) -> dict:
    d = {"ok": r.ok, "sgbd": r.ecu, "job": r.job}
    if r.args:
        d["args"] = r.args
    if r.variant and r.variant.upper() != r.ecu.upper():
        d["variant"] = r.variant
    if not r.ok:
        d["error"] = r.error_text or r.job_status
    return d


# --------------------------------------------------------------------------- doctor

def _serial_ports() -> dict[str, str]:
    import winreg
    ports = {}
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
        i = 0
        while True:
            try:
                dev, port, _ = winreg.EnumValue(k, i)
            except OSError:
                break
            ports[port.upper()] = dev
            i += 1
    except OSError:
        pass
    return ports


def _ftdi_latency(port: str) -> int | None:
    import winreg
    base = r"SYSTEM\CurrentControlSet\Enum\FTDIBUS"
    try:
        root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
    except OSError:
        return None
    i = 0
    while True:
        try:
            dev = winreg.EnumKey(root, i)
        except OSError:
            return None
        i += 1
        try:
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf"{base}\{dev}\0000\Device Parameters")
            if winreg.QueryValueEx(k, "PortName")[0].upper() == port:
                return winreg.QueryValueEx(k, "LatencyTimer")[0]
        except OSError:
            continue


def _ini(path: Path) -> configparser.ConfigParser:
    cp = configparser.ConfigParser(strict=False, inline_comment_prefixes=(";",))
    cp.optionxform = str.lower
    if path.exists():
        cp.read_string(path.read_text(encoding="latin-1"))
    return cp


def cmd_doctor(args):
    checks = []

    def check(name, ok, detail, fix=None):
        c = {"check": name, "ok": ok, "detail": detail}
        if fix and not ok:
            c["fix"] = fix
        checks.append(c)

    bits = struct.calcsize("P") * 8
    dll = DEFAULT_DIR / ("api64.dll" if bits == 64 else "api32.dll")
    check("ediabas_api", dll.exists(), f"{bits}-bit Python -> {dll}")
    ini = _ini(DEFAULT_DIR / "EDIABAS.INI")
    iface = ini.get("Configuration", "interface", fallback="?")
    check("ediabas_interface", iface.upper() == "STD:OBD", f"EDIABAS.INI Interface = {iface}",
          "set Interface = STD:OBD in C:\\EDIABAS\\Bin\\EDIABAS.INI")
    obd = _ini(DEFAULT_DIR / "obd.ini")
    port = obd.get("OBD", "port", fallback="").upper()
    check("obd_ini_port", bool(port), f"obd.ini [OBD] Port = {port or '(missing)'}")
    retry = obd.get("OBD", "retry", fallback="")
    checks.append({"check": "obd_ini_retry", "ok": True,
                   "detail": f"RETRY = {retry or '(default)'}; vendor doc recommends OFF (EDIABAS retries itself)"})
    ports = _serial_ports()
    present = port in ports
    check("cable_present", present, f"{port} {'present' if present else 'not present'} "
          f"(ports now: {', '.join(sorted(ports)) or 'none'})",
          "plug the K+DCAN cable in; if it enumerates on a different COM port, update obd.ini Port")
    lat = _ftdi_latency(port) if port else None
    check("ftdi_latency", lat in (1, None), f"LatencyTimer = {lat}",
          "Device Manager > Ports > USB Serial Port > Advanced > Latency Timer = 1 ms")

    car = {}
    if present and not args.offline:
        runner = Runner(args, "doctor")
        try:
            dme = runner.run("EMS2K", "IDENT")
            car["pin7_dme"] = summary(dme)
            if dme.ok:
                ub = runner.run("EMS2K", "STATUS_UBATT")
                if ub.ok:
                    v = ub.first("STAT_UBATT_WERT")
                    car["battery_v"] = v
                    check("battery_voltage", isinstance(v, (int, float)) and v >= 12.2,
                          f"{v} V at DME (after main relay)",
                          "low voltage makes modules drop out; connect a charger for long sessions")
            kmb = runner.run("D_0080", "IDENT")
            car["pin8_kombi"] = summary(kmb)
            if dme.ok and kmb.ok:
                verdict = "both diagnostic lines answer — cable bridges pins 7+8"
            elif dme.ok:
                verdict = ("pin 7 OK but the cluster (pin 8) is silent: check the cable switch is in the labelled position "
                           "that bridges OBD pins 7+8 (see kb/hardware.md), ignition on")
            elif kmb.ok:
                verdict = "cluster answers but DME does not: unusual — check DME power / fuse, re-run"
            else:
                verdict = "no module answered: ignition to position II (KL15)? cable fully seated? COM port right?"
            check("diagnostic_lines", dme.ok and kmb.ok, verdict)
        finally:
            runner.close()
    out({"checks": checks, "car": car, "ok": all(c["ok"] for c in checks)}, args)
    return 0 if all(c["ok"] for c in checks) else 1


# --------------------------------------------------------------------------- scan / ident / faults

def _targets(args_targets, use_all) -> list[tuple[kb.Module, str]]:
    if args_targets:
        res = []
        for t in args_targets:
            m, s = kb.resolve(t)
            res.append((m, s))
        return res
    prof = kb.profile().get("modules", {})
    res = []
    for m in kb.modules().values():
        if not m.scan:
            continue
        if prof:
            if m.key in prof and prof[m.key].get("sgbd"):
                res.append((m, prof[m.key]["sgbd"]))
        elif m.fitted != "no" or use_all:
            res.append((m, m.sgbds[0]))
    return res


def cmd_scan(args):
    runner = Runner(args, "scan")
    found, missing = {}, []
    try:
        for m in kb.modules().values():
            if not m.scan or (m.fitted == "no" and not args.all):
                continue
            eprint(f"- {m.key}: {m.name}")
            attempts = ([m.group] if m.group else []) + list(m.sgbds)
            hit = None
            tried = []
            for a in attempts:
                r = runner.run(a, "IDENT")
                tried.append({"sgbd": a, "error": None if r.ok else (r.error_text or r.job_status)})
                if r.ok:
                    hit = r
                    break
                if r.error_text and "IFH-0009" in r.error_text and m.group:
                    break  # the group already probed this address; variants won't answer either
            if not hit:
                missing.append({"module": m.key, "name": m.name, "line": m.line, "fitted": m.fitted, "tried": tried})
                continue
            sgbd = (hit.variant or hit.ecu).upper()
            entry = {"module": m.key, "name": m.name, "sgbd": sgbd, "line": m.line, "ident": decode.ident(hit)}
            if not args.no_faults:
                fr = runner.run(sgbd, "FS_LESEN")
                entry["faults"] = decode.faults(fr, sgbd) if fr.ok else {"error": fr.error_text or fr.job_status}
            found[m.key] = entry
    finally:
        runner.close()
    pin8_dead = not any(e["line"] == "pin8" for e in found.values()) and any(e["line"] == "pin8" for e in missing)
    hints = []
    if pin8_dead and found:
        hints.append("No pin-8 (K-bus) module answered while pin-7 modules did: the cable is not bridging "
                     "OBD pins 7+8 — change the cable switch position (kb/hardware.md).")
    result = {"responding": found, "not_responding": missing, "hints": hints,
              "session": str(runner.session.path) if runner.session.enabled else None}
    if args.save_profile and found:
        prof = {"updated": dt.date.today().isoformat(),
                "note": "Generated by `r53 scan --save-profile`. VIN-like fields are not stored.",
                "modules": {k: {"sgbd": e["sgbd"], "name": e["name"],
                                "ident": {ik: iv for ik, iv in e["ident"].items()
                                          if not any(x in ik for x in ("FGNR", "VIN", "FG_NR"))}}
                            for k, e in found.items()}}
        (kb.KB / "vehicle-profile.json").write_text(json.dumps(prof, ensure_ascii=False, indent=1, default=str),
                                                    encoding="utf-8")
        result["profile_saved"] = "kb/vehicle-profile.json"
    out(result, args)
    return 0 if found else 1


def cmd_ident(args):
    m, sgbd = kb.resolve(args.target)
    runner = Runner(args, f"ident {args.target}")
    try:
        r = runner.run(sgbd, "IDENT")
    finally:
        runner.close()
    out({**summary(r), "module": m.key if m else None, "ident": decode.ident(r) if r.ok else None}, args)
    return 0 if r.ok else 1


def cmd_faults(args):
    targets = _targets(args.targets, args.all)
    runner = Runner(args, "faults " + " ".join(args.targets or ["all"]))
    res, rc = [], 0
    try:
        for m, sgbd in targets:
            job = "IS_LESEN" if args.info else "FS_LESEN"
            r = runner.run(sgbd, job)
            entry = {**summary(r), "module": m.key if m else None}
            if r.ok:
                entry["faults"] = decode.faults(r, sgbd)
                entry["count"] = len(entry["faults"])
            else:
                rc = 1
            res.append(entry)
    finally:
        runner.close()
    out({"modules": res, "total_faults": sum(e.get("count", 0) for e in res)}, args)
    return rc


def cmd_status(args):
    m, sgbd = kb.resolve(args.target)
    runner = Runner(args, f"status {args.target} {args.job}")
    try:
        r = runner.run(sgbd, args.job.upper(), args.args or "")
    finally:
        runner.close()
    d = summary(r)
    if r.ok:
        d["values"] = decode.values(r, sgbd)
    if args.raw or not r.ok:
        d["raw"] = r.sets
    out(d, args)
    return 0 if r.ok else 1


def cmd_run(args):
    m, sgbd = kb.resolve(args.target)
    runner = Runner(args, f"run {args.target} {args.job}")
    try:
        r = runner.run(sgbd, args.job.upper(), args.args or "", confirm=args.confirm)
    finally:
        runner.close()
    out({**summary(r), "values": decode.values(r, sgbd) if r.ok else None, "raw": r.sets}, args)
    return 0 if r.ok else 1


def cmd_live(args):
    specs = []
    for s in args.jobs:
        t, _, job = s.partition(":")
        if not job:
            raise SystemExit(f"bad job spec {s!r}; use module:JOB (e.g. dme:STATUS_ANA_ENGINE4)")
        _, sgbd = kb.resolve(t)
        tier, why = kb.classify(sgbd, job)
        if tier != kb.READ:
            raise Refused(f"live only runs read-tier jobs; {sgbd}.{job} is {tier}")
        specs.append((sgbd, job.upper()))
    runner = Runner(args, "live " + " ".join(args.jobs))
    writer = None
    csv_file = None
    t0 = time.monotonic()
    n = 0
    try:
        while (time.monotonic() - t0) < args.duration and (args.count is None or n < args.count):
            row = {"t": round(time.monotonic() - t0, 2)}
            for sgbd, job in specs:
                r = runner.run(sgbd, job)
                if r.ok:
                    for v in decode.values(r, sgbd):
                        if isinstance(v.get("value"), (int, float)) or "text" in v:
                            row[f"{sgbd}.{v['name']}"] = v.get("value", v.get("text"))
                else:
                    row[f"{sgbd}.{job}.error"] = r.error_text or r.job_status
            n += 1
            if args.csv:
                if writer is None:
                    csv_file = open(args.csv, "w", newline="", encoding="utf-8")
                    writer = csv.DictWriter(csv_file, fieldnames=list(row), extrasaction="ignore")
                    writer.writeheader()
                writer.writerow(row)
                csv_file.flush()
            print(json.dumps(row, ensure_ascii=False), flush=True)
            sleep = args.interval - ((time.monotonic() - t0) % args.interval if args.interval else 0)
            if args.interval and sleep > 0:
                time.sleep(sleep)
    except KeyboardInterrupt:
        pass
    finally:
        if csv_file:
            csv_file.close()
        runner.close()
    eprint(f"{n} samples; session {runner.session.path}")
    return 0


def cmd_clear(args):
    m, sgbd = kb.resolve(args.target)
    if not args.confirm:
        raise Refused(f"clearing {sgbd} fault memory needs --confirm (faults are saved first)")
    runner = Runner(args, f"clear {args.target}")
    try:
        before = runner.run(sgbd, "FS_LESEN")
        if not before.ok:
            out({**summary(before), "cleared": False, "reason": "could not read faults first; not clearing"}, args)
            return 1
        saved = decode.faults(before, sgbd)
        clr = runner.run(sgbd, "FS_LOESCHEN", confirm=True)
        after = runner.run(sgbd, "FS_LESEN")
    finally:
        runner.close()
    out({"sgbd": sgbd, "cleared": clr.ok, "error": None if clr.ok else (clr.error_text or clr.job_status),
         "faults_before": saved, "faults_after": decode.faults(after, sgbd) if after.ok else None,
         "session": str(runner.session.path)}, args)
    return 0 if clr.ok else 1


def cmd_actuate(args):
    m, sgbd = kb.resolve(args.target)
    job = args.job.upper()
    tier, why = kb.classify(sgbd, job)
    if tier != kb.CONFIRM:
        raise Refused(f"{sgbd}.{job} is {tier}, not an actuation ({why})")
    if not args.confirm:
        raise Refused(f"actuating {sgbd}.{job} needs --confirm")
    conf = kb.actuation_defaults()
    rel = conf.get("release", {}).get(f"{sgbd}.{job}")
    hold = min(args.seconds, conf.get("default_max_seconds", 20))
    a0 = (args.args or "").split(";")[0]
    if not rel:
        eprint(f"note: no known release for {sgbd}.{job}; the ECU decides when the output returns to normal")
    runner = Runner(args, f"actuate {args.target} {job}")
    res = {"sgbd": sgbd, "job": job, "args": args.args, "hold_s": hold}
    try:
        r = runner.run(sgbd, job, args.args or "", confirm=True)
        res["start"] = {**summary(r), "values": decode.values(r, sgbd) if r.ok else None}
        if r.ok and rel:
            eprint(f"holding {hold}s… (Ctrl-C to release early)")
            try:
                time.sleep(hold)
            except KeyboardInterrupt:
                pass
        if rel:
            rr = runner.run(sgbd, rel["job"], rel["args"].format(a0), confirm=True)
            res["release"] = summary(rr)
    finally:
        runner.close()
    out(res, args)
    return 0 if res["start"]["ok"] else 1


# --------------------------------------------------------------------------- offline KB queries

def cmd_jobs(args):
    _, sgbd = kb.resolve(args.target)
    cat = kb.catalog(sgbd)
    if not cat:
        raise SystemExit(f"no catalog for {sgbd}; run python tools/build_kb.py")
    rows = []
    for name, j in cat["jobs"].items():
        if args.tier and j["tier"] != args.tier:
            continue
        text = " ".join([name, *j["comment"], *(r["name"] for r in j["results"])])
        if args.grep and args.grep.lower() not in text.lower():
            continue
        row = {"job": name, "tier": j["tier"], "comment": [kb.en(c) or c for c in j["comment"]]}
        if args.verbose:
            row["args"] = j["args"]
            row["results"] = j["results"]
        else:
            row["args"] = [a["name"] for a in j["args"]]
            row["results"] = [r["name"] for r in j["results"] if not r["name"].startswith("_")]
        rows.append(row)
    out({"sgbd": sgbd, "file": cat["file"], "jobs": rows}, args)
    return 0


def cmd_tables(args):
    _, sgbd = kb.resolve(args.target)
    cat = kb.catalog(sgbd)
    if not cat:
        raise SystemExit(f"no catalog for {sgbd}; run python tools/build_kb.py")
    if not args.name:
        out({"sgbd": sgbd, "tables": {k: len(v) for k, v in cat["tables"].items()}}, args)
        return 0
    rows = cat["tables"].get(args.name.upper())
    if rows is None:
        raise SystemExit(f"{sgbd} has no table {args.name}")
    if args.grep:
        rows = [r for r in rows if args.grep.lower() in json.dumps(r, ensure_ascii=False).lower()]
    rows = [{**r, **{f"{k}_en": kb.en(v) for k, v in r.items() if isinstance(v, str) and kb.en(v)}} for r in rows]
    out({"sgbd": sgbd, "table": args.name.upper(), "rows": rows}, args)
    return 0


def cmd_modules(args):
    prof = kb.profile().get("modules", {})
    out([{"module": m.key, "name": m.name, "sgbds": m.sgbds, "group": m.group, "line": m.line,
          "fitted": m.fitted, "profile_sgbd": prof.get(m.key, {}).get("sgbd")} for m in kb.modules().values()], args)
    return 0


def cmd_classify(args):
    _, sgbd = kb.resolve(args.target)
    tier, why = kb.classify(sgbd, args.job)
    out({"sgbd": sgbd, "job": args.job.upper(), "tier": tier, "reason": why}, args)
    return 0


# --------------------------------------------------------------------------- main

def build_parser() -> argparse.ArgumentParser:
    def common(parser, defaults):
        d = (lambda v: v) if defaults else (lambda v: argparse.SUPPRESS)
        parser.add_argument("--replay", metavar="PATH", default=d(None),
                            help="answer jobs from recorded session(s) instead of the car")
        parser.add_argument("--no-record", action="store_true", default=d(False), help="don't write a session file")
        parser.add_argument("--trace", action="store_true", default=d(False),
                            help="also capture EDIABAS API+IFH trace (raw bytes)")
        parser.add_argument("--timeout", type=float, default=d(30.0), help="per-job timeout in seconds")
        parser.add_argument("--compact", action="store_true", default=d(False), help="single-line JSON")

    p = argparse.ArgumentParser(prog="r53", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common(p, True)
    shared = argparse.ArgumentParser(add_help=False)
    common(shared, False)
    sub = p.add_subparsers(dest="cmd", required=True)
    _add = sub.add_parser
    sub.add_parser = lambda *a, **k: _add(*a, parents=[shared], **k)

    s = sub.add_parser("doctor", help="check setup, cable, battery, and which diagnostic lines answer")
    s.add_argument("--offline", action="store_true", help="skip talking to the car")
    s.set_defaults(fn=cmd_doctor)

    s = sub.add_parser("scan", help="find every module, identify it, count its faults")
    s.add_argument("--all", action="store_true", help="include modules marked fitted = no")
    s.add_argument("--no-faults", action="store_true")
    s.add_argument("--save-profile", action="store_true", help="write kb/vehicle-profile.json")
    s.set_defaults(fn=cmd_scan)

    s = sub.add_parser("ident", help="identification of one module")
    s.add_argument("target", help="module key (dme, kombi, ews, …) or SGBD name")
    s.set_defaults(fn=cmd_ident)

    s = sub.add_parser("faults", help="read fault memory (default: every module in the profile)")
    s.add_argument("targets", nargs="*")
    s.add_argument("--all", action="store_true", help="without a profile, include unknown-fitment modules")
    s.add_argument("--info", action="store_true", help="read the info/shadow memory (IS_LESEN) instead")
    s.set_defaults(fn=cmd_faults)

    s = sub.add_parser("status", help="run one read-only job and decode its values")
    s.add_argument("target")
    s.add_argument("job")
    s.add_argument("args", nargs="?", help="job arguments, ';'-separated")
    s.add_argument("--raw", action="store_true", help="include raw result sets")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("live", help="poll read-only jobs repeatedly (JSON lines; optional CSV)")
    s.add_argument("jobs", nargs="+", metavar="module:JOB")
    s.add_argument("--interval", type=float, default=0.0, help="seconds between samples (0 = as fast as possible)")
    s.add_argument("--duration", type=float, default=60.0)
    s.add_argument("--count", type=int)
    s.add_argument("--csv", metavar="FILE")
    s.set_defaults(fn=cmd_live)

    s = sub.add_parser("run", help="run any job (still subject to the safety policy)")
    s.add_argument("target")
    s.add_argument("job")
    s.add_argument("args", nargs="?")
    s.add_argument("--confirm", action="store_true", help="human-approved: allow a confirm-tier job")
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("clear", help="clear a module's fault memory (reads + saves faults first)")
    s.add_argument("target")
    s.add_argument("--confirm", action="store_true")
    s.set_defaults(fn=cmd_clear)

    s = sub.add_parser("actuate", help="drive an output/test, then release it")
    s.add_argument("target")
    s.add_argument("job")
    s.add_argument("args", nargs="?")
    s.add_argument("--seconds", type=float, default=5.0, help="hold time before release (capped by kb/safety.toml)")
    s.add_argument("--confirm", action="store_true")
    s.set_defaults(fn=cmd_actuate)

    s = sub.add_parser("jobs", help="offline: list a module's jobs with safety tier")
    s.add_argument("target")
    s.add_argument("--grep")
    s.add_argument("--tier", choices=[kb.READ, kb.CONFIRM, kb.BLOCKED])
    s.add_argument("-v", "--verbose", action="store_true", help="include arg/result comments")
    s.set_defaults(fn=cmd_jobs)

    s = sub.add_parser("tables", help="offline: list or show an SGBD's tables (fault texts, scaling…)")
    s.add_argument("target")
    s.add_argument("name", nargs="?")
    s.add_argument("--grep")
    s.set_defaults(fn=cmd_tables)

    s = sub.add_parser("modules", help="offline: the module map and this car's resolved variants")
    s.set_defaults(fn=cmd_modules)

    s = sub.add_parser("classify", help="offline: show the safety tier of a job")
    s.add_argument("target")
    s.add_argument("job")
    s.set_defaults(fn=cmd_classify)
    return p


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args) or 0
    except Refused as e:
        print(json.dumps({"ok": False, "refused": str(e)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
