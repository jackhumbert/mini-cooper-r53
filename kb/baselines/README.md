# Baselines

Known-good readings from this car, used for comparison when something feels off.

Capture them with `r53 live … --csv`, or keep the session JSONL. Store each one here as
`YYYY-MM-DD-<condition>.csv` (or `.jsonl`) and add a row to the table below.

Conditions to capture:

- cold start to warm idle (DME `STATUS_ANA_ENGINE4` + `FUEL_TRIM` + `ENGINE2`)
- warm idle with electrical load
- 2500 rpm hold
- EHPS lock-to-lock
- battery voltage with ignition on and engine off

| File | Date | Odometer | Condition | Notes |
|---|---|---|---|---|
| [`2026-10-02-cold-start-idle.csv`](2026-10-02-cold-start-idle.csv) | 2026-10-02 | 149,216 mi (240,140 km) | Cold start, first ~60 s of idle. Engine off overnight, ambient about 25 °C (cluster). 54 samples of DME `STATUS_ANA_ENGINE4`/`ENGINE2`/`ENGINE9`/`FUEL_TRIM`, EHPS `STATUS_ANALOG`, KOMBI `STATUS_ANALOG` | Coolant 23→37 °C. Idle 1,000–1,210 rpm. **14.0 V** at DME/EHPS/KOMBI. Alternator load 7–93 % (mean 47 %). Lambda correction mean −3.5 %. Adaptations: additive +0.17, multiplicative +2.4 %. Upstream O2 switching 0.08–0.87 V. MAP ≈ MAP_UP ≈ 390–460 hPa. EHPS 26–27 °C, 13.7 A, ~3,570 rpm |
| (session snapshot) | 2026-10-02 | 149,216 mi | Same start, a few minutes later | Coolant 58 °C. Idle 784 rpm. **Canister purge active** (state 3, 20 % duty). Fans off. Alternator load 25 %. EHPS 32 °C, 13 A |
