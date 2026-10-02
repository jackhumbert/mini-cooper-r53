# Reference summaries

Diagnosis-focused summaries of BMW/MINI service documents and one third-party code table, written
for the 2006 MINI Cooper S (R53).

**About these files.** Every summary here is an **original paraphrase** written for this project.
Facts and numbers are kept and attributed. The BMW source documents are copyrighted by BMW of North
America / BMW AG (and Mitchell Repair Information for the trouble-code chapter). They are **linked,
not redistributed**. Read the originals for figures, wiring and full procedures.

The public copies are hosted at <http://wtxmc.org/MiniCooperDocs/>. Our local filenames use
underscores (`BUS_SYSTEM.pdf`). The URLs below assume the hosted names use spaces
(`BUS SYSTEM.pdf`), as in the one URL pattern we have confirmed. If a link 404s, browse the
directory.

| Summary | Source document | Public URL | Diagnostic value |
|---|---|---|---|
| [bus-system.md](bus-system.md) | TIS *Bus Systems – Overview – MINI* (2002-07 GENINFO) | <http://wtxmc.org/MiniCooperDocs/BUS%20SYSTEM.pdf> | High: buses, gateway, termination, sleep, failure patterns |
| [engine-management.md](engine-management.md) | TIS *Engine Management – Overview – MINI* (EMS2000), plus Mitchell *Self-Diagnostics – MINI* (2005) for OBD monitors | <http://wtxmc.org/MiniCooperDocs/EMS%20OVERVIEW.pdf>, <http://wtxmc.org/MiniCooperDocs/TROUBLE%20CODE.pdf> | High: sensors, limp modes, misfire, adaptations, EWS link. Written for EMS2000; this car most likely has an MS5150 |
| [instrument-cluster.md](instrument-cluster.md) | TIS *Instruments – Repair Instructions – Cooper R50/W10 & Cooper S* (2002-05) | <http://wtxmc.org/MiniCooperDocs/INSTRUMENT%20CLUSTER.pdf> | Low: removal only. Gateway notes collected from other sources |
| [electronics-overview.md](electronics-overview.md) | TIS *Electronics – Overview – MINI* (2002-07 GENINFO) | <http://wtxmc.org/MiniCooperDocs/ELECTRONICS%20OVERVIEW.pdf> | Medium: what sensor signals should look like (NTC 0/2/4/5 V rule etc.) |
| [obd-p-codes.md](obd-p-codes.md) | **Third party:** Peake Research *R5/EMX* manual code tables (© 2003) | no stable public URL known (local `research/dtc/minidtc.pdf`) | Medium: generic P-code meanings, Cooper vs Cooper S |

Not summarised:
- *DISplus – Overview* (<http://wtxmc.org/MiniCooperDocs/DISplus.pdf>). This describes BMW's
  dealer tester hardware: PC specs, cables, multimeter leads. Nothing in it is diagnostic for the
  car. The only relevant point is that MINI uses the **16-pin OBD connector** (the 20-pin round
  BMW connector is not used).
- The Mitchell *Self-Diagnostics* chapter's DTC description tables are images. Only its code index
  and monitor descriptions are used (in engine-management.md and obd-p-codes.md).

See also [`../hardware.md`](../hardware.md), [`../architecture.md`](../architecture.md) and
[`../glossary.md`](../glossary.md), which cite these summaries.
