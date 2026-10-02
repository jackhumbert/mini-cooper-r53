# Engine management (summary)

**Sources:**
- `[EMS]` BMW of North America TIS, *2002-07 GENINFO Engine Management – Overview – MINI*.
  <http://wtxmc.org/MiniCooperDocs/EMS%20OVERVIEW.pdf> (local `research/tis/EMS_OVERVIEW.pdf`).
- `[TC]` Mitchell / BMW, *2005 ENGINE PERFORMANCE Self-Diagnostics – MINI*.
  <http://wtxmc.org/MiniCooperDocs/TROUBLE%20CODE.pdf> (local `research/tis/TROUBLE_CODE.pdf`).
  This one is used for its OBD monitor descriptions. Its DTC table exists only as images.

This is our own summary, focused on diagnosis. The originals are linked, not redistributed.

> **Which DME is this?** These documents describe the Siemens **EMS2000**. This car's DME
> identifies through EDIABAS SGBD `EMS2K` as Siemens, part 7557395, diagnostic index 38, built
> week 42/2006. INPA's `R50.ENG` labels the entry "EMS2K, EMS5150 for Pentagon" (added
> 15.11.2004). So the unit is most likely a **Siemens MS5150** (2005+ facelift), which uses the same
> SGBD. Reading "Pentagon" as the facelift engine programme is **our inference**. Treat the numbers
> below as **close but not guaranteed exact** for MS5150. Where they conflict with this car's live
> data or the `EMS2K` SGBD tables, the car and the SGBD win.
>
> In this KB the module is called **"DME (Siemens MS5150; EDIABAS SGBD EMS2K)"**.

## Cooper S specifics (vs Cooper)

| Item | Cooper S (R53, W11 supercharged) | Cooper | Src |
|---|---|---|---|
| Load sensing | **Speed-density, no MAF.** **Two pressure sensors**, one each side of the supercharger | One TMAP | [EMS] |
| Post-supercharger sensor | **TMAP** (pressure + intake air temperature) in the intake manifold, range **250 kPa** | TMAP, range 120 kPa | [EMS] |
| Pre-supercharger sensor | Same part as the Cooper TMAP, **temperature element unused**. Sits between the throttle and the supercharger inlet. TIS calls it "MAP" | — | [EMS] |
| Throttle body | 57 mm | 52 mm | [EMS] |
| Injectors | Siemens, **2-hole**, higher flow. 62 mm long, 3.5 bar. Connector differs from the Cooper's | Bosch 4-hole | [EMS] |
| DME location | Side compartment of the air box, left of the engine-bay fusebox | Battery box side compartment | [EMS] |
| Extra P-codes | P1237–P1242 (upstream MAP sensor) | — | [Peake](obd-p-codes.md) |

The DME compares the pre- and post-supercharger pressures to work out air density and air mass.
[EMS]

## Power supply and main relay

- **KL30** through F01 keeps the memory alive. **KL15** through **F34** is the wake-up input (also
  live at KL50). The DME then grounds **pin 97** to energise the **main relay**, which feeds:
  - **F02**: DME, injectors, crank sensor, coils
  - **F03**: cam sensor, O2 heaters, fan, A/C relay, purge
  - **F04**: automatic transmission
  - **F05**: coolant fan

  [EMS]
- The main relay **stays on about 5 min after key-off**. It won't energise with reverse polarity.
  A stuck-on relay causes **battery drain**. The DME logs a fault if it energises the relay but sees
  no supply. [EMS]
- Testing: battery voltage, F34 with key on, KL30 at the relay, the relay itself, the ground signal
  from the DME, the voltage drop across the contacts. [EMS]
- Grounds: `X6000` pins 61, 62, 80, 81 and `X6004` pins 114, 115. Connector: 81-pin engine side +
  40-pin vehicle side. [EMS]
- The DME compensates injection time and dwell for battery voltages of roughly 6–14 V. [EMS]

## Sensors

