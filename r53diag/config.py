"""Where things are: EDIABAS install, SGBD path, cable COM port, and the EdiabasLib DLL.

Defaults come from the BMW EDIABAS install (EDIABAS.INI / obd.ini) when present, so both
backends talk to the same cable with the same SGBDs. Override with environment variables:

  R53_BACKEND        ediabas | ediabaslib          (default: ediabas)
  R53_EDIABAS_BIN    BMW EDIABAS Bin dir           (default: C:\\EDIABAS\\Bin)
  R53_ECU_PATH       SGBD directory                (default: EDIABAS.INI EcuPath or C:\\EDIABAS\\Ecu)
  R53_COM_PORT       cable port, e.g. COM6 / FTDI0 (default: obd.ini [OBD] Port)
  R53_EDIABASLIB     path to EdiabasLib Api64.dll  (default: vendor/ediabaslib/Api64.dll)
"""
from __future__ import annotations

import configparser
import os
import struct
from pathlib import Path

from .kb import ROOT

BACKENDS = ("ediabas", "ediabaslib")


def bits() -> int:
    return struct.calcsize("P") * 8


def ediabas_bin() -> Path:
    return Path(os.environ.get("R53_EDIABAS_BIN") or os.environ.get("EDIABAS_BIN") or r"C:\EDIABAS\Bin")


def read_ini(path: Path) -> configparser.ConfigParser:
    cp = configparser.ConfigParser(strict=False, inline_comment_prefixes=(";",))
    cp.optionxform = str.lower
    if path.exists():
        cp.read_string(path.read_text(encoding="latin-1"))
    return cp


def ediabas_ini() -> configparser.ConfigParser:
    return read_ini(ediabas_bin() / "EDIABAS.INI")


def obd_ini() -> configparser.ConfigParser:
    return read_ini(ediabas_bin() / "obd.ini")


def ecu_path() -> Path:
    env = os.environ.get("R53_ECU_PATH")
    if env:
        return Path(env)
    return Path(ediabas_ini().get("Configuration", "ecupath", fallback=r"C:\EDIABAS\Ecu"))


def com_port() -> str:
    return (os.environ.get("R53_COM_PORT") or obd_ini().get("OBD", "port", fallback="COM6")).upper()


def default_backend() -> str:
    b = os.environ.get("R53_BACKEND", "ediabas").lower()
    return b if b in BACKENDS else "ediabas"


def ediabas_dll() -> Path:
    return ediabas_bin() / ("api64.dll" if bits() == 64 else "api32.dll")


def ediabaslib_dir() -> Path:
    return ROOT / "vendor" / "ediabaslib"


def ediabaslib_dll() -> Path:
    env = os.environ.get("R53_EDIABASLIB")
    if env:
        return Path(env)
    return ediabaslib_dir() / ("Api64.dll" if bits() == 64 else "Api32.dll")


def ediabaslib_init_config(trace_dir: Path | None = None) -> str:
    """apiInitExt config string for EdiabasLib ("key=value;…", applied after any config file)."""
    cfg = {
        "Interface": "STD:OBD",
        "EcuPath": str(ecu_path()),
        "ObdComPort": com_port(),
        "RetryComm": "1",
        "ApiTrace": "0",
        "IfhTrace": "0",
    }
    if trace_dir:
        cfg.update({"TracePath": str(trace_dir), "ApiTrace": "1", "IfhTrace": "3", "TraceBuffering": "0"})
    return ";".join(f"{k}={v}" for k, v in cfg.items())


def dotnet_framework_release() -> int | None:
    """.NET Framework 4.x release number (EdiabasLib's Api DLLs are mixed-mode .NET 4.x)."""
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full")
        return int(winreg.QueryValueEx(k, "Release")[0])
    except OSError:
        return None
