# BC1 — body and lights module (SGBD `BC1RD`, alt. `BC1`)

- **Module key:** `bc1`. **Group:** `D_ZKE_GM`. **Line:** K-bus; BC1 is the K-bus master.
- **What it covers:** MINI's single body computer for exterior and interior lights, central
  locking, windows, wipers and washers, alarm (DWA), heated rear window and hazards. There
  is no separate light module (LCM) or ZKE on the R50/R53.
- **Variants:** `BC1RD` (rev 3.00, "redesign") or the older `BC1`; `scan` resolves which.

## Useful jobs

| Job | Gives |
|---|---|
| `IDENT`, `READ_MANUFACTURER_DATA` | Identity |
| `FS_LESEN`, `IS_LESEN`, `IS_LESEN_ZV` | Faults (171 fault texts in BC1RD) and info memory, including central locking |
| `STATUS_DIGITAL_INPUTS` (~277 flags), `STATUS_DIGITAL_OUTPUTS` | Every switch input: brake switch, bonnet, boot, doors, window switches, light switches, key-lock switches… The best way to test a switch is to watch its flag change |
| `STATUS_ANALOG` | Terminal 30 feeds (`V30*`, `S_KL30*`), window motor currents, battery voltage monitor, blower sense |
| `STATUS_LIGHT_INPUTS` / `STATUS_LIGHT_OUTPUTS` | Lighting inputs and outputs |
| `READ_ALARM_TRIGGER`, `READ_ALARM_MISLOCK` | Why the alarm went off; why locking failed |
| **confirm** `STEUERN_IOSTATES "<ORT>;1"` | Switch one output (name from table `BITS`; `r53 tables bc1 BITS --grep …`). Released with `;0` automatically by `r53 actuate` |
| **confirm** `STEUERN_PWM_OUTPUTS`, `STEUERN_HSS`, `STEUERN_STEPPER_MOTOR`, `STEUERN_ANALOG` | Other output tests |

**Blocked:** key-fob (PLIP) code read/write, the seed/key `START_DIAGNOSTICS`, coding,
memory writes.
