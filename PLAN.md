# r53-diag — plan

A small Python tool and a knowledge base. Together they let Claude, or a person at a
terminal, identify, read faults from, log live data from and test the 2006 MINI Cooper S.
It uses the same K+DCAN cable and BMW EDIABAS install that INPA and NCS Expert already use.

The repo becomes a submodule of `car-manager` at
`vehicles/2006-mini-cooper-s/projects/r53-diag`. car-manager stays the record of
*what happened to the car* (issues, logs). This repo holds *how to talk to it* and
*what the data means*.

Background research: [`research/FINDINGS.md`](research/FINDINGS.md).

---

## Goals

1. **Easier than INPA.** `r53 scan` gives one command, one answer: every module's identity
   and faults, in plain English.
2. **Built for an agent.** The output is structured JSON with units and meanings, so Claude
   can reason over it, compare it to baselines and write findings into car-manager issues.
3. **Safe by default.** Reading is free. Anything that changes state needs explicit,
   per-action human approval. Coding, flashing and immobiliser writes cannot be run at all.
4. **Evidence is kept.** Every session is recorded and can be replayed. Recordings are also
   the test fixtures.

Non-goals for now: coding (NCS territory), flashing, a GUI, other cars.

## Architecture

```
Claude Code / terminal
        │  r53 <command> --json
        ▼
r53diag CLI ──► safety policy (kb/safety.toml) ──► session recorder (sessions/*.jsonl)
        │
        ▼
Backend interface ──┬── EdiabasBackend: ctypes → C:\EDIABAS\Bin\api64.dll  (real car)
                    ├── ReplayBackend: answers from recorded sessions        (offline dev/tests)
                    └── (later) EdiabasLibBackend / raw DS2 for byte-level debugging
        │
        ▼
EDIABAS 7.3 → OBD.ini (COM6) → FTDI K+DCAN cable (pins 7+8 bridged) → car
```

- **Why EDIABAS and not a raw protocol?** The `.prg` SGBDs already contain BMW's job
  logic, scaling and fault text for every R53 module. Re-implementing DS2/KWP2000 would
  throw that away. `api64.dll` was verified to load and run jobs from the installed
  64-bit Python 3.12, so no 32-bit Python or extra runtime is needed.
- **Why a CLI rather than an MCP server?** Claude Code drives CLIs well. A CLI also works
  for any agent and for you directly, and Claude Code's permission rules can gate
  subcommands as a second safety layer. An MCP wrapper can sit on top later if wanted.
- **Language:** Python ≥ 3.11, stdlib only. Hand-edited KB config is TOML (`tomllib`); generated data is JSON.

## CLI surface (first cut)

