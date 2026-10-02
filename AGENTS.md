# r53-diag — agent guide

You are helping diagnose a **2006 MINI Cooper S (R53, Getrag 6-speed manual, supercharged
W11, Siemens MS5150 DME)** through BMW EDIABAS and a K+DCAN USB cable. This repo is the tool
(`r53diag/`, run as `python -m r53diag`) plus the knowledge base (`kb/`). The car's history
(issues, repairs, logs) lives in the **car-manager** repo, which includes this one as a
submodule at `vehicles/2006-mini-cooper-s/projects/r53-diag`. When working from
car-manager, run commands from this directory.

## Rules (non-negotiable)

1. **Read before act.** Always read faults and status before any clear or actuation. Never
   clear fault memory "to see if it comes back" without first saving and reporting what was
   there. `r53 clear` saves automatically, but you must still report the codes to the user.
2. **Confirm-tier jobs need the user's explicit go-ahead for that specific action.** That
   covers `clear`, `actuate`, and `run … --confirm`. Say what will happen physically, e.g.
   "the radiator fan will run at high speed for 5 s; keep hands clear". Then wait for a yes.
   Never add `--confirm` on your own initiative, and never batch several confirm actions
   under one approval.
3. **Blocked jobs are out of scope.** That means coding, flashing, immobiliser/key, odometer,
   security access, and session/baud changes. Don't try to work around `kb/safety.toml`, edit
   it to unblock something, or call EDIABAS some other way (Tool32, INPA, raw serial) for
   blocked jobs. If one seems necessary, explain why to the user and stop.
4. **Engine-running and driving tests are the user's call.** Ask before anything that needs
   the engine running, and never suggest reading the screen while driving. `live` logging
   with a passenger or a parked car is fine.
5. **Don't invent.** Cite what you rely on: the KB file, the SGBD comment, a session file.
   Translations in `kb/translations/de-en.json` are machine-made; when a German fault text
   matters, show both texts. Mark inferences as inferences.

## The tool

Output is JSON on stdout and progress on stderr. Exit codes: 0 ok · 1 comms/job failure ·
2 refused by policy · 3 usage. Put global flags (`--trace`, `--timeout`, `--compact`,
`--replay`, `--no-record`) **after** the subcommand so permission rules match.

| Command | Use |
|---|---|
| `python -m r53diag doctor` | First thing every session: cable/COM port, config, battery voltage, which diagnostic lines answer |
| `python -m r53diag scan [--save-profile]` | Every module: ident + fault list. Writes `kb/vehicle-profile.json` with `--save-profile` |
| `python -m r53diag faults [dme ews …]` | Fault memory, decoded with English text, counts and environment data. `--info` reads IS_LESEN |
| `python -m r53diag status <module> <JOB> [args]` | One read-only job, decoded (`--raw` for raw sets) |
| `python -m r53diag live dme:STATUS_ANA_ENGINE4 … --interval 1 --duration 120 --csv out.csv` | Poll read-only jobs |
| `python -m r53diag jobs <module> [--grep x] [--tier read] [-v]` | Offline: what a module can do |
| `python -m r53diag tables <module> [TABLE] [--grep x]` | Offline: fault-text / scaling / actuator tables |
| `python -m r53diag modules` / `classify <module> <JOB>` | Offline: the module map; a job's safety tier |
| `python -m r53diag clear <module> --confirm` | **Confirm tier.** Saves faults, clears, re-reads |
| `python -m r53diag actuate <module> <JOB> "<args>" --seconds 5 --confirm` | **Confirm tier.** Drives an output, then releases it (`kb/safety.toml [actuation.release]`) |
| `python -m r53diag run <module> <JOB> [args] [--confirm]` | Escape hatch; still policy-checked |

- **Modules:** `dme, dsc, ehps, kombi, bc1, airbag, ews, ihka, mfl, lws, pdc, rls, shd, lwr,
  dws, oc3, radio, bmbt, dsp, xenon_l, xenon_r, rip, zcs` (see `kb/modules.toml`). An SGBD
  name (`EMS2K`, `KOMBI50F`) also works.
- **Sessions:** every run is recorded to `sessions/YYYY-MM-DD/*.jsonl` (gitignored). Key data
  and VINs are redacted. `--replay <file|dir>` re-runs commands against a recording; that's
  how tests work, and how to re-analyse without the car.

## Diagnosing

1. Read the car's context in car-manager: `vehicles/2006-mini-cooper-s/vehicle.md`, the
   open `issues/`, and recent `log/`.
2. Run `doctor`. If the cluster doesn't answer but the DME does, the cable isn't bridging OBD
   pins 7+8 (`kb/hardware.md`). Fix that first.
3. Run `scan` (or `faults`), then the relevant **playbook** in `kb/playbooks/`. Use the module
   notes in `kb/modules/` for meaning, normal ranges and caveats.
4. Report findings in plain language: codes (English + original), counts, environment
   values, what they suggest, and what to check next.
5. Record it in car-manager, following *its* `AGENTS.md`:
   - Append a dated entry to the issue's *Investigation log* summarising the readings.
   - Copy the session `.jsonl` to `vehicles/2006-mini-cooper-s/attachments/diag/` and
     link it from that entry.
   - Clearing codes or running tests are events too: log them.

## Knowledge base map

- `kb/hardware.md` — cable, pin 7/8 switch, EDIABAS config, error codes
- `kb/architecture.md` — buses, gateways, protocols, addresses
- `kb/modules/*.md` — per-module notes (curated); `kb/modules.toml` — module map (tool input)
- `kb/playbooks/*.md` — step-by-step diagnosis with this tool
- `kb/catalog/*.json` — every job/arg/result + tables per SGBD (generated: `python tools/build_kb.py`)
- `kb/translations/de-en.json` — German→English for SGBD texts (generated, unreviewed)
- `kb/reference/*.md` — our summaries of BMW TIS docs and DTC tables, with source links
- `kb/glossary.md` — German EDIABAS vocabulary (FS, HFK, UW, STEUERN …)
- `kb/vehicle-profile.json` — which variant of each module this car has (from `scan`)
- `kb/baselines/` — known-good readings from this car (add as they're captured)
- `research/FINDINGS.md` — how all this was worked out, with sources

## Developing

- **Stack:** Python ≥ 3.11, stdlib only. The tests are offline:
  `python -m unittest discover tests`.
- **Safety changes:** run `tools/build_kb.py` and the tests after editing
  `kb/safety.toml`. The tests assert that every catalogued job is classified and every
  write is blocked.
- **Adding a module:** add it to `kb/modules.toml`, then rebuild the KB.
- **Commits:** commit per change with clear messages, following the car-manager convention
  of working on `main`.
