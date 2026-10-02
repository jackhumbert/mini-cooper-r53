# DME — engine control (Siemens MS5150, SGBD `EMS2K`)

- **Module key:** `dme`. **SGBD:** `EMS2K.prg` (rev 1.15). **Group:** `D_0013` (address 0x13).
- **Line:** OBD pin 7, KWP2000\* at 9600 baud.
- **This car:** answered 2026-04-03 as Siemens, BMW # 7557395, HW 1, SW P1, coding index 4,
  diag index 38, built week 42/2006.
- **Which ECU:** most likely an **MS5150**, the 2005+ facelift unit. INPA labels the menu
  entry "EMS2K, EMS5150 for Pentagon". BMW serves it with the EMS2000 SGBD, so the jobs
  below apply. TIS and DTC material describing the EMS2000 is close, but not guaranteed
  exact. See [`../reference/engine-management.md`](../reference/engine-management.md).

## Engine facts that shape diagnosis (Cooper S)

- There is **no MAF**. Load comes from **two TMAP sensors**: `MAP_UP` before the
  supercharger and `MAP` after the supercharger and intercooler. `STAT_MAF_KGH` is a
  *calculated* airflow.
- Misfire detection uses crankshaft speed. Flywheel/sensor-wheel adaptation
  (`STATUS_GEBERRAD_ADAPTION`) must be learnt for it to work properly.
- One upstream and one downstream O2 sensor (bank 1). Fuel trims are additive (idle) and
  multiplicative (load).

## Useful jobs

All of these are read tier unless marked.

| Job | Gives |
|---|---|
| `IDENT`, `IDENT_EXTENDED`, `CONFIG_BYTES_LESEN` | Identity; coding config. Includes `ALTERNATOR_TYPE`: Denso 105 A / Valeo 120 A |
| `FS_LESEN` | Fault memory: code, text, count (`F_HFK`), fault types, up to 5 environment values |
| `STAT_FREEZEFRAME` | OBD freeze frame |
| `STATUS_ANA_ENGINE4` | Coolant `TCO`, intake air `TIA`, `MAP`, `MAP_UP`, throttle `TPS`/`TPS_MTC_1/2`, pedal `PV_AV`, O2 volts up/down, `VB_RLY`/`VB_KEY` battery |
| `STATUS_ANA_ENGINE9` | Battery `VB`, speed `VS`, rpm `N`, gear, purge duty `CPPWM`, calculated load `LOAD_CLC` |
| `STATUS_ANA_ENGINE7` | Calculated airflow `MAF_KGH`, MAP setpoints, idle target `N_SP_IS`, throttle adaptation |
| `STATUS_ANA_ENGINE5` | Knock: `KNKS_*`, `KNK_EGY_0`; per-cylinder ignition angle `IGA_IGC_0..3`, ignition setpoint |
| `STATUS_ANA_ENGINE2` | Purge state, **alternator load `ALTER` (%)** |
| `STATUS_ANA_FUEL_TRIM` | Lambda `LAM_MV_1`, lambda correction `TI_LAM_1`, additive and multiplicative adaptation |
| `STATUS_ANA_MAN_TEST` | One-shot snapshot of everything above, plus **misfire counters `MIS_B0..B3`** (cylinders 1–4) and catalyst/LDP results |
| `STATUS_ANA_OBD2`, `STATUS_IO_READY_CODE` | OBD readiness monitors |
| `STATUS_IO_ENGINE1/2` | Digital flags: crank-signal error, limp-home, clutch, and others |
| `STATUS_IO_EWS`, `STATUS_ANA_EWS` | Immobiliser handshake flags and counters (see [`ews.md`](ews.md)) |
| `STATUS_SYSTEMCHECK_LAUFUNRUHE` | Rough-running values per cylinder |
| `STATUS_UBATT`, `STATUS_MOTORTEMPERATUR`, `STATUS_AN_LUFTTEMPERATUR`, `STATUS_MOTORDREHZAHL` | Single values |
| **confirm** `STEUERN_ACTUATOR "<NAME>;7"` | Actuator test. NAME from table `ACTUATOR_TEST`: `MAIN_RELAY`, `FUEL_PUMP`, `AC_COMPRESSOR`, `FAN_RELAY_LOW/MED/HIGH`, `CANISTER_PURGE`, `THROTTLE_ACT`, `LEAK_DETECTION`, `PRIME_FUEL`, `INJECTOR_1..4`, `UPSTR_O2_HEAT`, `DWSTR_O2_HEAT`. CONTROL 7 = adjust, 1 = report, 0 = return to ECU. The release (`;0`) is automatic in `r53 actuate` |
| **confirm** `STEUERN_ADAPTIVE_VALUES "<NAME>"` | Reset adaptations: `ALL_VALUES`, `MAP`, `KNOCK_CONTROL`, `LAMBDA`, `MISFIRING`, `IDLE_SPEED`… (table `ADAPTIVE_VALUES`). Do it after repairs, not as a diagnosis |
| **confirm** `LDP_TEST`, `START_CAT_TEST`, `START_MAN_TEST`, `GIB_SELF_TEST` | Routine tests |
| **confirm** `FS_LOESCHEN` | Clear faults (use `r53 clear dme --confirm`) |

**Tables:** `FORTTEXTE` (250 fault codes), `FARTTEXTE` (fault types), `FUMWELTMATRIX`
(which environment values each fault stores), `FREEZEFRAME`, and `ANALOG`/`DIGITAL`
(scaling for every signal), all via `r53 tables dme <TABLE>`.

**Blocked:** flashing, `WRITE_MEMORY`, immobiliser seed learn/resync, coding, and
`STEUERN_APPLICATION_CORRECTION` (CO/idle trims).

## Watch-items on this car

- **July 2026 harmonic-balancer failure:** the car overheated, lost charging and entered
  limp mode. Fault memory from then may still be stored. Read it and record it before
  anything clears it.
- **Charging:** see [`../playbooks/charging-system.md`](../playbooks/charging-system.md).

## Normal ranges

*To be captured from this car into `kb/baselines/`.*
