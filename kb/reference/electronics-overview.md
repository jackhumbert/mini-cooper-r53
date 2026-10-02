# Electronic signals (summary)

**Source:** BMW of North America TIS, *2002-07 GENINFO Electronics – Overview – MINI*.
<http://wtxmc.org/MiniCooperDocs/ELECTRONICS%20OVERVIEW.pdf> (local
`research/tis/ELECTRONICS_OVERVIEW.pdf`). This is our own summary. The original is linked, not
redistributed.

This is a generic primer on the kinds of signals MINI modules use. For diagnosis it helps you work
out what a status value *should* look like, and what a stuck value means.

## Signal types and how to read them

| Type | Examples on R50/R53 | What a status/meter reading tells you |
|---|---|---|
| **Inductive (AC)** | (generic; voltage depends on sensor design) | Sine wave whose frequency is proportional to speed. Not every inductive sensor makes 12 V |
| **NTC thermistor** (resistance falls as temperature rises) | **Coolant temp, TMAP air temp**, transmission temp, IHKA interior temp | At the module input with a 5 V supply: **0 V** = no supply or shorted to ground, **≈ 2 V** = warm, **≈ 4 V** = cold, **5 V** = open circuit (sensor or harness) |
| PTC thermistor | — | The opposite of NTC: a higher voltage means hotter |
| **Potentiometer** | **Pedal sensor, throttle feedback** | Smoothly varying voltage proportional to position. Should move smoothly, with no dropouts |
| **Switched B+ / B−** | Ignition switch, light switch, seat-belt, brake (Hall), door/window/sunroof switches | Two states only: supply voltage or 0 V |
| **Modulated square wave** (frequency, pulse width, duty cycle) | Idle/throttle drive, alternator load signal, speed signals | Check the frequency (Hz), pulse width (ms) or duty cycle (%) as the module expects |
| **Hall effect** | **Crank and cam sensors**, window/sunroof motor position | Digital high/low as target teeth pass. Recognises speed and position |
| **Magnetoresistive** | **Wheel speed sensors** (DSC) | 12 V supply, about 10 V output. Signalled as **current pulses ≈ 7 mA (low) / 14 mA (high)**. Works down to zero speed |
| **Designated value** | Multi-position switches with resistor ladders | Each switch position gives a fixed voltage |
| **Coded ground** | **Wiper stalk** (2-pin high/low pattern: single wipe, off, intermittent, slow, fast) | Combination of high/low on several pins |

## Output stages

Modules drive loads through transistor final stages that switch ground (B−) or supply (B+),
either steadily or PWM-modulated. Examples in the source:
- the DME grounding a relay coil (constant B−)
- PWM-driven idle/throttle motors (modulated B− / B+)
- one module's output being another's input (e.g. a speed signal from ASC to the DME)

The base–emitter path is the control side and the collector–emitter path the switched (work)
side, like a relay.

## Diagnostic rule of thumb from the source

**Before replacing a module because a displayed input is wrong, prove the input signal is good.**
Measure at the module connector, not just at the sensor.