| Command | What it does | Tier |
|---|---|---|
| `r53 doctor` | Checks: cable present on COM6, FTDI latency, `obd.ini`/`EDIABAS.INI` sane, `api64` loads, battery voltage via EMS2K, which buses answer (pin 7 vs pin 8 → bridge switch hint) | read |
| `r53 scan` | Ident and fault count for every module in `kb/vehicle-profile.json`; flags non-responders | read |
| `r53 ident <mod>` | Full ident (part #, HW/SW, supplier, date) | read |
| `r53 faults [<mod>…\|--all]` | `FS_LESEN`, decoded: code, English text, count, environment conditions, freeze frame, KB notes and links to playbooks | read |
| `r53 status <mod> <job> [args]` | One status job, results with units and normal ranges from the KB | read |
| `r53 live <mod> <job>[,<job>…] --interval 0.5 --duration 60 [--csv]` | Polls status jobs into a timestamped log (warm-up, idle, drive) | read |
| `r53 jobs <mod> [--grep X]` | Offline: job/arg/result catalog for a module, with tier | none |
| `r53 run <sgbd> <job> [args]` | Escape hatch for any job, still subject to the safety policy | per job |
| `r53 clear <mod>` | `FS_LOESCHEN`, after automatically saving the faults first | **confirm** |
| `r53 actuate <mod> <test> …` | `STEUERN_*` tests (fan, fuel pump, gauges sweep, EHPS PWM…) with automatic return-to-normal | **confirm** |
| `r53 baseline save <name>` | Snapshots a set of status jobs as a known-good reference for this car | read |

Output is JSON by default (`--pretty` for humans). Every result includes the raw EDIABAS
result name and value, plus the KB's English label, unit, normal range and verdict.

### Safety policy

The policy is an **allow-list**: any job not classified is blocked.

- **read** — `IDENT*`, `FS_LESEN*`, `IS_LESEN`, `STATUS_*`, `*_LESEN`, `STAT_*`, `_JOBS` and
  similar. Runs freely.
- **confirm** — `FS_LOESCHEN`, `STEUERN_*`, `*_TEST`, `SIA_RESET`, adaptation resets, DSC
  bleed routines. The CLI refuses unless given `--confirm`. Project `.claude/settings.json`
  sets these subcommands to *ask*, so you approve each one in the Claude Code permission
  prompt. Actuations carry max-duration limits and preconditions (e.g. engine off for
  injector tests).
- **blocked** — everything in FINDINGS §4's must-block list. It is never executable, even
  with `--confirm`; the code has no override flag.

### Sessions

Each invocation appends to `sessions/YYYY-MM-DD/<time>-<cmd>.jsonl`. Each record holds the
request, every raw result set, timing, EDIABAS errors, battery voltage, and an optional
EDIABAS `IfhTrace` file. A session can be copied into car-manager
(`vehicles/2006-mini-cooper-s/attachments/diag/`) and linked from an issue's
investigation log. `ReplayBackend` reads these same files, so code and playbooks can be
tested without the car.

## Knowledge base (`kb/`)

| Path | Contents | Source |
|---|---|---|
| `kb/README.md` | Agent entry point: what's here and how to diagnose | written |
| `kb/hardware.md` | Cable, **pin 7/8 switch**, COM6, latency, ignition/KL15, EDIABAS error codes (IFH-0009, IFH-0018…) and fixes | research + car |
| `kb/architecture.md` | Buses (CAN / K-bus / pin 7 / pin 8), KOMBI gateway, protocols, addresses, wake/sleep | TIS |
| `kb/vehicle-profile.json` | **This car's** modules: which SGBD variant answers, part numbers, coding index; generated by `r53 scan --save-profile` | car |
| `kb/modules/<MOD>.md` | Per module: what it does, failure lore, the useful jobs, key results with units/ranges, safe tests | curated over generated |
| `kb/catalog/<SGBD>.json` | Machine-readable job/arg/result catalog with safety tier; used by the CLI | generated (`xtract.exe` / `prgdesc.py`) |
| `kb/faults/<SGBD>.toml` | Fault code → English text (from `FORTTEXTE` German, machine-translated and flagged), P-code mapping (Peake/Mitchell), likely causes, linked playbook | generated + curated |
| `kb/playbooks/*.md` | Step-by-step diagnosis using the tool: **charging system**, **no-crank / EWS**, misfire / rough running, boost/TMAP, fuel trims / lambda, overheating / fan, EHPS pump, ABS/DSC light, airbag light, service (SIA) reset | curated |
| `kb/baselines/*.json` | Known-good readings from this car (cold start, warm idle, 2500 rpm, cruise) | car |
| `kb/glossary.md` | German SGBD vocabulary: FS, HFK, UW, Ort, STEUERN, LESEN, KL15/30/50… | written |
| `kb/safety.toml` | Tier patterns and per-job overrides, actuation limits | written |

Generated files are rebuilt by `tools/build_kb.py`. Curated files are never overwritten;
a generated section sits below a marker line.

## Agent integration

- **This repo's `AGENTS.md`:** how to use the CLI, the safety rules, where the KB lives and
  how to cite it, and the rule to *read before act*.
- **This repo's `.claude/settings.json`:** allow `r53 doctor|scan|ident|faults|status|live|jobs|baseline`;
  ask for `r53 clear|actuate|run`.
- **car-manager `AGENTS.md`:** a short section saying the Mini has a diagnostic tool at
  `projects/r53-diag`, and that diagnostic sessions get summarised into the issue's
  investigation log with the session file attached. Do not duplicate KB content there.
- **Optional `/r53` skill:** runs the standard health check (doctor, scan, faults, key
  status blocks, compare to baseline) and drafts the car-manager note.

## Phases

### Phase 0 — foundation, offline (no car needed) ✅ done 2026-10-02
- [x] Scaffold the repo: `pyproject.toml`, `r53diag/`, `kb/`, `tests/`, `AGENTS.md`, `.gitignore`.
- [x] `ediabas.py`: ctypes wrapper on `api64.dll` with job timeout, result-set parsing into typed
      values, error mapping, and a context manager. Tested against the unplugged cable
      (expected IFH-0018).
- [x] `tools/build_kb.py`: run `xtract.exe` (or the existing `prgdesc.py`) on all R50 SGBDs,
      giving `kb/catalog/*.json`, then the safety-tier classification report. Pull out
      `FORTTEXTE`/`FARTTEXTE`/`ANALOG` tables, giving the translation work list (`kb/translations/`).
- [x] Safety policy and its unit tests: every blocked job in the catalog is unrunnable, and
      every unclassified job is blocked.
- [x] `ReplayBackend`, session recorder, and the CLI skeleton (`doctor`, `jobs`, `scan`, `faults`, `status`).
- [x] Write `kb/hardware.md`, `kb/architecture.md` and `kb/glossary.md` from FINDINGS.

Notes from phase 0:
- The PRG reader decodes the SGBD lookup tables (fault texts, scaling, actuator lists) as well as the job descriptions, so `xtract.exe` isn't needed.
- 51 SGBDs are catalogued. Every job is classified, and the tests enforce that.
- 998 German strings are machine-translated.
- The DME is an MS5150 (EMS2K SGBD); see FINDINGS §3.

### Phase 1 — first car session (engine off, ignition on, battery charger attached if possible)
- [ ] **Cable switch to the pin 7+8 bridged position**, then plug in to confirm COM6.
- [ ] `r53 doctor`, then `r53 scan` with `IfhTrace` on. Repeat with the switch in the other
      position so `kb/hardware.md` records which position works on this car.
- [ ] Resolve module variants (MRS4/MRS5K, BC1/BC1RD, KOMBI50F/KOMBIR50, EWS3/EWS3D) and
      write `kb/vehicle-profile.json`. Confirm DSC/EHPS addresses from the trace.
- [ ] `r53 faults --all`. Record everything; **clear nothing**. Save to car-manager.
- [ ] Charging-system snapshot for the **open no-crank issue**: battery volts from EMS2K
      `STATUS_UBATT` / ENGINE4, KOMBI50F `AIF_BATTMON_*` history, EHPSR50 `STATUS_ANALOG`.
      Check EWS3 `STATUS_EWS` / `FS_LESEN` to rule the immobiliser in or out.
- **Done when** every fitted module answers, the profile is saved, a full fault report is
  attached to car-manager, and the no-crank issue has the diagnostic readings in its log.

### Phase 2 — engine running
- [ ] `r53 live` on EMS2K blocks (ENGINE4/5/9, FUEL_TRIM, MAN_TEST misfire counters).
      Capture a cold-start-to-warm-idle log and a 2500 rpm hold.
- [ ] Save baselines; fill in normal ranges in `kb/modules/EMS2K.md`.
- [ ] Charging voltage under load (lights, blower, rear demist on) to chase the intermittent
      non-charging.
- [ ] EHPS status while turning the wheel (pump temp/current); KOMBI/BC1 status reads.

### Phase 3 — knowledge base build-out
- [ ] English fault tables for EMS2K, DSC_MK60, EHPSR50, MRS4/5K, BC1RD, KOMBI50F, EWS3,
      IHKAR50; review the machine translations.
- [ ] Playbooks, starting with charging, no-crank/EWS, misfire, overheating/fan and EHPS.
- [ ] Cross-check live values against the dashboard project's PT-CAN decoding (0x316 rpm,
      0x329 coolant, 0x545 oil temp).

