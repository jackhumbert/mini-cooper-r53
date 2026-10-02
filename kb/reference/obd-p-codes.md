# OBD-II P-codes for the R50/R53 DME (third-party table)

**Source (third party, not BMW):** Peake Research Corp., *R5/EMX Code-Scan/Reset Tool for Mini
Cooper & Mini Cooper S – Instruction Manual & Code Tables*, Rev 1.0, © 2003. Local copy
`research/dtc/minidtc.pdf`. We don't know a stable public URL; the manufacturer's old page was
`www.r5tool.com/emxtech.shtml`. The code list was cross-checked against the list of codes in TIS
*Self-Diagnostics – MINI* (<http://wtxmc.org/MiniCooperDocs/TROUBLE%20CODE.pdf>). That document's
description tables are images only.

**Caveats:**
- Peake says its definitions are "a starting point" and may contain errors. Its tool targeted Minis
  built **up to 2003** (EMS2000). This car's DME is most likely a **Siemens MS5150** (2005+), which
  may set codes not listed here, or describe them differently.
- These are the **generic OBD P-codes** that a scan tool sees. EDIABAS `FS_LESEN` on `EMS2K` returns
  Siemens/BMW fault numbers (`F_ORT_NR`) with richer text and environment data, plus `F_PCODE` where
  the SGBD maps one. **Prefer the EDIABAS reading.** Use this table to interpret codes from generic
  scanners or from `F_PCODE`.
- Short descriptions below are our own wording of the standard SAE J2012 meanings and Peake's
  manufacturer-code definitions.

## Cooper vs Cooper S differences

- Peake's Cooper S table is the Cooper table **plus P1237–P1242**. These cover the second,
  upstream (pre-supercharger) manifold pressure sensor that only the Cooper S has.
- Both tables also list **P0705, P0815/P0816, P1698–P1789 and P1815/P1816**: CVT, gear-selector and
  Steptronic codes. On the R50 these belong to the **Cooper CVT** (gearbox interface unit). They
  can't occur on this **manual** Cooper S. The R53 automatic option uses a separate Aisin unit with
  its own SGBD.
- The Cooper table prints P0304 three times. This is a typo in the source.
- The 2005 Mitchell/TIS code index (`TROUBLE CODE.pdf`, titled "2005 MINI Cooper") has three codes
  Peake lacks: **P0070** (ambient air temperature sensor, generic SAE), **P101F** and **P1498**.
  Their meanings are only in that document's image tables and aren't transcribed here. That index
  also omits many Peake codes, including all of P1237–P1242. It may cover the Cooper only, or the
  MS5150 code set may differ. Unresolved.

## Code table

"S" in the third column = Cooper S only. Blank = both models.

### Oxygen sensors and heaters

| Code | Meaning | |
|---|---|---|
| P0030 | Upstream O2 heater control circuit | |
| P0031 / P0032 | Upstream O2 heater circuit low / high | |
| P0036 | Downstream O2 heater control circuit | |
| P0037 / P0038 | Downstream O2 heater circuit low / high | |
| P0053 / P0054 | O2 heater resistance, upstream / downstream | |
| P0130 | Upstream O2 sensor circuit | |
| P0131 / P0132 | Upstream O2 sensor voltage low / high | |
| P0133 | Upstream O2 sensor slow response | |
| P0135 | Upstream O2 heater circuit | |
| P0136 | Downstream O2 sensor circuit | |
| P0137 / P0138 | Downstream O2 sensor voltage low / high | |
| P0141 | Downstream O2 heater circuit | |
| P1143 / P1144 | Downstream O2 activity check: signal too high / too low | |
| P2270 / P2271 | Downstream O2 signal stuck lean / stuck rich | |

### Fuel trim and mixture

| Code | Meaning | |
|---|---|---|
| P0171 / P0172 | System too lean / too rich | |
| P2096 / P2097 | Post-catalyst trim too lean / too rich | |

### Air, pressure and temperature sensors

| Code | Meaning | |
|---|---|---|
| P0107 / P0108 | Manifold absolute / barometric pressure circuit low / high | |
| P1106 | MAP too low with engine stopped | |
| P1107 | MAP too low at idle, engine running | |
| P1108 | MAP too low at full load and low rpm | |
| P1109 | MAP too high on deceleration | |
| **P1237 / P1238** | **Upstream (pre-supercharger) MAP sensor input low / high** | **S** |
| **P1239** | **Upstream MAP too low with engine stopped** | **S** |
| **P1240** | **Upstream MAP too low at idle** | **S** |
| **P1241** | **Upstream MAP too low at full load, low rpm** | **S** |
| **P1242** | **Upstream MAP too high on deceleration** | **S** |
| P0112 / P0113 | Intake air temperature circuit low / high | |
| P0114 | Intake air temperature intermittent | |
| P0116 | Coolant temperature range/performance | |
| P0117 / P0118 | Coolant temperature circuit low / high | |
| P0119 | Coolant temperature intermittent | |
| P0125 | Coolant too cold for closed-loop fuel control | |
| P0128 | Thermostat: coolant below regulating temperature | |

### Throttle and pedal (drive-by-wire)

| Code | Meaning | |
|---|---|---|
| P0122 / P0123 | Throttle/pedal sensor "A" low / high | |
| P0222 / P0223 | Throttle/pedal sensor "B" low / high | |
| P1122 / P1123 | Pedal sensor 1 low / high | |
| P1222 / P1223 | Pedal sensor 2 low / high | |
| P1224 | Pedal sensors 1 and 2 disagree | |
| P1125 / P1126 | Throttle sensors A and B disagree, small / large error | |
| P1226 | Throttle (flap) malfunction | |
| P1229 | Throttle adaptation failed | |
| P0638 | Throttle actuator range/performance | |
| P2122 / P2123 | Pedal sensor "D" low / high | |
| P2127 / P2128 | Pedal sensor "E" low / high | |
| P2138 | Pedal sensors D/E voltage correlation | |
| P1617 | DME throttle H-bridge driver | |
| P1679–P1693 | Throttle-safety monitor ("level 2/3") faults: torque loss, ADC, rpm, idle A/B, clutch torque min/max, pedal/throttle sensor diagnosis, air-mass and torque calculation, rpm limitation, throttle + injection shut-off A/B | |

### Injectors, ignition and misfire

| Code | Meaning | |
|---|---|---|
| P0201–P0204 | Injector circuit open, cylinders 1–4 | |
| P0261 / P0262 | Cylinder 1 injector circuit low / high | |
| P0264 / P0265 | Cylinder 2 injector circuit low / high | |
| P0267 / P0268 | Cylinder 3 injector circuit low / high | |
| P0270 / P0271 | Cylinder 4 injector circuit low / high | |
| P0300 | Random / multiple-cylinder misfire | |
| P0301–P0304 | Misfire, cylinders 1–4 | |
| P0313 | Misfire detected with low fuel | |
| P1320 / P1321 | Flywheel (tone-wheel) adaptation for misfire detection: range / performance | |
| P0351 / P0352 | Ignition coil A / B (wasted-spark pairs) primary/secondary circuit | |
| P1366 / P1367 | Ignition coil A / B circuit low | |
| P2300 / P2301 | Ignition coil A primary control low / high | |
| P2303 / P2304 | Ignition coil B primary control low / high | |
| P0324 | Knock control system error | |
| P0326 | Knock sensor range/performance | |

### Crank, cam, speed and idle

| Code | Meaning | |
|---|---|---|
| P0335 / P0336 | Crankshaft sensor circuit / range-performance | |
| P0340 / P0341 | Camshaft sensor circuit / range-performance | |
| P0500 | Vehicle speed signal | |
| P0506 / P0507 | Idle rpm lower / higher than target | |

### Catalyst and EVAP (leak diagnosis pump)

| Code | Meaning | |
|---|---|---|
| P0420 | Catalyst efficiency below threshold | |
| P0441 | Incorrect purge flow | |
| P0442 / P0456 / P0455 | EVAP leak: small / very small / large | |
| P0443 / P0444 / P0445 | Purge valve circuit / open / shorted | |
| P1436 | LDP open circuit | |
| P1437 | LDP range/performance | |
| P1442 / P1443 | LDP control signal low / high | |
| P1475 / P1477 | LDP reed switch did not close / did not open | |
| P1476 | LDP clamped tube | |
| P2400 / P2401 / P2402 | LDP control circuit open / low / high | |
| P2404 | LDP sense circuit range/performance | |

### DME internal, supplies and communication

| Code | Meaning | |
|---|---|---|
| P0601 | DME memory checksum | |
| P0603 | DME keep-alive memory | |
| P0604 / P1600 | DME RAM / external RAM | |
| P1615 | DME processor SPI-bus failure | |
| P0642 / P0643 | Sensor reference voltage A low / high | |
| P0652 / P0653 | Sensor reference voltage B low / high | |
| P1570 / P1571 / P1572 | DME sensor supply A low / high / noisy | |
| P1573 / P1574 / P1575 | DME sensor supply B low / high / noisy | |
| P1607 | CAN version mismatch | |
| P1611 | Serial link to the transmission control unit | |
| P1612 | Serial link to the instrument cluster | |
| P1613 | Serial link to ASC (stability control) | |

### Transmission (CVT and gear selector; not applicable to this manual car)

| Code | Meaning |
|---|---|
| P0705 | Transmission range sensor (PRNDL input) |
| P0815 / P0816 | Upshift / downshift switch circuit |
| P1698 / P1699 | Transmission controller control error / checksum |
| P1705 / P1706 | Transmission LED output open / short |
| P1739 / P1741 / P1742 | Clutch solenoid communication / open / short |
| P1749 / P1751 / P1752 | Secondary pressure solenoid communication / open / short |
| P1785–P1789 | Ratio-control actuator: circuit, range, open, short, communication |
| P1815 / P1816 | Steering-wheel shift + / − switch low input |

## MIL and clearing (from TIS)

A code is stored on first detection. The MIL lights on the next drive cycle in which the fault is
confirmed, or immediately for catalyst-damaging misfire. It goes out after 3 clean cycles and the
code self-erases after 40 (80 for catalyst-damage misfire). See
[engine-management.md](engine-management.md#obd-behaviour-ems-tc).
