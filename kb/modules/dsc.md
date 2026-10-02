# DSC — ABS / ASC / DSC (Teves MK60, SGBD `DSC_MK60`)

- **Module key:** `dsc`. **Line:** OBD pin 7, KWP2000 services. The bus address is not
  confirmed; capture it with `scan --trace`.
- **This car:** answered 2026-04-03 as Temic, BMW # 6765286, HW 0.6, coding index 11.

## Useful jobs

| Job | Gives |
|---|---|
| `IDENT`, `IDENT_VIN`, `IDENT_PRODUCTION_DATA` | Identity (VIN is redacted by the tool) |
| `FS_LESEN`, `FS_LESEN_DETAIL` | Faults, including symptom, readiness, present/stored and warning-lamp status per fault |
| `STATUS_RADGESCHWINDIGKEIT` | Wheel speeds FL/FR/RL/RR. Compare while rolling to find a dead or erratic wheel-speed sensor |
| `STATUS_SCHALTER` | Brake-light switch, handbrake, DSC button, brake-fluid level switch, RPA reset button |
| `STATUS_SENSOREN` | Yaw rate, lateral acceleration, both brake-pressure sensors, sensor temperature, Uref, pump and terminal 30 voltages |
| `STATUS_SENSOREN_OFFSET`, `STATUS_LWS_LI_RE_MAX` | Sensor offsets, steering-angle end stops |
| `STATUS_CAN_DME_1/2/4_LESEN`, `STATUS_CAN_LWS_1_LESEN` | What DSC receives over CAN from the DME and steering-angle sensor |
| **confirm** `STEUERN_DIGITAL`, `STEUERN_DIGITAL_WARNLAMPEN`, `STEUERN_DIGITAL_BLS` | Valve, lamp and brake-light tests |
| **confirm** `R50_ABS_BLEEDMASTER_FA/RA`, `R50_ASC_DSC_BLEEDMASTER_FA/RA`, `NA_ENTLUEFTUNG_LI/RE`, `VAKUUM*` | Brake-bleed routines. Only during a bleed procedure, with the service manual |
| **confirm** `RPA_RESET` | Tyre-deflation (RPA) reset |

**Blocked:** sensor calibration (`*_ABGLEICHEN`), coding, and VIN/production-data writes.