### Phase 4 — confirmed actions and car-manager integration
- [ ] `clear` and `actuate` with confirmation, pre-read and post-read, and duration limits.
      First targets: radiator fan stages, fuel pump, gauge sweep, EHPS PWM, SIA reset.
- [ ] Push to GitHub, add as a car-manager submodule, add the car-manager `AGENTS.md`
      section, and optionally the `/r53` skill.

### Done since: EdiabasLib backend (2026-10-02)
- [x] `--backend ediabaslib` uses EdiabasLib's open-source drop-in `Api64.dll`, installed by
      `tools/install_ediabaslib.py` into a gitignored `vendor/`. It runs the same SGBDs and cable
      as BMW's runtime, configured through the `apiInitExt` string.
- [x] Works offline (loads, resolves SGBDs, runs init bytecode).
- [ ] **Verify on the car:** `doctor`, then `scan`, run with `--backend ediabaslib --trace`. Compare
      against the BMW-backend results from 2026-10-02.
- [x] Fixed `--trace` on the BMW backend. BMW truncates `TracePath` to 64 characters, so traces
      are now staged in `C:\EDIABAS\TRACE\r53`.

### Later / maybe
- EdiabasLib backend for byte-level traces, if EDIABAS errors get opaque.
- A passive K-bus/CAN monitor using the dashboard project's decoders.
- An MCP server wrapper.

## Risks and open questions

| Risk / question | Mitigation |
|---|---|
| Body modules still silent with pins bridged | Check KL15 is on, check the cable isn't a fake FT232R, try `obd.ini RETRY=OFF`, compare with an EdiabasLib trace |
| `api64.exe` proxy quirks (timeouts, stuck server) | Job timeouts plus killing and restarting `api64.exe` in the wrapper; fall back to 32-bit Python + `api32.dll` if needed |
| Battery drain or low voltage during long sessions | `doctor` checks voltage; warn below 12.2 V; charger recommended |
| An agent clears faults before reading them | `clear` always saves first; the confirm tier means a human approves |
| Licensing — BMW TIS/SGBD dumps and GPL EdiabasLib source in `research/` | **Keep the GitHub repo private**, or gitignore `research/tis`, `research/sgbd_desc` and `research/third_party` if it goes public |
