# Airbag — MRS (SGBD `MRS4`, alt. `MRS5K` / `MRS4RD`)

- **Module key:** `airbag`. **Group:** `D_00A4` (address 0xA4). **Line:** K-bus.
- **Variants:** INPA's R50 ident tries `MRS4` ("E46 E53 R50 R53 (Bosch)"). `MRS5K` covers
  later R50/R52/R53. A 2006 build could be either; `scan` resolves which.

## Useful jobs (read tier)

| Job | Gives |
|---|---|
| `IDENT`, `HERSTELLERDATEN_LESEN`, `TYP_LESEN` | Identity |
| `FS_LESEN`, `FS_QUICK_LESEN` | Faults: squib circuits, seat-belt buckles, seat occupancy, satellites |
| `STATUS_LESEN` (MRS4) | Squib-circuit states `ZK0..23`, belt-buckle switches per seat, seat-occupancy (OC3) states |
| `STATUS_ZUENDKREISWIDERSTAENDE` (MRS5K) | Squib-circuit resistances |
| `STATUS_GURTKONTAKTE`, `STATUS_AUSSTATTUNG` (MRS5K) | Belt contacts, configured equipment |

**Safety:** never disconnect airbag components with the ignition on. Treat an airbag
light as a safety item. Clearing airbag faults is confirm tier, and only makes sense after
the cause is fixed. Crash data cannot be cleared by this tool (it is blocked).
