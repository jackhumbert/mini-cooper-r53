# Playbook: charging system / battery voltage

Use this for:

- a battery that goes flat, slow or no crank;
- a "not charging" voltage reading (≈12.6–12.8 V with the engine running);
- a charge warning light;
- modules dropping out.

It is written for this car's **intermittent** charging fault: 12.8 V running on 2026-09-29,
14.1 V on 2026-09-30. See car-manager `issues/2026-09-29-no-crank.md`.

## What the car can tell you

| Source | Job → result | Meaning |
|---|---|---|
| DME | `STATUS_UBATT` → `STAT_UBATT_WERT` | Battery voltage *after the DME main relay* (V) |
| DME | `STATUS_ANA_ENGINE4` → `STAT_VB_RLY_WERT`, `STAT_VB_KEY_WERT` | Voltage after main relay / after ignition key |
| DME | `STATUS_ANA_ENGINE2` → `STAT_ALTER_WERT` | **Alternator load** (%): the DME's reading of the alternator's load/DFM signal. 0 % with the engine running while voltage sags would point at the alternator or its wiring (inference — confirm against a known-good baseline) |
| DME | `CONFIG_BYTES_LESEN` → `ALTERNATOR_TYPE` | Fitted alternator per coding: Denso 105 A (0) / Valeo 120 A (1) |
| KOMBI | `STATUS_ANALOG` → `STAT_AD5_BATTERY_VOLTS_WERT` | Cluster's battery voltage |
| KOMBI | `AIF_BATTMON_STATUS_LESEN` | Current voltage, **last voltage during sleep mode**, number of low-voltage events stored |
| KOMBI | `AIF_BATTMON_BLOCK_1_LESEN` … `_8_` | **History of low-voltage events.** Each has voltage, ambient temp, odometer, days since service and duration. This shows *when* the battery was run down |
| EHPS | `STATUS_ANALOG` → `STAT_BATTERY_VOLTS_WERT`, `STAT_MOTOR_CURRENT_WERT` | Voltage at the power-steering pump, and its current draw. The pump is the biggest electrical load after the starter and fan |
| BC1 | `STATUS_ANALOG` → `STAT_AIP_BATT_VOLTS_MON_WERT`, `STAT_V30*` | Body module's view of terminal 30 feeds |
| DSC | `STATUS_SENSOREN` → `STAT_SPANNUNG_KLEMME_30_WERT` | DSC's terminal 30 voltage |

The KOMBI battery-monitor jobs exist in **KOMBI50F** only, not KOMBIR50. `r53 scan`
records which cluster variant this car has.

## Procedure

1. **Engine off, ignition on.** Run `r53 doctor` and note the battery voltage.
2. **Pull the battery-monitor history.**
   ```
   python -m r53diag status kombi AIF_BATTMON_STATUS_LESEN
   python -m r53diag status kombi AIF_BATTMON_BLOCK_1_LESEN    # repeat for 2…N (N = STAT_ANZAHL_BLOECKE)
   ```
   Low-voltage events at specific odometer readings let you match drain episodes to dates
   in the car-manager logs.
3. **Read faults** on DME, KOMBI and EHPS: `python -m r53diag faults dme kombi ehps`.
   Look for voltage, supply or alternator texts.
4. **Engine running at idle.** Compare voltage at three points: DME, KOMBI and EHPS. A
   disagreement of more than ~0.3 V between modules suggests a ground or feed problem;
   all low together points to supply.
   ```
   python -m r53diag live dme:STATUS_ANA_ENGINE4 dme:STATUS_ANA_ENGINE2 ehps:STATUS_ANALOG kombi:STATUS_ANALOG --interval 1 --duration 120 --csv idle.csv
   ```
   Healthy charging is roughly 13.8–14.6 V; check this against the car's own baseline
   once captured.
5. **Under load.** Repeat with headlights, blower on max and rear demist on, and turn the
   steering wheel (EHPS load). Watch for voltage collapse together with `STAT_ALTER`
   behaviour.
6. **Make the intermittent fault happen.** Log during a cold start and a heat-soaked
   restart. The July harmonic-balancer failure overheated the front of the engine, so heat
   damage to the alternator is plausible. Then wiggle-test the alternator plug and B+
   cable while logging; this is a two-person job.

## Interpreting results

| Pattern | Likely area |
|---|---|
| Low voltage at every module, `STAT_ALTER` ~0 % with the engine running | Alternator not excited / regulator / alternator plug or wiring |
| Alternator B+ voltage (multimeter) high but modules low | Cable or connection between alternator and battery: the shared starter main post (Pelican notes), fusible link, or ground strap |
| Voltage normal, then drops when warm | Failing regulator or diodes. Heat-related |
| Battery-monitor history shows repeated sleep-mode lows | Parasitic drain or a weak battery. Also a cause of no-crank |

## Record

Copy the session JSONL and CSVs to car-manager `attachments/diag/`. Add an
investigation-log entry with the voltages, `STAT_ALTER`, the battery-monitor events and a
conclusion.
