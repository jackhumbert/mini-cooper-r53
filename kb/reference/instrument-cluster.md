# Instrument cluster (summary)

**Source:** BMW of North America TIS, *2002-05 ACCESSORIES & EQUIPMENT Instruments – Repair
Instructions – Cooper (1.6L) R50/W10 & Cooper S*.
<http://wtxmc.org/MiniCooperDocs/INSTRUMENT%20CLUSTER.pdf> (local
`research/tis/INSTRUMENT_CLUSTER.pdf`). This is our own summary. The original is linked, not
redistributed.

## What the document covers

It is a **removal and installation** procedure only. It contains no diagnostic or functional
description. The useful facts are:

| Procedure | Note |
|---|---|
| 62 11 400 Instrument on the steering column (all versions) | Held by screws on the back, one plug connection. **After replacement: programming/coding is required.** |
| 62 13 050 Clock (headliner) | Release the housing from the headliner, unplug, two screws |
| 62 21 000 Instrument carrier (centre speedometer pod) | Remove the centre dash trim first. Screws + plugs. **After replacement: programming/coding is required.** |
| 62 21 020 Navigation instrument carrier | As above, for nav cars. **Programming/coding required.** |

## Diagnosis-relevant points (from other sources)

The cluster's diagnostic role is covered by other documents. It is collected here for convenience:

- On the R50/R53 the cluster (TIS "IKE"; EDIABAS `KOMBI50F` / `KOMBIR50`, address 0x80) is the
  **gateway** between PT-CAN, the K-bus and the DS2 diagnostic line. It is one of the two **120 Ω
  CAN terminators**. [BUS SYSTEM](bus-system.md)
- **Cluster or gateway replacement needs coding.** Coding is out of scope for this tool (NCS
  Expert territory), and coding jobs are blocked by the safety policy.
- The cluster passes low-fuel information to the DME for misfire evaluation, and relays A/C
  requests from the K-bus to the DME over CAN. [ENGINE MANAGEMENT](engine-management.md)
- The cluster broadcasts VIN, odometer, fuel level, ambient temperature and lamp states on PT-CAN
  (0x610–0x61F). See [architecture §6](../architecture.md#6-pt-can-broadcast-frames-useful-for-cross-checking).
- `KOMBIR50` has **no `FS_LESEN`** job. `KOMBI50F` has fault memory and `AIF_BATTMON_*`
  battery-monitor history (`research/FINDINGS.md`). Which variant this car has is still to be
  resolved.

> The PDF is mostly photographs. If a functional/diagnostic cluster document exists in the
> wtxmc.org set, it should replace this summary.
