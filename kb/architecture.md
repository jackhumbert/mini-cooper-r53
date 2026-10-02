# R53 bus architecture

This page describes how the modules of the 2006 MINI Cooper S (R53) are networked, and which path
a diagnostic request takes to reach each one.

**Source tags.** `[TIS-BUS]` is TIS *Bus Systems – Overview*
(<http://wtxmc.org/MiniCooperDocs/BUS%20SYSTEM.pdf>). `[TIS-EMS]` is TIS *Engine Management –
Overview* (<http://wtxmc.org/MiniCooperDocs/EMS%20OVERVIEW.pdf>). `[FAQ]` is BMW's EDIABAS FAQ.
`[local]` means read from SGBDs or group files on this PC. `[src]` means open-source code or docs.
`[dash]` means the owner's own PT-CAN reverse engineering (`mini_cooper_dashboard_redo`).
`[car]` means observed on this car. `[inference]` means our own reasoning, unverified.

TIS (written for BMW technicians) calls the instrument cluster **IKE**. The EDIABAS SGBDs call it
**KOMBI**. They are the same unit.

```
                     ┌──────────── PT-CAN 500 kbit/s (twisted pair, 120 Ω at each end) ───────────┐
                     │                                                                             │
                 DME (MS5150)  ── DSC MK60 ── steering-angle (LWS) ── [auto trans, if fitted] ── KOMBI/IKE
                     │                │                                                            │  gateway
 OBD pin 7 ──────────┴────────────────┴── EHPS ─── (D-bus, K-line 9600 baud, ISO 9141)             │
                                                                                                    │
 OBD pin 8 ── DS2 line 9600 baud ─────────────────────────────────────────────────────────────────┤
                                                                                                    │
                     K-bus 9600 baud (single wire, BC1 is master) ─────────────────────────────────┘
                     BC1 · EWS3 · MRS airbag · IHKA · MFL · PDC · RLS · SHD · radio/nav · LWR · DWS …
```

`[TIS-BUS]` covers the topology and speeds. The pin numbers come from `[src]`/`[forum]` (see
[hardware.md §2](hardware.md#2-obd-ii-socket-pins-used-by-r50r53)). The per-module bus assignment is
`[local]`/`[car]`.

## 1. PT-CAN (powertrain CAN)

| Property | Value | Source |
|---|---|---|
| Speed | **500 kbit/s** (the fastest bus in the car) | [TIS-BUS] |
| Wires | Unshielded twisted pair. CAN-H yellow/black, CAN-L yellow/brown | [TIS-BUS] |
| Topology | Linear main line with stubs **≤ 1 m**. Any untwisted section must be **≤ 4 cm** | [TIS-BUS] |
| Termination | **120 Ω inside the DME ("EMS 2000") and inside the cluster ("IKE")**. They are in parallel, so **60 Ω** measured between H and L with the power off and all modules connected | [TIS-BUS] |
| Non-terminating modules | 10–50 kΩ between H and L, measured at the unplugged module | [TIS-BUS] |
| Levels | Both lines idle at 2.5 V (recessive = logic 1). Dominant (logic 0): H about 3.5 V, L about 1.5 V | [TIS-BUS] |
| Users | DME, DSC/ABS, cluster. Automatic transmission on automatics. Steering-angle sensor (it broadcasts 0x1F5; see §6) | [TIS-BUS] [TIS-EMS] [dash] |
| Diagnostic use | **None directly.** Diagnosis goes over the K-lines. CAN problems show up as "timeout" or "CAN" faults stored in the other modules | [TIS-BUS] |

CAN messages carry no address. Each message ID identifies its content and also sets its priority.
If a message can't be sent, the module stores it and resends it later. `[TIS-BUS]` A module that
keeps failing to reach another one stores a **timeout** fault. `[TIS-BUS]`

**Quick plausibility check from TIS:** a plausible tachometer and coolant gauge mean the DME↔cluster
CAN link works. `[TIS-BUS]`

## 2. K-bus (body bus)

| Property | Value | Source |
|---|---|---|
| Speed | **9600 bit/s**, single wire (white/red/yellow), swings 0–12 V | [TIS-BUS] |
| Segments | K-bus I and K-bus II. Electrically one bus, spliced inside BC1. A short on one segment kills both; an open circuit only isolates the modules beyond it | [TIS-BUS] |
| Master | **BC1** supplies the bus and sequences messages. It has the highest priority | [TIS-BUS] |
| Sleep | **60 s after ignition off**. Rests at 12 V while asleep | [TIS-BUS] |
| Access | Event-driven. A sender waits for an idle bus, then listens for its own message echoed back. If the echo doesn't come back correctly, a higher-priority sender collided with it, so it waits and retries. It gives up after **5 failed attempts** | [TIS-BUS] |
| Topology | "Tree". One module failing doesn't take down the bus, unless the failure shorts the line or a software fault jams it | [TIS-BUS] |
| Diagnostic access | Through the cluster gateway from the DS2 line (OBD pin 8) | [TIS-BUS] |

A short to ground looks to most modules like an idle bus. Only the master and standby units log it.
A short to B+ makes senders retry 5 times and then give up. `[TIS-BUS]`

## 3. Diagnostic lines

TIS describes "the diagnostic bus" as two separate single-wire lines on the 16-pin socket, both at
**9600 baud**. They are only active while a tester is talking. `[TIS-BUS]`

| Line | OBD pin | Reaches | Protocols seen |
|---|---|---|---|
| **D-bus** ("ISO 9141-2 OBD II") | 7 | Emissions/powertrain units: DME, DSC, EHPS (and the auto transmission) | KWP2000\* (DME), KWP2000-style (DSC, EHPS); generic OBD-II for scan tools |
| **DS2 protocol bus** | 8 | The cluster (KOMBI/IKE) and, through it, every K-bus module | DS2 |

The two pins must be bridged in the cable for one adapter to reach both lines. See
[hardware.md §3](hardware.md#3-the-switch-on-the-cable).

**KOMBI is the gateway.** It has a processor that converts messages between CAN, the K-bus and
the diagnostic line `[TIS-BUS]`. TIS gives this example: the DSC computes road speed and sends it on
CAN; the cluster re-sends it on the K-bus to BC1 (speed-dependent wipers) and the radio
(speed-dependent volume) `[TIS-BUS]`. The DME's information about non-CAN units, such as the A/C
request from IHKA, also passes through the cluster. `[TIS-EMS]`

## 4. Protocols

**You don't need to implement these.** EDIABAS and the SGBDs handle all framing. This section is
only for reading `IfhTrace` output, or for a future raw backend.

All diagnostic traffic runs on a single-wire K-line at **9600 baud, 8E1** (8 data bits, even
parity, 1 stop bit) `[TIS-BUS]` `[src]`. The line is half-duplex, so **the adapter receives an echo
of every byte it sends**. EDIABAS discards the echo. `[src]` `[TIS-BUS]` (this is how K-bus
arbitration works)

### DS2 (body modules behind KOMBI)

```
request : [addr] [len] [data …] [xor]
response: [addr] [len] [status] [data …] [xor]
```

- `len` counts the **whole telegram**, including the address, the length byte itself and the
  checksum. `[src]`
- The checksum is the XOR of all preceding bytes. `[src]`
- Status `0xA0` = OK / acknowledged. `[src]` (In other DS2 implementations, `0xA1` = busy,
  `0xA2` = rejected/bad parameter and `0xFF` = not acknowledged. `[src]`, not verified on this car.)
- No init or wake-up sequence is needed. `[src]`
- Example: `KOMBI50F` at `0x80` (group file `D_0080.GRP`). `[local]`

### KWP2000\* (DME / EMS2K)

- BMW's K-line variant of KWP2000 (ISO 14230 framing), with EDIABAS group file `D_0013`, so DME
  address **0x13**. `[local]` `[src]`
- Frame: `[fmt] [tgt] [src] ([len]) [service + data …] [checksum]`. `[src]`
  ⚠ `research/FINDINGS.md` calls the checksum "xor". ISO 14230 normally uses an **8-bit additive
  (sum) checksum**. Not verified. Confirm from an `IfhTrace` before relying on either.
- The DME also answers **generic OBD-II** (ISO 9141-2, 5-baud init) on pin 7, which is how
  third-party scan tools read P-codes. `[TIS-EMS]` `[src]`

### KWP2000-style services (DSC MK60, auto transmission, airbag)

The job comments in `DSC_MK60` and `GSF21` name standard KWP2000 services: `$1A`
ReadECUIdentification, `$17/$18` read DTCs, `$14` clear, `$21/$22` read data, `$30` I/O control,
`$31` routines, `$3E` tester present. `MRS5K` mixes "DS2 init" with KWP2000 `$22`. `[local]`
DSC's exact address is not confirmed yet. It will come from an `IfhTrace`.

## 5. Modules, SGBDs and addresses

For pre-E65 cars, the group file name `D_00xx.GRP` encodes the ECU address `xx` `[FAQ 3.15]`. The
addresses below are taken from the group files `[local]`. "?" means not yet confirmed.

| Module | What it does | SGBD (variants) | Group | Addr | Reached via | Fitted on this car? |
|---|---|---|---|---|---|---|
| DME | Engine management. **Siemens MS5150** (facelift); TIS describes its predecessor EMS2000 | `EMS2K` | D_0013 | 0x13 | pin 7 | yes [car] |
| EHPS | Electro-hydraulic power-steering pump (ZF) | `EHPSR50` | D_0031 | 0x31 | pin 7 | yes [car] |
| DSC / ABS / ASC | Brakes and stability (Teves MK60) | `DSC_MK60` | (D_ABSKWP) | ? | pin 7 | yes [car] |
| Auto transmission | Aisin 6-speed | `GSF21` | D_EGS | ? | pin 7 | no (manual) |
| KOMBI (IKE) | Instrument cluster, **gateway** | `KOMBI50F` / `KOMBIR50` | D_0080 | 0x80 | pin 8 | variant TBD |
| BC1 | Body controller, K-bus master (lights, wipers, locking, A/C request) | `BC1RD` / `BC1` | D_ZKE_GM | 0x00 | K-bus | variant TBD |
| Airbag | Restraint system | `MRS4` / `MRS5K` | D_00A4 | 0xA4 | K-bus | variant TBD |
| EWS 3 | Immobiliser | `EWS3` / `EWS3D` | D_0044 | 0x44 | K-bus | yes |
| IHKA | Automatic climate control | `IHKAR50` / `IHKAR50R` | D_005B | 0x5B | K-bus | ? |
| MFL | Steering-wheel buttons | `MFLR50` | D_0050 | 0x50 | K-bus | ? |
| LWS | Steering-angle sensor | `LWS5_1B` | D_0057 | 0x57 | ? | ? |
| PDC | Park distance control | `PDCACT` | D_0060 | 0x60 | K-bus | ? |
| RLS | Rain/light sensor | `RLS_DS2` / AIC | D_00E8 | 0xE8 | K-bus | ? |
| SHD | Sunroof | `SHD46` | D_0008 | 0x08 | K-bus | ? |
| LWR | Headlight levelling | `LWR2A` | D_009A | 0x9A | ? | ? |
| DWS | Tyre-deflation warning | `DWS` | D_0070 | 0x70 | ? | ? |
| OC3 | Seat occupancy (US) | `OC3` | D_0074 | 0x74 | ? | ? |
| Radio / nav / DSP / BMBT | Audio and navigation | `RADIO`, `NAVMK3`, `DSP_R50`, `BMBTR50` | … | 0x68 / 0x7F / 0x6A / 0xF0 | K-bus | ? |
| Vehicle ID | Reads the ZCS (central coding key), VIN, production date | `ZCS_R50` | — | — | — | — |

Variants still to resolve on the car: MRS4 vs MRS5K, BC1 vs BC1RD, KOMBI50F vs KOMBIR50
(KOMBIR50 has no `FS_LESEN`), EWS3 vs EWS3D. NCS `R50SGFAM.DAT` lists EMS2K, KOMBI50F, DSC_MK60,
MRS4, BC1 and C_EWS3. `[local]`

**About the DME.** This car's DME identifies through `EMS2K.prg` as Siemens, part 7557395,
diagnostic index 38, built in week 42/2006 `[car]`. INPA's `R50.ENG` menu labels the entry
"EMS2K, EMS5150 for Pentagon" (added 15.11.2004) `[local]`. So the unit is most likely a
**Siemens MS5150**, served by the same `EMS2K` SGBD as the earlier EMS2000. Our reading of
"Pentagon" as the name of the facelift engine programme is **an inference**.

### Hard-wired links that bypass the buses

The EMS2000 description notes that the most critical signals are hard-wired, not bussed. `[TIS-EMS]`

- **EWS → DME:** a dedicated one-way single-wire line carrying an encrypted rolling code, with a
  time limit. The DME only enables injection and ignition after receiving a valid code.
- **MRS → DME:** crash signal that cuts the fuel pump (from 09/2002 production; earlier cars used an
  inertia switch).
- **MFL → DME:** cruise-control buttons on a single-wire serial line.
- **Alternator → DME:** PWM load signal used for idle control.

## 6. PT-CAN broadcast frames (useful for cross-checking)

These come from the owner's own sniffing of this car's PT-CAN, summarised from
`mini_cooper_dashboard_redo/lib/r53/r53.dbc` and `src/can_data.hpp` `[dash]`. Many names and
scalings follow the well-known E46 PT-CAN layout. They are **not BMW-documented for the R53**.
Use them to sanity-check diagnostic values (rpm, coolant, oil temperature, speed), not as ground
truth. Bit positions use DBC little-endian start bits.

| ID | Name | Sender (likely) | Key signals (start bit \| length → scaling) |
|---|---|---|---|
| 0x153 | ASC1 | DSC | `VehicleSpeed` 11\|13 × 0.0625 → km/h. ASC/MSR torque requests 24\|8 / 32\|8 × 0.390625 %. ABS/ASC lamp and activity bits 0–10 |
| 0x1F0 | ASC2 | DSC | Four wheel speeds, 12 bits each at 0 / 16 / 32 / 48, × 0.0625 → km/h (order FL, FR, RL, RR) |
| 0x1F3 | ASC3 | DSC | Lateral/longitudinal force, brake-assist status, DSC-active bit 34 |
| 0x1F5 | LWS1 | Steering-angle sensor | `Steering_Angle` 0\|15 × 0.04375 °, sign bit 15. Angular velocity 16\|15 |
| 0x1F8 | ASC4 | DSC | Rough-road signal, MSR/ASR active bits 13/14 |
| **0x316** | **DME1** | DME | **`EngineSpeed` 16\|16 × 0.156252 → rpm** (= raw/6.4). Indicated torque 8\|8 × 0.390625 %. Key-off bit 0, crank-signal error bit 1, A/C relay bit 6 |
| **0x329** | **DME2** | DME | **`CoolantTemperature` 8\|8 × 0.75 − 48.373 → °C**. Pedal position (`DriverDemand`) 40\|8 × 0.39 %. Brake switch bit 48, brake-switch fault bit 49, clutch bit 24, cruise bits 51–53 |
| 0x336 | DME6 (`DME3` in can_data.hpp) | DME | Wheel-torque values. DBC comment says it is only sent when traction-control config is set |
| **0x545** | **DME4** | DME | **Check-engine (MIL) bit 1**, EML bit 4, overheat bit 27, **`OilTemp` 32\|8 − 48.373 → °C**, charge-light bit 40, oil-pressure-light bit 44, fuel-consumption counter 8\|16 |
| 0x565 | DME5 | DME | CVT actuator data plus `ManifoldAbsolutePressure` 56\|8 − 100 → kPa (unverified). DBC comment: sent only on automatics or a specific config, so **it may not appear on this manual car** |
| 0x610 | INSTR1 | KOMBI | VIN fragment (8 bytes) |
| **0x613** | INSTR2 | KOMBI | Odometer 0\|16 × 10 km, **fuel level** 16\|7 (litres), low-fuel bit 23, minute counter 24\|16 |
| 0x615 | INSTR3 | KOMBI | A/C request bits, **ambient temperature** 24\|8 (scaling uncertain), door / handbrake bits, "OBD fault" bit 47 |
| 0x618 | INSTR4 | KOMBI | Gear indicator 8\|4, A/C evaporator temperature 16\|8 × 0.127 − 30 |
| 0x61A | INSTR5 | KOMBI | Odometer 0\|19 (miles, per can_data.hpp), stalk state |
| 0x61F | INSTR6 | KOMBI | Lights, indicators, high-beam, cruise lamp bits |
| 0x43F / 0x44F | EGS1 / CVT1 | Auto trans | Automatics only. Absent here |
| 0x501 | unknown | ? | Seen on the bus, not decoded |

Suggested cross-checks against `EMS2K` status jobs:

- 0x316 rpm against engine speed in `STATUS_ANA_ENGINE9`
- 0x329 coolant against `STATUS_MOTORTEMPERATUR` / `ENGINE4`
- 0x545 oil temperature
- 0x153 speed against DSC
- 0x613 fuel level against the KOMBI status

A mismatch points to a sensor or scaling problem on one side.
