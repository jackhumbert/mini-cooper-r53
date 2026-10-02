# Playbook: no crank / starter does nothing

On the R50/R53 the **EWS immobiliser switches the starter itself**. It drives the terminal-50
starter relay internally (see car-manager `issues/2026-09-29-no-crank.md`), so EWS can say
directly whether it *allowed* a start and, if not, why. Pair this with
[`charging-system.md`](charging-system.md). A battery that has been run down is the other
common cause.

## What the car can tell you

**`python -m r53diag status ews STATUS_LESEN`** returns EWS3 states. Each is 0/1 unless noted:

| Result | Meaning (from the SGBD; English is our translation) |
|---|---|
| `STAT_ANLASSER_FREIGESCHALTET` | **Starter enabled** by EWS |
| `STAT_ANLASSER_AUS_DREHZAHL` | Starter disabled: engine speed (already running) |
| `STAT_ANLASSER_AUS_P_N` | Starter disabled: P/N input not satisfied. On a manual this is most likely the **clutch-pedal switch** input (inference; confirm by watching it change with the pedal) |
| `STAT_ANLASSER_AUS_ZV` | Starter disabled: central locking (car locked/secured) |
| `STAT_ANLASSER_AUS_BC` | Starter disabled: body-computer code |
| `STAT_P_N_EINGANG` | State of the P/N (clutch) input right now |
| `STAT_KL_R_EINGANG` / `STAT_KL_R_EINGANG_KBUS` | Terminal R (accessory) seen on the wire / on the K-bus |
| `STAT_SCHLUESSEL_SENDET` | A key transponder is answering the ring antenna |
| `STAT_AKTUELLE_SCHLUESSELNUMMER` | Which key (0–9) was recognised |
| `STAT_SCHLUESSEL_GESPERRT` / `_NIO_ID` / `_NIO_PW` / `_NIO_WC` | Key disabled / wrong ID / wrong password / rolling-code mismatch |
| `STAT_DME_LEITUNG_FREI` | DME release line OK |
| `STAT_VORGABE_ANLASSERRELAIS*` | Starter-relay command state |

Key ID and rolling-code values are **redacted** by the tool on purpose.

Other sources:

- **DME** `STATUS_IO_EWS` gives `STAT_LV_LOCK_IMOB_ACTIVE` (engine immobilised) and
  comms-error flags. `STATUS_ANA_EWS` gives counters: locked-engine count,
  failed-comms count and key-on count.
- **DME** `STATUS_IO_ENGINE1` gives `STAT_LV_CRK_ERR_ACTIVE`, a crank-signal error. That
  matters for a crank-but-no-start, not for no-crank.
- **EWS / DME** `FS_LESEN`.

## Procedure

1. Run `python -m r53diag doctor` and check the battery voltage. Below about 12.2 V,
   charge first: a weak battery confuses everything.
2. Run `python -m r53diag faults ews dme kombi bc1`.
3. **Key in position II, clutch released.** Run `status ews STATUS_LESEN`.
4. **Clutch fully pressed** (a helper holds it). Run `status ews STATUS_LESEN` again.
   `STAT_P_N_EINGANG` should change. If it doesn't, the clutch switch or its wiring is
   suspect.
5. **Hold START while it fails to crank**, if the fault is present; two people. Run
   `status ews STATUS_LESEN` and look at `STAT_ANLASSER_FREIGESCHALTET` and the
   `_AUS_` reasons.
   - **Starter enabled = 1 but nothing happens:** the fault is downstream of EWS. That
     means the terminal-50 wire, the solenoid, the starter, the main cable or post, or
     ground.
   - **Starter enabled = 0:** the `_AUS_*` and key flags tell you why. Check the clutch,
     key recognition and central locking.
6. Try the spare key and compare `STAT_SCHLUESSEL_SENDET` and the key number.

The no-crank is intermittent, so the useful moment is *when it happens*. Keep the cable
plugged in and the laptop ready so step 5 can be captured live.

## Record

Add an investigation-log entry with each `STATUS_LESEN` snapshot (pedal up and down,
during the failed start) and attach the session file.
