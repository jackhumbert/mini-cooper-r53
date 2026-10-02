# Hardware: cable, OBD socket, EDIABAS configuration

This page covers how the PC reaches the car (2006 MINI Cooper S R53, manual): the cable, the
OBD-II pins that matter on R50/R53, the switch on the cable, EDIABAS and `obd.ini` settings,
power and ignition requirements, and what each common EDIABAS error means.

**Source tags.** `[TIS-BUS]` is TIS *Bus Systems – Overview*
(<http://wtxmc.org/MiniCooperDocs/BUS%20SYSTEM.pdf>). `[TIS-EMS]` is TIS *Engine Management –
Overview* (<http://wtxmc.org/MiniCooperDocs/EMS%20OVERVIEW.pdf>). `[TIS-TROUBLE]` is the Mitchell
*Self-Diagnostics – MINI* chapter (<http://wtxmc.org/MiniCooperDocs/TROUBLE%20CODE.pdf>). `[OBD_DOKU]` is BMW TI-538
*Dokumentation zum On Board Diagnose Stecker OBD* v1.11, 2010 (`C:\EDIABAS\Hardware\OBD\OBD_DOKU.pdf`,
German). `[FAQ]` is BMW *FAQ regarding EDIABAS, INPA and ToolSet* v2.12, 2009
(`C:\EDIABAS\Doku\English\FAQ.pdf`). `[local]` means read from this PC. `[car]` means observed on
this car. `[src]` means open-source code or docs. `[forum]` means owner reports. `[inference]` means
our own reasoning, not yet verified.

---

## 1. The cable

| Item | Value | Source |
|---|---|---|
| Type | "K+DCAN" USB cable, FTDI FT232R (`VID_0403 PID_6001`, serial `AH01BRM5`) | [local] |
| Windows port | **COM6** | [local] |
| FTDI driver | 2.12.36.4 | [local] |
| FTDI latency timer | **1 ms** (Device Manager → Ports → USB Serial Port (COM6) → Port Settings → Advanced) | [local] |
| Switch | Multi-position switch, **undocumented** (see §3) | [car] |

Why the latency matters: the K-line protocols time their gaps between bytes and between messages
in milliseconds. The FTDI default of 16 ms buffers received bytes long enough to break those
timings. Keep it at 1 ms. `[src]` (standard advice for FTDI-based K-line cables) `[inference]`

Plug-in order: BMW's own adapter manual says to connect the PC end first, then the car. The ground
pins 4 and 5 make contact first and drain any static charge. `[OBD_DOKU §5]`

The genuine BMW "OBD connector" this driver was written for can sense KL15 (ignition) on the
serial DSR line and KL30 (battery) on RI. It only reports KL15 reliably once the battery is above
8.5 V. `[OBD_DOKU §3.2]` We don't know whether this clone cable wires DSR and RI at all, and the
current `EDIABAS.INI` disables both checks anyway (§4). So **EDIABAS will not warn that the
ignition is off. You just get IFH-0009.**

## 2. OBD-II socket pins used by R50/R53

The socket is the 16-pin connector in the driver's footwell, under the dash to the left of the
steering column near the A-pillar, behind a snap-off cover. `[TIS-BUS]` `[TIS-TROUBLE]`

| Pin | Function on R50/R53 | Source |
|---|---|---|
| 4 | Chassis ground | SAE J1962 |
| 5 | Signal ground | SAE J1962 |
| **7** | **Diagnostic K-line ("D-bus", ISO 9141-2)** to the powertrain units: DME, DSC, EHPS (and the auto-transmission unit on automatics) | [TIS-BUS] for the bus, [src]/[forum] for the pin number |
| **8** | **"DS2 protocol bus"** to the instrument cluster (KOMBI). KOMBI gateways it to every K-bus body module | [TIS-BUS] for the bus, [src]/[forum] for the pin number |
| 16 | Battery + (KL30). Powers the cable | SAE J1962 |
| 6 / 14 | CAN-H / CAN-L on 2007+ D-CAN BMWs. **Not used for diagnosis on R50/R53.** We haven't checked whether they are populated on this car | [src] `[inference]` |

TIS describes the two diagnostic buses but does not give pin numbers. Pins 7 and 8 come from
EdiabasLib's adapter documentation ("for BMW-DS2 vehicles an OBD II Pin 7+8 connection in the
adapter is required", <https://github.com/uholeschak/ediabaslib/blob/master/docs/AdapterTypes.md>)
and from owner reports such as
<https://www.northamericanmotoring.com/forums/r50-r53-hatch-talk-2002-2006/334903-r53-inpa-yes-engine-dsc-and-ps-codes-but-nothing-else.html>.

**Consequence:** the cable has only one K-line transceiver. To reach both buses on a pre-03/2007
car, it must **bridge pins 7 and 8**. Without the bridge, only the pin-7 (powertrain) units
answer.

## 3. The switch on the cable

The cable has a multi-position switch with no documentation. On switched K+DCAN cables, one
position usually **bridges pins 7+8** (for older K-line BMW/MINI) and another leaves pin 8 open
(for 2007+ D-CAN cars). **That convention is not guaranteed for this cable.** `[forum]` `[inference]`

**The position we need for this car is the one that bridges pins 7 and 8.**

> **This cable, 2026-10-02:** the owner found the position that shorts pins 7 and 8 with a
> multimeter and **labelled it on the switch**. Use the labelled position for this car.
> `[car]` It hasn't been confirmed on the car with `r53 doctor` yet; update this note after the
> first session.

### Definitive test: multimeter (do this first)

1. Unplug the cable from the car **and** from USB.
2. Set the multimeter to continuity (beep) or the lowest ohms range.
3. Find pins 7 and 8 on the cable's male OBD plug. Most plugs have the numbers moulded in. Pins 7
   and 8 sit next to each other at one end of the row that also holds the grounds 4 and 5. Pin 8
   sits directly above pin 16. The numbering on the plug is a mirror image of the numbering on the
   car's socket, so go by the moulded numbers.
4. Probe 7↔8 in **each** switch position and write down the result.
   - About 0 Ω, or a beep: **bridged**. This is the position to use.
   - Open circuit (OL): **not bridged**.
5. Record the result here, and mark the switch physically. Done for this cable on 2026-10-02.

### Empirical test: with the tool

With KL15 (ignition) on, run `r53 doctor` or `r53 scan`:

| DME (`EMS2K`) | KOMBI (`KOMBI50F`) and other body modules | Meaning |
|---|---|---|
| answers | answer | Bridged. Correct position. |
| answers | **IFH-0009** | **Not bridged** (or pin 8 is faulty) |
| IFH-0009 | IFH-0009 | Ignition off, wrong COM port, or cable not powered. Go to §7 |

**Canonical "not bridged" symptom, observed 2026-04-03** `[car]`: INPA's "all ECUs" run got
answers only from `EMS2K`, `DSC_MK60` and `EHPSR50`. All three are pin-7 units. Every body SGBD
returned `IFH-0009 NO RESPONSE FROM CONTROLUNIT`: BC1RD, MRS4, EWS3, SHD46, PDCACT, IHKAR50,
KOMBI50F, RLS_DS2, LWR2A, LWS5_1B, DWS, radio/nav and others. We don't know which switch position
was used that day. (Source: INPA `na_id.tmp` / `na_fs.tmp`, summarised in `research/FINDINGS.md`
§2.)

## 4. EDIABAS configuration

### `C:\EDIABAS\Bin\EDIABAS.INI` (current values) `[local]`

| Key | Value | Notes |
|---|---|---|
| `Interface` | `STD:OBD` | Required for this cable `[OBD_DOKU §6.1]`. Exactly one interface line may be active `[FAQ 1.10]` |
| `EcuPath` | `C:\EDIABAS\ECU` | Location of the SGBDs (`*.PRG`) and group files (`D_00xx.GRP`, where `xx` is the ECU address) `[FAQ 3.15, 3.18]` |
| `TracePath` | `C:\EDIABAS\TRACE` | Where `api.trc` / `ifh.trc` are written |
| `ApiTrace` | `0` | 1–7 traces job and result names and values `[FAQ 3.18]` |
| `IfhTrace` | `0` | 1–3 traces raw sent/received telegrams to `ifh.trc`. **Use this when debugging a bus** `[FAQ 3.18]` |
| `UbattHandling`, `IgnitionHandling` | `0` | EDIABAS does not check battery or ignition state |
| `RetryComm` | `1` | EDIABAS retries failed communication itself |
| `SystemResults` | `1` | Result set 0 carries system results (see [glossary](glossary.md#ediabas-conventions)) |

### `C:\EDIABAS\Bin\obd.ini` `[local]`

```ini
[OBD]
Port=Com6
Hardware=USB
RETRY=ON
```

| Key | Allowed values | Meaning | Recommendation |
|---|---|---|---|
| `Port` | `Com1`…`Com9` `[OBD_DOKU §6.2]` | Serial port used by the driver | `Com6` |
| `Hardware` | `OBD`, `ADS` per `[OBD_DOKU §6.2]` | Adapter type | Currently `USB`. That value is **not** in BMW's v1.11 document. It comes from the third-party K+DCAN driver bundle. Leave it alone, because INPA worked with it on 2026-04-03 `[car]` |
| `RETRY` | `ON`, `OFF` | Driver-level retry | **Set `OFF`.** BMW: "repetition on error is already done by EDIABAS, so this should be off" `[OBD_DOKU §6.2]`. `RetryComm=1` is already set in `EDIABAS.INI`, so having both on doubles the retries and the time spent on non-responding modules |
| `MODE` | `NORMAL`, `KBUS` | `KBUS` converts DS2 telegrams into K-bus telegrams, for a single DS2 unit on the K-bus | Leave unset (`NORMAL`) |
| `UBATT` | `ON`, `OFF` | `OFF` forces "battery present", a workaround for adapters without RI sensing | Unset |
| `WAKEUP_LOW` / `WAKEUP_HIGH` | 10–40 ms, default 25 | KWP2000 fast-init wake-up pulse | Unset |
| `TRACELEVEL` | bitmask | Driver-internal debugging | `0` |
| `[UNIT_x]` sections | — | Per-unit overrides for multi-instance use, via `apiInitExt("STD:OBD","x",…)` | `UNIT_E` already points at `Com6` |

**Where `obd.ini` must live.** `[OBD_DOKU]` says the Windows directory. `[FAQ 3.6]` says
`C:\EDIABAS\BIN` for EDIABAS packages 1.4 and later. `[FAQ 2.2]` says old INPA builds wanted
`C:\WINDOWS`. On this PC only `C:\EDIABAS\Bin\obd.ini` exists, and INPA used it successfully, so
**`Bin` is the effective location** `[local]` `[car]`. If you edit the file, make sure no stray
`C:\Windows\obd.ini` appears and overrides it.

## 5. Ignition (KL15) and bus wake-up

- **KL15 (ignition, key position 2) must be on** for diagnosis. Most units only communicate with
  KL15 on. Most K-bus users become active from KL R (accessory) upward. `[TIS-BUS]`
- **Engine off, ignition on** is the default state for identification, fault reads and most
  status reads. Live engine data obviously needs the engine running.
- **The K-bus goes to sleep 60 s after ignition off.** While asleep it rests at 12 V. `[TIS-BUS]`
  After switching the ignition off and on again, allow a moment before scanning body modules.
- The DME main relay stays energised for **about 5 minutes after key-off**. Wait 5 minutes, or pull
  the relay, before disconnecting DME connectors. `[TIS-EMS]`
- The diagnostic buses (D-bus and DS2) are only active while a tester is communicating. Each
  module supplies its own bus voltage, nominally 12 V, and communication still works down to
  about 2 V levels. `[TIS-BUS]`

## 6. Battery voltage

- BMW: **keep a battery charger on the car during diagnosis.** A slowly falling battery voltage
  causes sporadic communication faults, because different modules stop communicating at
  different voltages. Check charge, the charging system, fuses and module grounds before blaming a
  bus. `[TIS-BUS]`
- The DME compensates injector timing and coil dwell for supply voltages of roughly 6 V to 14 V.
  `[TIS-EMS]` That is an operating range, not a diagnostic threshold.
- KL15 sensing in the BMW adapter only works above 8.5 V. `[OBD_DOKU]`
- Project policy (not a BMW number): `r53 doctor` warns below **12.2 V** with the engine off
  (`PLAN.md`). This car has an open no-crank / intermittent-charging issue, so use a charger for
  long sessions.
- A defective alternator can inject noise into the K-bus and CAN wiring. This gives intermittent
  communication faults that are stored in some modules but not others. `[TIS-BUS]`

## 7. Troubleshooting EDIABAS errors

EDIABAS reports `<number>: <code>: <text>`, for example `Error 19: IFH-0009`. Codes starting
`IFH-` come from the interface handler (cable, port, bus). `SYS-` codes are file and runtime
errors. `API-` codes are caller errors. `BIP-` codes come from the SGBD interpreter.

| Error | Text | Likely causes (this setup first) | Fix |
|---|---|---|---|
| 12 IFH-0002 | NO RESPONSE FROM INTERFACE | `Interface` in `EDIABAS.INI` doesn't match the hardware `[FAQ 1.1]` | Set `Interface = STD:OBD` |
| 13 **IFH-0003** | DATATRANSMISSION TO INTERFACE DISTURBED | Cable plugged into USB but **not into the car** (pin 16 unpowered). Short on the line. Wrong interface type `[FAQ 1.2]` | Plug into the car and check that pin 16 has 12 V. Check for shorts |
| 16 IFH-0006 | COMMAND NOT ACCEPTED | Tool32 multi-instance set to a different interface, or a UDS SGBD used on the OBD interface `[FAQ 1.3]` | Use single-instance. R50 SGBDs are not UDS, so this shouldn't occur |
| 19 **IFH-0009** | NO RESPONSE FROM CONTROLUNIT | **Ignition off** `[FAQ 1.4]`. **Pins 7+8 not bridged** (body modules only, §3). Module not fitted, or wrong SGBD variant. K-bus asleep. Low battery. Module or bus fault `[TIS-BUS]` | Ignition on. Set the switch to the bridged position. Run `r53 scan` to see which modules answer. Use a charger. Check fitted options (no PDC or nav means those modules won't answer) |
| 20 **IFH-0010** | DATATRANSMISSION TO CONTROLUNIT DISTURBED | `[FAQ 1.5]` only lists EDIC/OMITEC/serial-buffer causes, none of which apply here. For a K-line FTDI cable: corrupted or garbled reply, echo mismatch, latency too high, noise, low voltage `[inference]` | Check latency = 1 ms, battery voltage and the connector seating. Retry. Capture `IfhTrace=2` |
| 23 **IFH-0013** | COMMAND NOT IMPLEMENTED | **Another program holds the COM port**: INPA, Tool32, NCS Expert, a serial terminal, another `r53` process `[FAQ 1.6]` | Close the other program. Kill stale `api64.exe` |
| 28 **IFH-0018** | INITIALIZATION ERROR | **COM port missing or busy**: cable unplugged from USB, wrong `Port=` in `obd.ini`, port opened by another app `[FAQ 1.7]`. Verified symptom with the cable unplugged, 2026-10-02 `[local]` | Plug in the cable. Check that COM6 exists in Device Manager and that `Port=Com6` |
| 30 IFH-0020 | DRIVER ERROR | Port in use by another program, or no interface defined `[FAQ 1.8]` | As IFH-0013 / IFH-0002 |
| 37 IFH-0027 | IFH NOT FOUND | `EDIABAS.INI` missing, or no or commented-out `Interface=` line `[FAQ 1.10]` | Restore `EDIABAS.INI` and check that `C:\EDIABAS\Bin` is on `PATH` |
| 48 IFH-0038 | INTERFACE COMMAND NOT IMPLEMENTED | Another program on the COM port, or `obd.ini` missing or pointing at a nonexistent port `[FAQ 1.11]` | As IFH-0013. Check `obd.ini` |
| 70 BIP-0010 | CONSTANT DATA ACCESS ERROR | External table (e.g. `T_GRTB.PRG`) missing or outdated `[FAQ 1.13]` | Mostly affects group/functional jobs. Call the variant SGBD (e.g. `KOMBI50F`) directly |
| 92 SYS-0002 | ECU OBJECT FILE NOT FOUND | Variant SGBD not in `EcuPath` `[FAQ 1.14]` | Check that `C:\EDIABAS\ECU\<NAME>.PRG` exists |
| 95 **SYS-0005** | OBJECT FILE NOT FOUND | SGBD or group file missing. Wrong `EcuPath`. Name longer than 8 characters or containing illegal characters. No read access to `ECU\` `[FAQ 1.15]` | Check the name spelling (8.3, `A-Z0-9_`) and `EcuPath` |
| 100 SYS-0010 | INITIALIZATION ERROR | SGBD with automatic protocol-concept switching could not reach the ECU `[FAQ 1.16]` | Treat it like IFH-0009 |
| 126 API-0006 | ACCESS DENIED | Two applications using EDIABAS at once (FAQ says EDIABAS ≤ 6.4; we run 7.3) `[FAQ 1.17]` | Never run INPA/Tool32 alongside `r53` |
| 134 API-0014 | RESULT NOT FOUND | Requested a result name the job didn't return `[FAQ 1.18]` | Wrong result name or wrong SGBD variant. List the results returned |

### Quick decision tree

1. **IFH-0018 / IFH-0013 / IFH-0038**: a PC-side problem (port missing or busy). Nothing reached the car.
2. **IFH-0003**: the cable has no car power. Check that it is plugged into the car and the battery.
3. **IFH-0009 from everything**: ignition off, or the battery is very low.
4. **IFH-0009 only from body modules**: pins 7+8 not bridged (§3).
5. **IFH-0009 from a single module**: not fitted, wrong variant, or a fault in that module or its
   wiring. TIS suggests a quick K-bus health check: hazard lights should flash the cluster
   indicators, and the MFL volume buttons should change the radio volume. `[TIS-BUS]`
6. **Intermittent IFH-0010 / IFH-0009**: voltage, the connector, or electrical noise (alternator).
   Capture an `IfhTrace`.
