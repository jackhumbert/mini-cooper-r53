# EHPS — electro-hydraulic power steering pump (SGBD `EHPSR50`)

- **Module key:** `ehps`. **Group:** `D_0031` (address 0x31). **Line:** OBD pin 7.
- **This car:** answered 2026-04-03 as ZF Lenksysteme, BMW # 6770303, HW 25, SW 55.
  Fault memory was empty that day.
- **Background:** the pump sits low at the front left. A well-known R53 failure is its
  cooling fan clogging or failing; the pump then overheats and limits assist to protect
  itself. In July 2026 this car had weak or intermittent steering assist during the
  belt-drive failure. That was probably low system voltage rather than the pump; confirm
  with fault memory.

## Useful jobs

| Job | Gives |
|---|---|
| `IDENT`, `IDENT_EXTENDED`, `READ_ZF_HW_NR` | Identity |
| `FS_LESEN`, `STATUS_FS_LESEN` | Fault memory |
| `STATUS_ANALOG` | Supply `BATTERY_VOLTS`, pump **`TEMPERATURE`** (°C), `MOTOR_CURRENT` and `MOTOR_CURRENT_MAX`, `MOTOR_SPEED` and its setpoint, `PWM_*`, `ENGINE_RUNNING_ANALOG`, `MOTOR_RESISTANCE` |
| `STATUS_IO_LESEN` | Ignition on, engine running, application running, speed control enabled |
| **confirm** `STEUERN_PWM <0-100>` | Force pump duty. Released with `STEUERN_PWM_RESET`, which `r53 actuate` does automatically |

**Diagnosis idea:** log `ehps:STATUS_ANALOG` while turning lock to lock with the engine
running. Watch temperature climb and current draw. Pump temperature after a drive is a
good fan-health indicator (baseline to be captured).
