# KOMBI — instrument cluster (SGBD `KOMBI50F`, alt. `KOMBIR50`)

- **Module key:** `kombi`. **Group:** `D_0080` (address 0x80).
- **Line:** OBD pin 8. The cluster is the **gateway** between the diagnostic line, the K-bus
  and PT-CAN. If it doesn't answer, no K-bus module will, so check the cable's 7+8 bridge
  first ([`../hardware.md`](../hardware.md)).
- **Which SGBD:**
  - `KOMBI50F` is what INPA's R50 ident and NCS use. It has fault memory and the battery
    monitor.
  - `KOMBIR50` (an older variant) has **no** `FS_LESEN` and no battery monitor.
  - `scan` resolves the variant through the group file.

## Useful jobs

All of these are read tier unless marked.

| Job | Gives |
|---|---|
| `IDENT`, `HERSTELLERDATEN_LESEN` | Identity |
| `FS_LESEN` | Fault memory (KOMBI50F) |
| `STATUS_ANALOG` | Fuel sender resistances, ambient temp sensor, light sensor, **battery volts (`AD5`)**, and CAN-received speed / rpm / coolant / consumption |
| `READ_DIGITAL`, `STATUS_IO_*` | Switch inputs, power state, wake-up, K-bus interrupt, LCD, dimmer |
| `STATUS_TANKINHALT_LESEN`, `STATUS_AUSSENTEMP_LESEN` | Fuel level, outside temperature |
| `AIF_BATTMON_STATUS_LESEN`, `AIF_BATTMON_BLOCK_1..8_LESEN` | **Battery monitor:** voltage now and during sleep, plus up to 8 stored low-voltage events (voltage, temperature, odometer, duration) |
| `AIF_GWSZ_LESEN`, `AIF_SIA_DATEN_LESEN`, `ZEITINSPEKTIONSZAEHLER_LESEN` | Odometer and service-interval data |
| **confirm** `STEUERN_ALL_GAUGES "<speedo>;<tacho>;<fuel>;<temp>;<boost>"` (0–100 %) | Gauge sweep test |
| **confirm** `STEUERN_SELBSTTEST`, `STEUERN_GONG`, `STEUERN_LEUCHTE`, `STEUERN_BACKLIGHT`, `STEUERN_LCD_*` | Display, lamp and gong tests |
| **confirm** `SIA_RESET` | Service-interval reset |
| **confirm** `AIF_BATTMON_RESET` | Clears the battery-monitor history. Read it first: it's evidence |

**Blocked:** odometer (`GWSZ_*` offset and reset), coding, test-stamp writes.
