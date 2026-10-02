# Playbook: first connection (and every new session)

1. **Setup:** park the car, turn the engine off, and put the key in **position II**
   (ignition, KL15). A battery charger is recommended for long sessions, because modules
   misbehave below about 12 V.
2. **Plug in** the K+DCAN cable: USB first, then OBD. The OBD socket is under the dash,
   driver's side.
3. **Check** with `python -m r53diag doctor`:
   - `cable_present` false: is the cable plugged in, and on COM6? If Windows gave it another
     port, update `C:\EDIABAS\Bin\obd.ini` `Port=`.
   - `diagnostic_lines` gives "pin 7 OK but cluster silent": check the cable's switch is in
     the **labelled 7+8 position**. The owner found it with a multimeter and labelled it on
     2026-10-02. If it is, see `kb/hardware.md` §7.
   - Neither line answers: is the ignition really in position II? Wait about 5 s after
     turning it on, then re-run.
4. **First time only:** run `python -m r53diag scan --save-profile --trace`.
   - Saves which SGBD variant each module uses to `kb/vehicle-profile.json`. Commit it.
   - `--trace` also captures raw EDIABAS/IFH traces. These are useful to confirm protocol
     details (DSC address, KWP vs DS2) and to update `kb/architecture.md`.
5. **Read** with `python -m r53diag faults`. This uses the profile, so it is quick. **Clear
   nothing** until the faults are recorded in car-manager.
6. **Record:** in car-manager, add a log entry or issue note, and copy the session file(s)
   from `sessions/` into `vehicles/2006-mini-cooper-s/attachments/diag/`.
