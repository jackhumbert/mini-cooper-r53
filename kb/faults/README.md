# Fault-code notes

One TOML file per SGBD, for example `EMS2K.toml`. `r53 faults` attaches a matching
entry to each decoded fault under `"kb"`. Keys are the code exactly as the tool prints
it (`0x113C`).

```toml
[codes."0x113C"]
summary = "Intake air temperature (TIA) signal stuck"
likely = ["TMAP sensor (post-supercharger) connector/wiring", "sensor failure"]
playbook = "playbooks/…"
seen = ["2026-10-xx — note, link to car-manager issue"]
source = "SGBD text + …"
```

- Add a note when a code actually shows up on this car, or when a source documents it well.
- Don't bulk-paste generic DTC lists here. Those live in `catalog/` (SGBD text) and in
  `reference/obd-p-codes.md`.
