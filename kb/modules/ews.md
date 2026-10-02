# EWS — immobiliser (SGBD `EWS3`, alt. `EWS3D`)

- **Module key:** `ews`. **Group:** `D_0044` (address 0x44). **Line:** K-bus, reached via
  OBD pin 8 through the cluster.
- **What it does:** EWS reads the key transponder through the ignition-lock ring antenna.
  It releases the DME with a rolling-code handshake, and **drives the starter relay
  (terminal 50) internally**. "Everything powers up but the starter is silent" can
  therefore be EWS, its inputs (clutch switch, central-locking state) or its relay.
- The key fob's remote lock/unlock is a separate function and says nothing about the
  transponder.

## Useful jobs (read tier)

| Job | Gives |
|---|---|
| `IDENT`, `HERSTELLDATEN_LESEN`, `STATUS_SW_VERSION` | Identity |
| `FS_LESEN`, `IS_LESEN` | Fault and info memory |
| `STATUS_LESEN` | Starter enabled; reasons the starter is disabled (engine speed / P-N or clutch input / central locking / BC code); key sending, key number, key-rejected reasons; terminal R; DME release line. Full table in [`../playbooks/no-crank.md`](../playbooks/no-crank.md) |
| `STATUS_EWS` | EWS3/EWS4 capability and active flags |
| DME `STATUS_IO_EWS` / `STATUS_ANA_EWS` | The DME's side of the handshake: immobilised flag, comms errors, counters |

## Blocked

ISN read/write, key data, key enable/disable, rolling-code sync with the DME, password
jobs, initialisation and all writes. Key-ID and rolling-code values are also redacted from
the tool's output and sessions.