| Sensor | Type | Normal / diagnostic values | Failure behaviour | Src |
|---|---|---|---|---|
| **Accelerator pedal (PWG)** | 2 Hall tracks, separate 5 V supplies | Track 1 ≈ **0.5–4.5 V**, track 2 ≈ **0.5–2.0 V** (plausibility). Both ≈ 0.5 V at idle | One track bad: rpm capped. **Both bad: ≈ 1300 rpm, ≈ 1000 rpm with brake pressed.** If the two disagree, the lower value is used [TC] | [EMS] |
| **Throttle (EDR) feedback** | 2 potentiometers | Pot 1 **0.5 V (idle) → 4.5 V (WOT)**. Pot 2 mirrors it, 4.5 → 0.5 V | Pot 1 fault: pot 2 substitutes. Emergency mode 1 = reduced dynamics. **Mode 2 = rough, limited response (limp home)**, also triggered by pressing brake and throttle together in mode 1, or by a brake-switch fault. Detects a jammed throttle or broken spring. **Throttle controller fault: H-bridge off, ≤ 2000 rpm** [TC] | [EMS] |
| **TMAP / MAP** | Piezo-resistive + NTC | Idle ≈ **1–2 V** (0.6–1.5 V quoted elsewhere), WOT ≈ **4–4.8 V**. Key-on, engine stopped = barometric. **0 V or 5 V = fault mode**, default map used | Hard start, stalling, misfire. Status values should move and not sit at 0 or 5 V | [EMS] |
| **Intake air temperature** (in TMAP) | NTC, 5 V supply | ≈ **4 V cold, ≈ 1 V hot** | Cold-start problems, poor driveability, power loss when hot. A default value is used | [EMS] |
| **Coolant temperature** | NTC, two wires, in the head by the thermostat housing | See the resistance table below | Open/short: default value, rich-hot/lean-cold running. Sensor ground shorted to 5/12 V: **gauge reads full hot and the fan runs on high** | [EMS] |
| **Crankshaft** | Hall. **60-2 wheel** (58 teeth + 2 missing, 6° pitch) | — | **No crank signal = no injection and no ignition. There is no backup** (the cam has only 1 pulse per rev) | [EMS] |
| **Camshaft** | Hall. Half-moon target, one edge per cam revolution | 0–5 V square | Injection drops to **semi-sequential**. Coils unaffected (wasted spark). If no sync at start: injection at a fixed phase (50 % chance of correct timing), open loop, knock control at a default value [TC] | [EMS] |
| **Knock** | Piezo accelerometer | — | Retard is **cylinder-selective**, then timing creeps back. On a sensor fault: safe default timing, power and economy loss | [EMS] |
| **O2 sensors** | Zirconia, heated, 1 upstream + 1 downstream | Pre-cat oscillates ≈ **0.1–0.9 V**. Post-cat steady ≈ **0.7–0.8 V**. Heaters need 250–300 °C | Upstream fault: **open loop**, rough idle, MIL. A post-cat signal that copies the pre-cat signal = catalyst efficiency fault | [EMS] |
| **A/C pressure** | Voltage transducer | ≈ **1.2–2.0 V** normal. Open circuit reads as max pressure, so the compressor is disabled | — | [EMS] |
| **Alternator load** | PWM from the alternator | — | Signal lost: idle dips when electrical loads switch on | [EMS] |
| **Brake switch** | 2 Hall inputs (main + test) | — | Disagreement: throttle demand ignored (engine stays at idle), cruise disabled for the trip | [EMS] |
| **Clutch switch** (manual) | Single Hall | — | Used only to cancel cruise | [EMS] |
| LDP reed switch | Reed in the leak-diagnosis pump | — | EVAP faults | [EMS] |

### Coolant sensor resistance (typical, kΩ) [EMS]

| °C | −40 | 0 | 30 | 50 | 70 | 80 | 90 | 100 | 110 | 120 |
|---|---|---|---|---|---|---|---|---|---|---|
| kΩ | 336.6 | 32.66 | 8.06 | 3.60 | 1.75 | 1.255 | 0.915 | 0.68 | 0.51 | 0.39 |

Generic NTC check at the DME input [ELECTRONICS_OVERVIEW]: 0 V = no supply or shorted to ground,
≈ 2 V = warm, ≈ 4 V = cold, 5 V = open circuit.

## Actuators and control functions

