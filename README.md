# r53-diag

Diagnostics for a **2006 MINI Cooper S (R53)** built to be driven by an AI agent such as
Claude Code, or by a person at a terminal. It uses the BMW EDIABAS install and the
K+DCAN USB cable that INPA / NCS Expert already use, so the same `.prg` SGBD files do all
the protocol work. What this adds:

- **One-command answers:** `scan` returns every module's identity and faults, decoded and in English.
- **JSON output** with units, English text and documentation for each value.
- **A safety policy:**
  - Reading runs freely.
  - Clearing faults and running actuator tests need explicit, per-action confirmation.
  - Coding, flashing, immobiliser and odometer jobs can't run at all.
- **Recorded sessions** that double as evidence and as replayable test fixtures.
- **A knowledge base:** job catalogs for every R50/R53 module, translated fault tables,
  hardware notes, module notes and diagnostic playbooks.

```
> python -m r53diag doctor
> python -m r53diag scan --save-profile
> python -m r53diag faults dme ews
> python -m r53diag status ews STATUS_LESEN
> python -m r53diag live dme:STATUS_ANA_ENGINE4 --interval 1 --duration 300 --csv warmup.csv
> python -m r53diag jobs dme --grep lambda
```

## Requirements

- Windows, Python **3.11+** (32- or 64-bit), no third-party packages.
- **The SGBD files** (`.prg`/`.grp`) for the R50/R53 modules. INPA/NCS installs ship these
  in `C:\EDIABAS\Ecu`. They are BMW's and aren't included here.
- **One of two interchangeable backends:**
  - **BMW EDIABAS 7.x** at `C:\EDIABAS` (`--backend ediabas`, the default):
    - `EDIABAS.INI` must have `Interface = STD:OBD`.
    - `obd.ini` must set `Port` to the cable's COM port.
    - 64-bit Python goes through EDIABAS's `api64.dll` proxy.
  - **[EdiabasLib](https://github.com/uholeschak/ediabaslib)** (`--backend ediabaslib`):
    - an open-source (GPL-3) reimplementation of EDIABAS that runs the same SGBDs and drives
      the cable directly;
    - install it with `python tools/install_ediabaslib.py` (downloads into the gitignored
      `vendor/`);
    - needs .NET Framework 4.7.2+, which Windows 10/11 has built in;
    - takes the COM port and SGBD folder from an existing `obd.ini`/`EDIABAS.INI`, or from
      `R53_COM_PORT` / `R53_ECU_PATH`. With those set, no BMW EDIABAS install is needed.
  - Pick a backend per command with `--backend`, or set `R53_BACKEND`.
- An FTDI-based **K+DCAN cable** set to bridge **OBD pins 7+8**. That setting is needed to
  reach the body modules on pre-2007 cars; see [`kb/hardware.md`](kb/hardware.md).

`pip install -e .` gives you an `r53` command; `python -m r53diag` works without installing.

## Layout

| Path | What |
|---|---|
| `r53diag/` | the tool: EDIABAS ctypes wrapper, SGBD reader, safety policy, decoders, CLI |
| `kb/` | knowledge base; start at [`kb/README.md`](kb/README.md) |
| `tools/build_kb.py` | regenerates `kb/catalog/` and the translation work list from the installed SGBDs |
| `tests/` | offline tests (`python -m unittest discover tests`) |
| `research/FINDINGS.md` | how it was worked out, with sources |
| `PLAN.md` | roadmap |
| `AGENTS.md` | rules and workflow for AI agents |

## Status

Phase 0 is done: offline tooling, KB and tests. Nothing has been verified on the car yet;
see [`PLAN.md`](PLAN.md).

## License

- **Code:** MIT.
- **Docs and knowledge base:** CC BY 4.0.

See [`LICENSE`](LICENSE). Not affiliated with BMW; BMW, MINI, EDIABAS and INPA are
trademarks of BMW AG. Talking to a car's control units can change its behaviour; use at
your own risk.
