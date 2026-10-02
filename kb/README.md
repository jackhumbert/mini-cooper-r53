# Knowledge base

Everything here is about **this car**: a 2006 MINI Cooper S (R53), Getrag 6-speed manual,
Siemens MS5150 DME. The general R50/R53 facts apply to the whole family.
**Curated** files are written by people or agents and edited by hand. **Generated** files
are rebuilt by `python tools/build_kb.py`; don't edit those.

| Path | Kind | Contents |
|---|---|---|
| [`hardware.md`](hardware.md) | curated | Cable, **OBD pin 7/8 switch**, EDIABAS/obd.ini config, ignition, error codes and fixes |
| [`architecture.md`](architecture.md) | curated | Buses, the KOMBI gateway, protocols, module addresses, PT-CAN broadcast frames |
| [`glossary.md`](glossary.md) | curated | German EDIABAS vocabulary (FS, HFK, UW, STEUERN, KL15 …) and result-naming conventions |
| [`modules.toml`](modules.toml) | curated (tool input) | Module map: SGBD variants, group files, line, fitment |
| [`safety.toml`](safety.toml) | curated (tool input) | Which jobs are read / confirm / blocked, plus actuator release rules |
| [`modules/`](modules/) | curated | Per-module notes: what it does, the useful jobs, caveats, this car's history |
| [`playbooks/`](playbooks/) | curated | Step-by-step diagnosis with the tool |
| [`reference/`](reference/) | curated | Our own summaries of BMW TIS documents and DTC tables, linking to the originals |
| [`faults/`](faults/) | curated | Notes on specific fault codes: likely causes, playbook links. Shown by `r53 faults` |
| [`baselines/`](baselines/) | captured | Known-good readings from this car |
| `vehicle-profile.json` | captured | Which SGBD variant each module uses, with ident data (`r53 scan --save-profile`) |
| [`catalog/`](catalog/) | generated | Every job, argument, result and table for each R50/R53 SGBD, with safety tier |
| [`translations/`](translations/) | generated | German→English for SGBD texts (machine-translated, unreviewed) |

**Playbooks so far:**
[first connection](playbooks/first-connection.md) ·
[charging system](playbooks/charging-system.md) ·
[no crank](playbooks/no-crank.md)

**Module notes so far:**
[DME](modules/dme.md) · [EWS](modules/ews.md) · [KOMBI](modules/kombi.md) ·
[EHPS](modules/ehps.md) · [DSC](modules/dsc.md) · [BC1](modules/bc1.md) ·
[Airbag](modules/airbag.md)

**Confidence:**

- The KB states where each fact comes from: the SGBD (BMW's own job descriptions), TIS,
  forum reports, or this car.
- Anything inferred is marked as inferred.
- Until the first session on the car is recorded, nothing about module variants, addresses
  or normal ranges is confirmed.