- **Electronic throttle (EDR):** DC motor driven at a **600 Hz** polarity-switched PWM. It handles
  driver demand, DSC torque requests, cruise and idle (there is no separate idle valve). [EMS]
- **Idle target 750 rpm** for all MINIs. The DME uses the alternator PWM to anticipate electrical
  load. An **idle "jack"** raises idle when system voltage drops, until it recovers. [EMS]
- **Injectors:** individually driven (full sequential). About **12 Ω**. Typical injection time
  ≈ **3.0–5.0 ms** at idle. With one injector circuit dead, the engine keeps running on the rest.
  [EMS]
- **Rev limit:** injectors cut individually above **6500 rpm**. Vehicle speed limiting works the
  same way. Neither protects against a missed downshift. [EMS]
- **Ignition:** two **wasted-spark** double coils (cylinders 1+4 and 2+3). Cylinders 1 and 2 fire
  outer→centre electrode (negative kV, about 20 % higher). Secondary ≈ **7–9 kV** on compression,
  **3–5 kV** on the waste stroke. **A bad coil affects two cylinders; a bad plug lead affects one.**
  [EMS]
- **Fuel pump:** relay grounded by the DME on **pin 105**, fed via fuse 20. Primes for a few
  seconds at key-on, then runs only while rpm is seen. From **09/2002** a crash signal from the MRS
  replaces the inertia switch (> 14 g, manual reset) used before. Rail pressure **3.5 bar**, held
  by a regulator in the right-hand half of the saddle tank. TIS describes no return line from the
  engine. [EMS]
- **Radiator fan** (two-speed via a resistor in the relay pack). [EMS]
  - Low speed **on at 105 °C, off at 101 °C**.
  - High speed **on at 112 °C**, back to low after a 4 °C drop.
  - A/C pressure: low at **8 bar**, high above **18 bar**.
- **A/C compressor:** BC1 sends an on/off request every 10 s. The DME grants it and reports back.
  The switch LED flashes at 0.5 Hz if the request is refused. [EMS] The DME cuts the compressor at:
  - more than **6016 rpm**
  - evaporator below **2 °C**
  - coolant above **118 °C**
  - A/C pressure above **30 bar** or below **1.6 bar**
  - full pedal held more than 5 s, or a rapid full pedal more than 2 s
  - rpm below 500 (stall)
  - cranking
- **Purge (TEV):** active in closed loop, with coolant above **67 °C** and under load. Opens and
  closes in 16 steps over a 6 min cycle, then rests 1 min. Fully open at WOT, closed on overrun
  cut. Checked by the lambda shift, or else by an rpm change when pulsed at idle. [EMS]
- **O2 heaters:** PWM, about 98 % duty until hot, increased on overrun. [EMS]
- **Torque manager:** arbitrates idle, catalyst protection, limp-home, DSC/ASC/MSR, cruise and
  driver demand. Torque is changed **only through ignition timing (fast) and throttle (slow)**,
  never through mixture. [EMS]
- **EML lamp** (amber, on the cluster via CAN): engine-safety / drive-by-wire faults that are *not*
  emissions-related. **MIL:** emissions faults. [EMS]

## EWS interaction (immobiliser)

- Before releasing **injection and ignition**, the DME must receive a valid **rolling code** from
  EWS 3 over a **dedicated one-way single wire**. The exchange is encrypted and time-limited. [EMS]
- The key transponder code is read by the coil at the ignition lock and checked by EWS, which then
  sends its codes to the DME. [EMS]
- So **crank but no start**, with no injector pulse and no spark, is a classic EWS↔DME mismatch or
  line fault. **No crank** at all points to the starter, KL50 or EWS starter release (and P/N on
  automatics). See the no-crank playbook. `[inference from EMS]`

## Adaptations (fuel trims)

- **Additive** adaptation (ms) applies at idle and low load. **Multiplicative** (%) applies at
  normal-to-high load. [EMS]
- **Positive = the DME is adding fuel (it sees lean).** **Negative = it is removing fuel (it sees
  rich).** Adaptation can only make small corrections. A large air leak or fuel-supply fault drives
  it to its limit, which sets fuel-system faults. [EMS]
