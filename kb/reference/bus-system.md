# Bus systems (summary)

**Source:** BMW of North America TIS, *2002-07 GENINFO Bus Systems – Overview – MINI*
(as printed for a 2006 MINI Cooper S).
<http://wtxmc.org/MiniCooperDocs/BUS%20SYSTEM.pdf> (local copy `research/tis/BUS_SYSTEM.pdf`).
This is our own summary, focused on diagnosis. The original is linked, not redistributed. See
[`../architecture.md`](../architecture.md) for how this fits this car and the tool.

TIS uses the BMW name **IKE** for the instrument cluster. The EDIABAS SGBDs call it **KOMBI**.

## The four networks

| Bus | Speed | Physical layer | Role |
|---|---|---|---|
| CAN | 500 kbit/s | Twisted pair, yellow/black (H) and yellow/brown (L) | Time-critical powertrain data: engine management, automatic transmission, stability control |
| K-bus | 9600 bit/s | Single wire, white/red/yellow, 0/12 V | Body and comfort modules, event-driven |
| D-bus (ISO 9141-2) | 9600 bit/s | Single wire | Tester access to emissions-relevant powertrain units |
| DS2 bus | 9600 bit/s | Single wire | Tester access to the cluster and, through it, every K-bus module |

The cluster is the **gateway** between buses. Example given in TIS: the DSC calculates road speed
and sends it on CAN; the cluster re-sends it on the K-bus for speed-dependent wipers (BC1) and
radio volume.

## K-bus facts that matter for diagnosis

- Split into **K-bus I and K-bus II**, joined inside BC1. Electrically they are one bus: a short
  to ground or B+ on one half disables both. An open circuit only cuts off the modules beyond the
  break.
- **BC1 is the master.** It powers the bus, sequences messages and has the highest priority.
- Most users are active from **KL R**. The bus **sleeps 60 s after ignition off** and rests at 12 V
  while asleep.
- Arbitration works by echo: a sender transmits when the bus is idle and must read its own message
  back. If it doesn't, it waits and retries. It gives up after **5 attempts**.
- The bus survives a disconnected or dead module ("tree" structure). A module with a software fault
  can still jam the whole bus.
- **Short to B+:** senders see no acknowledgement, retry 5 times, then log a fault and carry on
  without the undelivered commands.
- **Short to ground:** most modules read this as an idle bus. Only the master and standby units log
  a bus fault.
- **Quick functional check:** turn on the hazard lights (the cluster indicators must flash), then
  adjust the radio volume with the MFL buttons (the volume must change). If both work, the K-bus is
  basically OK, and any remaining fault is local to one module or its wiring.
- **Isolating a module that jams the bus:** disconnect modules one at a time and repeat the bus
  test after each.

## CAN facts that matter for diagnosis

- Linear bus, terminated at **both ends (EMS 2000 / DME and IKE / cluster) with 120 Ω each**.
  Measure **≈ 60 Ω** between CAN-H and CAN-L with power off and all modules connected. A module
  without a terminator measures **10–50 kΩ** between its own H/L pins when unplugged.
- Stubs **≤ 1 m**. Untwisted sections **≤ 4 cm**.
- Recessive (logic 1): both lines at **2.5 V**. Dominant (logic 0): H ≈ **3.5 V**, L ≈ **1.5 V**
  (2 V difference). The bus keeps working with somewhat wrong termination, but gives sporadic
  faults.
- Messages carry content IDs, not addresses. The ID also sets the priority, and a message that
  can't be sent is held and resent.
- A module that can't reach another stores a **"timeout"** or CAN fault. When one module drags the
  whole CAN down, *every* unit logs CAN faults. Isolate by unplugging modules one at a time and
  clearing/re-reading faults.
- Scope patterns described: an isolated (automatic-transmission) module times out after about
  **10 s** and then sits flat at 2.5 V until the key is cycled. A flat line on one or both wires
  means an open circuit to that module. H shorted to L cancels the signal (flat line).
- **Plausibility shortcut:** a working tachometer and temperature gauge prove DME↔cluster CAN
  traffic. The gear display and DSC lamp give similar clues for other modules.
- After programming a module, the others will have stored faults. Clear them and re-read. Faults
  that won't clear suggest a wrongly programmed module.

## Diagnostic (D-bus / DS2) facts

- The diagnostic buses are **only active while a tester is connected and talking**.
- Nominal level **12 V**. Communication still works down to about **2 V**. Each module supplies its
  own bus voltage. Measure each data line to ground.
- **If vehicle identification succeeds, the D-bus is OK.** If several units don't answer, suspect a
  bus link, not the individual units.

## General causes of K/D-bus and CAN failure (TIS checklist)

1. Wiring: open circuit, short to B+ or ground, CAN-H shorted to CAN-L, bad crimps or corroded
   pins.
2. A failed module (usually logged as a fault in the *other* modules).
3. **Supply voltage or ground at a module.** A slowly discharging battery gives sporadic
   communication faults, because modules drop out at different voltages. A bad module ground stops
   it seeing a valid low level (0–2 V).
4. **Interference.** A defective **alternator** or aftermarket electronics (phones, amplifiers)
   can induce noise. This gives intermittent faults stored in only some modules. Isolate aftermarket
   wiring and verify the alternator.

**First steps TIS always recommends:** check the battery charge (keep a **charger** connected
during diagnosis), and check the diagnosis cable and head connection.
