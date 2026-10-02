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
| *(none yet)* | | | | |