- The fuel-system monitor checks that short-term + long-term trim stays within a band. [TC]
- After replacing the **throttle body or pedal**, clear the adaptations and relearn them, or the
  engine may not start or will run in fail-safe. [EMS]
- **Flywheel / tone-wheel adaptation** is learned during overrun fuel cut. Until it is learned,
  misfire detection is less sensitive. If it is out of limits, a fault is set (P1320/P1321). It is
  not displayed by the tester. [EMS]

## Misfire detection

- Based on **crank acceleration**: the period of each **180° crank segment, starting 54° before
  TDC**. A cylinder whose segment takes too long is flagged. About 9 valid contiguous segments are
  needed for a roughness value. [EMS] [TC]
- **Emissions level:** misfires summed per cylinder over **1000 revs**. Over the threshold sets a
  fault and the MIL. [EMS]
- **Catalyst-damage level:** counted over **200 revs**, depending on load and rpm. Sets a fault,
  the MIL comes on **immediately**, lambda goes **open loop**, and the **injector of the affected
  cylinder is shut off**. [EMS]
- Suppressed during overrun, load transitions, rough road (from the DSC signal), cylinder cut-off
  and similar. [TC]
- The cluster tells the DME about **low fuel** so that misfires caused by fuel starvation can be
  judged (P0313). [EMS]

## OBD behaviour [EMS] [TC]

- A fault is **stored on first detection**. The **MIL** lights after the fault is seen again in
  the next drive cycle where that monitor runs, or **immediately** for catalyst-damaging misfire.
- The MIL goes out after **3** consecutive clean cycles. The fault self-erases after **40** clean
  cycles (**80** for catalyst-damage misfire).
- BMW/Siemens fault codes (read with EDIABAS) are stored **before** the MIL comes on. Each carries
  **4 environment conditions**, up to **10 faults**, a "last occurred" time stamp, and a qualifier
  (upper/lower limit, open, plausibility…), plus present / not present / intermittent status. They
  give far more detail than generic P-codes and freeze frames.
- Monitors and readiness groups: misfire (stages A / B1 / B4), EVAP 1–4, catalyst, lambda control,
  pre-/post-cat O2 sensors, "complete system". The TIS readiness-bit table appears garbled in the
  source. Don't rely on it.
- **Catalyst monitor**: runs once per trip in closed loop, steady throttle, 5–80 km/h, catalyst
  model at 350–650 °C. [EMS] Uses oxygen-storage capacity with forced rich/lean pulses. [TC]
- **Thermostat monitor:** compares a modelled coolant temperature with the measured one. It
  decides when the model crosses about **85.5 °C**. Too slow a warm-up = stuck-open thermostat.
  [TC]
- **MAP plausibility** [TC]: MAP too low with the engine stopped, too low at idle, too low at full
  load and low rpm, **too high in overrun (target ≈ 200 hPa)**. These are P1106–P1109 (and
  P1239–P1242 for the Cooper S upstream sensor). On a MAP fault, load is estimated from rpm and
  throttle.
- **Idle-speed monitor:** idle error too large with the vehicle stopped (P0506/P0507). [TC]
- **EVAP (LDP):** on cold start the pump strokes for about **27 s** to build ≈ **+25 mbar**,
  stabilises until 38 s, measures from **38 to 63 s** (fast pumping = leak), then releases from 63
  to 100 s. At key-on the DME does a static circuit check. Leak resolution is down to **0.5 mm**.
  The purge valve is checked by opening it near the end of the LDP test. [EMS] [TC]

## Source inconsistencies noticed

- The TMAP text says the pre-supercharger sensor is "between the supercharger and the throttle
  plate" in one place and "between the supercharger and the EDR" in another. Both mean
  throttle → sensor → supercharger inlet. Fine.
- The MAP worked example quotes a barometer of "1.5 bar at sea level". That is wrong (≈ 1.0 bar).
  Ignore the example numbers.
- Unit conversions are slipshod: purge enable is given as "67 °C (39 °F)" in one place and
  "(153 °F)" in another, and the fan hysteresis as "4 °C (39 °F)". Trust the °C values.
- Idle MAP voltage is given as 1–2 V in one place and 0.6–1.5 V in another. Treat it as a range to
  verify against this car's baseline.
