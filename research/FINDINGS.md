# Research findings — talking to the R53 through EDIABAS

Compiled 2026-10-02 from: the local EDIABAS/INPA/NCS install, prior work in
`../ipo-decompiler`, `../mini_cooper_dashboard_redo`, the April 2026 Copilot chats,
BMW TIS PDFs from wtxmc.org, and web sources (cited inline).
Confidence tags: **[local]** read from files on this PC · **[TIS]** BMW docs ·
**[src]** open-source code · **[forum]** hearsay · **[car]** observed on this car.

## 1. Installed toolchain [local]

| Thing | Value |
|---|---|
| EDIABAS | 7.3.0 (`C:\EDIABAS\Versions.def`), `EDIABAS.INI`: `Interface=STD:OBD`, `EcuPath=C:\EDIABAS\ECU`, traces off |
| OBD driver config | `C:\EDIABAS\Bin\obd.ini`: `Port=Com6`, `Hardware=USB`, `RETRY=ON` (vendor doc recommends `OFF`) |
| Cable | FTDI FT232R `VID_0403 PID_6001`, serial `AH01BRM5`, **COM6**, latency timer 1 ms, driver 2.12.36.4 |
| API | `api32.dll` (x86, stdcall), **`api64.dll` + `api64.exe`** (x64 proxy to a 32-bit server) |
| Python | 3.12.10 **64-bit** only; no pyserial |
| .NET | runtimes 7/8 only, no SDK |
| Tools | `Tool32.exe` (run any job), **`xtract.exe`** (dump SGBD → XML), `bestvw32.exe` |
| INPA | 5.0.6, menu `CFGDAT\R50.ENG` V1.15 (2006); no R50 `.ips` sources, only `.IPO` |
| NCS Expert | 4.0.1, `DATEN\R50\` present (coding data — **not** in scope) |
| Docs | `C:\EDIABAS\Doku\English\EDIABAS-EN.chm`, `FAQ.pdf`; `C:\EDIABAS\Api\WIN64\Api.h`; `C:\EDIABAS\Hardware\OBD\OBD_DOKU.pdf` |

**Verified 2026-10-02:** 64-bit Python can `ctypes.WinDLL("C:\EDIABAS\Bin\api64.dll")`,
`__apiInit` succeeds, and `__apiJob` runs; with the cable unplugged the job ends in
`IFH-0018: INITIALIZATION ERROR` (expected). See `tools/api64_smoke.py`. → No 32-bit
Python needed. Even offline jobs (`_JOBS`) need a live interface, so offline job
catalogs come from `xtract.exe` / `tools/prgdesc.py` instead.

## 2. What the car said on 2026-04-03 [car]

From INPA's `C:\EC-APPS\INPA\BIN\na_id.tmp` / `na_fs.tmp` (R50.IPO "all ECUs"):

| SGBD | Result |
|---|---|
| `ems2k` | OK — Siemens, BMW # 7557395, coding idx 4, diag idx 38, built wk 42/2006 |
| `dsc_mk60` | OK — Temic, BMW # 6765286, coding idx 11 |
| `ehpsr50` | OK — ZF, BMW # 6770303; fault memory: **no faults** |
| bc1rd, mrs4, ews3, shd46, pdcact, ihkar50, kombi50f, rip, navmk3, nav_jap, videomod, bmbtr50, mflr50, dws, radio, rls_ds2, lwr2a, lws5_1b, dsp_r50 | `IFH-0009 NO RESPONSE FROM CONTROLUNIT` |

**Explanation (high confidence):** the R50/R53 has two diagnostic lines on the OBD
socket [TIS `tis/BUS_SYSTEM.pdf`]:
- **pin 7** — ISO 9141 "diagnostic bus": the powertrain units (DME, DSC, EHPS).
- **pin 8** — "DS2 protocol bus" via the instrument cluster (KOMBI), which gateways to every
  K-bus body module.

The cable must **bridge pins 7+8** for pre-03/2007 cars. On a switched K+DCAN cable that
is the "pin 7+8 / K-line" position. Without it, exactly the three modules above answer.
Same symptom reported at NAM [forum]:
https://www.northamericanmotoring.com/forums/r50-r53-hatch-talk-2002-2006/334903-r53-inpa-yes-engine-dsc-and-ps-codes-but-nothing-else.html ;
EdiabasLib adapter docs [src]: "for BMW-DS2 vehicles an OBD II Pin 7+8 connection in
the adapter is required" (https://github.com/uholeschak/ediabaslib/blob/master/docs/AdapterTypes.md).

## 3. Protocols & modules

- **This car's DME is most likely a Siemens MS5150, not an EMS2000** [car + local, inference].
  - The user remembers it as "the other MS one".
  - INPA's `R50.ENG` labels the engine entry *"EMS2K, EMS5150 for Pentagon"*. That line was added on 15.11.2004 (V1.13), i.e. for the MY2005 facelift cars.
  - The ECU ident says Siemens, BMW # 7557395, diag index 38, built week 42/2006.
  - BMW never made a separate SGBD for it. **`EMS2K.prg` serves both**, and it answered on this car.
  - Equating "Pentagon" with the facelift engine program is an inference.
  - Most public docs (TIS, Peake) describe the EMS2000. Treat them as close but not exact for this ECU.
- Everything is single-wire K-line at **9600 baud, 8E1** [TIS][src].
- **DME (EMS2K, Siemens EMS2000)** speaks **KWP2000\*** (EDIABAS concept 0x010D),
  address **0x13** (`D_0013.grp`) [local][src]. The 4-byte header frame is
  `[fmt][tgt][src][len][data][xor]`. Generic OBD-II (ISO 9141-2, 5-baud init) also works on pin 7.
- **Body modules** speak **DS2**: `[addr][len-incl-cksum][data…][xor]`, response status
  `A0` = OK. The line echoes every transmitted byte. No init sequence is needed [src].
- **DSC_MK60, EHPSR50, MRS4** use KWP2000-style services per their SGBD comments. The exact
  addresses for DSC/GSF21 are unconfirmed and will come from an `IfhTrace` on the car.
- Let EDIABAS handle framing. The above only matters for debugging or for a future raw backend.

### Module → SGBD → group/address [local]

| Module | SGBD (variants) | Group | Addr | Bus |
|---|---|---|---|---|
| DME | EMS2K | D_0013 | 0x13 | pin 7 |
| Power steering pump | EHPSR50 | D_0031 | 0x31 | pin 7 |
| ABS/ASC/DSC | DSC_MK60 | (D_ABSKWP) | ? | pin 7 |
| Auto trans (Aisin, if fitted — this car is manual) | GSF21 | D_EGS | ? | pin 7 |
| Instrument cluster (gateway) | KOMBI50F / KOMBIR50 | D_0080 | 0x80 | pin 8 |
| Body + lights (K-bus master) | BC1RD / BC1 | D_ZKE_GM | 0x00 | K-bus |
| Airbag | MRS4 / MRS5K | D_00A4 | 0xA4 | K-bus |
| Immobiliser | EWS3 / EWS3D | D_0044 | 0x44 | K-bus |
| Climate | IHKAR50 / IHKAR50R | D_005B | 0x5B | K-bus |
| Steering-wheel buttons | MFLR50 | D_0050 | 0x50 | K-bus |
| Steering angle | LWS5_1B | D_0057 | 0x57 | |
| PDC | PDCACT | D_0060 | 0x60 | K-bus |
| Rain/light sensor | RLS_DS2 / AIC | D_00E8 | 0xE8 | K-bus |
| Sunroof | SHD46 | D_0008 | 0x08 | K-bus |
| Headlight levelling | LWR2A | D_009A | 0x9A | |
| Tyre deflation | DWS | D_0070 | 0x70 | |
| Seat occupancy (US) | OC3 | D_0074 | 0x74 | |
| Radio / nav / DSP / BMBT | RADIO, NAVMK3, DSP_R50, BMBTR50 | … | 0x68/0x7F/0x6A/0xF0 | K-bus |
| Vehicle ID | ZCS_R50 | — | — | (reads ZCS/VIN/prod date) |

Variant to resolve on the car: MRS4 vs MRS5K, BC1 vs BC1RD, KOMBI50F vs KOMBIR50
(KOMBIR50 has no `FS_LESEN`). NCS `R50SGFAM.DAT` lists EMS2K, KOMBI50F, DSC_MK60, MRS4,
BC1, C_EWS3.

## 4. Job catalogs [local]

Full JOBNAME/ARG/RESULT dumps for every relevant SGBD are in `sgbd_desc/*.txt`,
generated by `tools/prgdesc.py`. Prior XTRACT XML exports for KOMBIR50, KOMBI50F,
EHPSR50, IHKAR50(R), MFLR50, BMBTR50, RADIO and DSP_R50 are in
`../ipo-decompiler/docs/decompilation/r50/can_packing/static_pipeline/xtract/`.

Highlights for EMS2K (123 jobs):

| Group | Jobs and contents |
|---|---|
| Faults | `FS_LESEN` (F_ORT_NR/TEXT, F_HFK count, environment), `FS_LOESCHEN`, `STAT_FREEZEFRAME` |
| `STATUS_ANA_ENGINE4` | MAP before/after supercharger, coolant, IAT, TPS, pedal, O2 volts, battery voltage |
| `STATUS_ANA_ENGINE5` | knock and per-cylinder ignition angle |
| `STATUS_ANA_ENGINE9` | rpm, speed, load, gear |
| `STATUS_ANA_FUEL_TRIM` | lambda and additive/multiplicative adaptation |
| `STATUS_ANA_MAN_TEST` | misfire counters cyl 1–4 |
| Simple status | `STATUS_ANA_OBD2`, `STATUS_IO_READY_CODE`, `STATUS_UBATT`, `STATUS_MOTORTEMPERATUR` |
| Actuators | `STEUERN_ACTUATOR` NAME=FUEL_PUMP / FAN_RELAY_* / AC_COMPRESSOR / CANISTER_PURGE / INJECTOR_n …; `STEUERN_ADAPTIVE_VALUES` (reset adaptations) |
| Tables | `FORTTEXTE` (250 Siemens fault codes, German text), `ANALOG`, `DIGITAL` |

Online renderings: `https://emdzej.github.io/ediabasx-docs-sgbd/sgbd/<NAME>/`.

**Must-block job families** (coding, flash, immobiliser, odometer):
`C_*`, `COD_*`, `CODIERUNG_*`, `FLASH_*`, `WRITE_*`, `*_SCHREIBEN`, `SPEICHER_SCHREIBEN`,
`SEED_KEY`, `SG_LOGIN`, `SWITCH_TO_BOOT`, `EXECUTE_RAM_ROUTINE`, `LEARN_IMOB_SEED`,
`RESYNC_IMOB_SEED`, `ISN_*`, `WECHSELCODE_*`, `SCHL_*`, `KD_INIT*`, `PASSWORT_*`, `GWSZ_*`
writes, `WRITE_PLIP_CODES`, `ABGLEICH_SCHREIBEN/VORGEBEN`, `*_ABGLEICHEN`.

## 5. EDIABAS API (ctypes) [local `third_party/Api.h`, src]

Every function takes a handle and uses `__stdcall`, exported as `__api*`:
`__apiInit(&h)`, `__apiInitExt(&h, ifh, unit, app, reserved)`,
`__apiJob(h, ecu, job, para, result)` (async), `__apiJobData(h, ecu, job, bytes, len, result)`,
`__apiState(h)` (0 = busy, 1 = ready, 2 = break, 3 = error), `__apiResultSets(h, &n)`,
`__apiResultNumber(h, &n, set)`, `__apiResultName(h, buf, idx, set)`,
`__apiResultText(h, buf, name, set, fmt)` (256-byte buffer),
`__apiResultReal/Int/Long/Word/Binary`, `__apiErrorCode(h)`, `__apiErrorText(h, buf, n)`,
`__apiSetConfig/GetConfig`, `__apiEnd(h)`. Set 0 holds the system results, and `JOB_STATUS`
is in the last set. Reference wrapper: **pydiabas** (MIT, 32-bit only),
https://github.com/BembelBytes/pydiabas.

## 6. Alternatives considered

| Option | Verdict |
|---|---|
| **api64.dll via ctypes (own thin wrapper)** | **Chosen.** Reuses BMW's tested SGBD interpreter, the existing config, and the cable. Verified loadable. |
| pydiabas | Good API design reference; would need 32-bit Python. |
| EdiabasLib (GPL-3, C#) | Excellent fallback: same PRGs, direct FTDI, great raw traces (`EdiabasTest.exe … --cfg="IfhTrace=2"`). Needs .NET SDK or prebuilt binaries. |
| Native DS2/KWP in Python (garagediag-style, `third_party/gd_*.py`) or the C++ lib in `../ipo-decompiler/src/ds2/` | Lose all the scaling/decoding in the PRGs. Only for raw K-bus sniffing / debugging. |
| Generic OBD-II (ELM-style mode 01/03) | Engine only, less data. Not needed. |
| Deep OBD | No R50 configs; nothing to reuse. |

## 7. Prior work worth reusing

- `../mini_cooper_dashboard_redo/src/can_data.hpp`, `lib/r53/r53.dbc`, `src/kbus_data.hpp`,
  and `logs/*.crtd|crbd`: PT-CAN broadcast frames (0x316 DME1 rpm, 0x329 coolant, 0x545
  CEL/oil temp, 0x613 odometer/fuel…) and K-bus messages captured from this car.
  Useful cross-checks for diagnostic values.
- `../ipo-decompiler/src/ds2/`: untested C++ DS2 client. Its `group_tables`, `pseudocode` and
  `can_packing` output is **unreliable** (it treated `tabget` operands as CAN IDs). Ignore it.
- `../mini_cooper_dashboard_redo/reference/R53_Wiring.pdf`, `bus_network.png`, and the
  EMS2000 Funktionsrahmen PDF.

## 8. Knowledge sources for the KB

- **TIS PDFs** (`tis/`, from http://wtxmc.org/MiniCooperDocs/, about 90 docs):
  `BUS_SYSTEM`, `EMS_OVERVIEW` (Cooper S uses **two TMAP sensors** pre/post
  supercharger and **no MAF**; misfire via crank speed), `INSTRUMENT_CLUSTER`,
  `ELECTRONICS_OVERVIEW`, `TROUBLE_CODE` (Mitchell index), `DISplus`.
- **DTC tables:** `dtc/minidtc.pdf` (Peake R5/EMX, separate Cooper / Cooper S P-code tables).
  Pelican fault-code article:
  https://www.pelicanparts.com/techarticles/MINI/18-FUEL-Reading_Fuel_Injection_Fault_Codes/18-FUEL-Reading_Fuel_Injection_Fault_Codes.htm
- **Common R53 failure modes** [forum]:
  - EHPS pump (fan clogs → pump overheats)
  - expansion tank / thermostat housing
  - water pump driven via the supercharger nose gears
  - supercharger oil and coupler
  - crank damper (**already failed on this car, 2026-07**)
  - crank seal / crank sensor O-ring
  - upper engine mount
