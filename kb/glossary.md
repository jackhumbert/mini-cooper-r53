# Glossary: BMW/MINI and EDIABAS vocabulary

BMW SGBD job names, result names and comments are mostly German, sometimes abbreviated. This list
covers the terms that recur in `research/sgbd_desc/*.txt` (the R50/R53 SGBDs) and in TIS.
German spelling in SGBDs replaces umlauts: ä→ae, ö→oe, ü→ue, ß→ss (`LOESCHEN` = *löschen*).

Most translations are standard. Where a term is ambiguous or our reading is uncertain, the entry
says so.

## EDIABAS conventions

| Convention | Meaning |
|---|---|
| **SGBD** (*Steuergeräte-Beschreibungsdatei*) | ECU description file (`*.PRG`). Holds the telegrams for one ECU variant and decodes its replies into typed results (int, long, real, string, binary). The filename (≤ 8 characters) is the name you call. [FAQ 3.12] |
| **Group file** (`D_00xx.GRP`) | Picks the right variant SGBD for an ECU address `xx`. [FAQ 3.15] |
| **Job** | One named service in an SGBD. Usually one request telegram and one reply, decoded. Jobs are independent of each other. [FAQ 3.13] |
| `_` prefix | Internal/developer item. `_JOBS`, `_TABLES` and `_JOBCOMMENTS` are metadata jobs. `_TEL_ANTWORT`/`_TEL_AUFTRAG` results are raw response/request telegrams. SGBD *files* whose names start with `_` contain development-only jobs. [FAQ 3.14] |
| **Result sets** | A job returns numbered sets. **Set 0 holds the system results** when `SystemResults=1` (e.g. `VARIANTE`, `OBJECT`, `JOBNAME`, `SAETZE`; battery and ignition state where supported). Sets 1…n hold the job's results, for example one set per fault for `FS_LESEN`. **`JOB_STATUS` is in the last set.** [local] (`EDIABAS.INI`, `api64` tests) |
| **`JOB_STATUS`** | `OKAY` on success. Otherwise `ERROR_…`, for example an ECU rejection or bad argument. Always check it, even when EDIABAS raised no error. |
| `…_WERT` | Numeric **value** (*Wert*) |
| `…_EINH` | **Unit** string for the matching `_WERT` (*Einheit*), e.g. `°C`, `mV`, `1/min` |
| `…_TEXT` | Decoded **text** (from an SGBD table) |
| `…_NR` | **Number** / index (*Nummer*) |
| `…_ANZ` | **Count** (*Anzahl*) |
| `STAT_…` | A **status** result inside a `STATUS_*` job, e.g. `STAT_MOTORTEMPERATUR_WERT` + `STAT_MOTORTEMPERATUR_EINH` |
| `F_…` | Fault-memory results (see the FS block below) |
| `ID_…` | Identification results (see the IDENT block below) |
| `ARG` | Job argument. Passed as a `;`-separated string |
| Concept (*Konzept*) | The diagnostic protocol family an SGBD speaks: DS2, KWP2000\*, KWP2000, BMW-FAST, UDS. "Low-/High-Konzept nach Lastenheft Codierung/Diagnose" refers to the short and long fault-memory record formats in BMW's coding/diagnosis spec. |
| *Lastenheft* | Specification document (BMW requirements spec) |
| *Steuergerät* (SG) | Control unit / ECU. *SG-Adresse* = ECU address |
| *Auftrag* / *Anforderungstelegramm* / *Sendetelegramm* | Request / request telegram |
| *Antwort* / *Antworttelegramm* | Response / response telegram |
| *Variante*, *Variantenindex* | ECU variant. Variant index |
| *Diagnoseindex*, *Codierindex*, *Bus-Index* | Diagnostic index, coding index, bus index. Ident fields that pick the SGBD and the coding data |

## Job verbs and families

| Term | German | Meaning | Safety tier (kb/safety) |
|---|---|---|---|
| **IDENT** | *Identifikation* | Read part number, HW/SW, supplier, date | read |
| **LESEN** | *lesen* | read | read |
| **STATUS** | — | read current values (status jobs) | read |
| **FS_LESEN** | *Fehlerspeicher lesen* | read fault memory | read |
| **FS_LESEN_DETAIL** | — | read one fault in detail (environment data) | read |
| **IS_LESEN** | *Infospeicher lesen* | read info memory | read |
| **FS_LOESCHEN** | *Fehlerspeicher löschen* | **clear** fault memory | confirm |
| **LOESCHEN** | *löschen* | delete / clear | confirm |
| **STEUERN** | *steuern* | **actuate** / drive an output (component test) | confirm |
| **STEUERN_ENDE** / *Ende* | — | end actuation, return control to the ECU | — |
| **SCHREIBEN** | *schreiben* | **write** | blocked (mostly) |
| **VORGEBEN** | *vorgeben* | specify / preset a value | confirm/blocked |
| **ABGLEICH** / **ABGLEICHEN** | *Abgleich* | calibration / trim / alignment value. *Abgleich schreiben* = write a trim | blocked |
| **ADAPTION** / *Adaption löschen* | *Adaption* | learned adaptation values / reset them | confirm |
| **CODIERUNG**, `C_…`, `COD_…` | *Codierung* | coding (configuration data) | blocked |
| **SIA** | *Service-Intervall-Anzeige* | service interval indicator (oil service / inspection). `SIA_RESET` | confirm |
| **TEST** / *Prüfung* | — | self-test / check | confirm |
| **DIAGNOSE_ENDE**, **DIAGNOSEMODE** | — | end diagnostic session / select session mode | read |
| *Freigabe* | — | enable / release (e.g. *Zündfreigabe*, ignition release from EWS) | — |
| *Beschreiben* / *Auslesen* | — | write to / read out | — |

## Fault memory (FS) vocabulary

| Term | German | Meaning |
|---|---|---|
| **FS** | *Fehlerspeicher* | Fault memory (the DTC store) |
| **IS** | *Infospeicher* | Info memory. A secondary store of events and informational entries, separate from the customer-relevant fault memory. On BC1, `IS_LESEN` returns the alarm mislock and alarm-trigger logs, and a central-locking ring buffer |
| **ORT** / `F_ORT_NR`, `F_ORT_TEXT` | *Fehlerort* | Fault **location**, meaning the fault code itself (the manufacturer code number, not the SAE P-code) and its text |
| **ART** / `F_ARTn_NR`, `F_ARTn_TEXT` | *Fehlerart* | Fault **type/status**, e.g. present / not present, sporadic, upper/lower limit, open, short. An ECU may give several per fault |
| **HFK** / `F_HFK` | *Häufigkeitszähler* | **Frequency counter**: how often the fault was detected. Range 0–31 in EWS3 |
| **LZ** / `F_LZ`, `F_LZ1/2` | *Logistikzähler* | "Logistics counter". The SGBD comments describe it as fault age: "fault age in AUX cycles", "secondary frequency counter (age)". In standard BMW practice it counts the drive cycles until a fault that is no longer present self-clears. *(The self-clear meaning is our reading.)* |
| **UW** / `F_UW_ANZ`, `F_UWn_NR/TEXT/WERT/EINH` | *Umweltbedingung* | **Environment condition**: snapshot values stored with the fault (rpm, temperature, voltage…). Like an OBD freeze frame. EMS2000 stores 4 per fault, for up to 10 faults [TIS-EMS] |
| `F_HEX_CODE` | — | Raw fault record bytes |
| `F_PCODE`, `F_PCODE_STRING`, `F_PCODE_TEXT` (`F_PCODE7…`) | — | SAE J2012 code as a number, as a 5-character `'Pxxxx'` string (`'--'` if none), and as text. Only where the SGBD maps one (powertrain) |
| *Fehler vorhanden / nicht vorhanden* | — | fault currently present / not currently present |
| ***sporadisch*** | — | **intermittent** |
| *Fehlerhäufigkeit* | — | fault frequency |
| *Fehlercode* | — | fault code |
| *Plausibilität* / *unplausibel* | — | plausibility / implausible |
| *oberer / unterer Grenzwert* | — | upper / lower limit exceeded |
| *Signal zu groß / zu klein* | — | signal too high / too low |
| ***Kurzschluss nach Masse*** | — | **short circuit to ground** |
| ***Kurzschluss nach Plus / UBatt*** | — | **short circuit to B+** |
| ***Unterbrechung*** / *Leitungsunterbrechung* | — | **open circuit** / broken wire |
| *Kurzschluss oder Unterbrechung* | — | short or open (cannot tell which) |
| *Zeitüberschreitung* / *Timeout* | — | timeout (bus message missing) |
| *Botschaft fehlt* | — | (CAN) message missing |
| *Unterspannung / Überspannung* | — | under-voltage / over-voltage |
| *Endstufe* | — | output (driver) stage |

## Identification (IDENT) fields

| Result | German | Meaning |
|---|---|---|
| `ID_BMW_NR` | *BMW-Teilenummer* | BMW part number |
| `ID_HW_NR` | *Hardwarenummer* | hardware number |
| `ID_SW_NR` | *Softwarenummer* | software number |
| `ID_COD_INDEX` | *Codierindex* | coding index |
| `ID_DIAG_INDEX` | *Diagnoseindex* | diagnostic index (selects the SGBD variant) |
| `ID_BUS_INDEX` | *Bus-Index* | bus index |
| `ID_DATUM_KW`, `ID_DATUM_JAHR` | *Herstelldatum KW / Jahr* | production **calendar week** / year |
| `ID_LIEF_NR`, `ID_LIEF_TEXT` | *Lieferant* | supplier number / name (Siemens, Temic, ZF, Bosch…) |
| **AIF** | *Anwenderinfofeld* | "user information field": programming/assembly record (VIN, date, programming km, assembly number) |
| **ZCS** | *Zentralcodierschlüssel* | central coding key: **GM** (*Grundmerkmal*, basic feature), **SA** (*Sonderausstattung*, options) and **VN** (*Versionsmerkmal*, version). Stored in EWS/cluster. Read via `ZCS_R50` |
| **FGNR** / FG | *Fahrgestellnummer* | **VIN** (chassis number; often the last 7 characters) |
| **GWSZ** | *Gesamtwegstreckenzähler* | **total distance counter (odometer)**. `GWSZ_*` writes are blocked |
| *Kilometerstand* | — | mileage |
| *Prüfstempel* | — | test stamp (end-of-line / workshop test marker) |
| *Baureihe* | — | model series (R50, R52, R53…) |
| *Seriennummer* | — | serial number |
| *Teilenummer* | — | part number |

## Terminals (*Klemmen*, KL)

| Term | Meaning |
|---|---|
| **KL30** | permanent battery positive |
| **KL31** | ground |
| **KL R** (*Radio*) | accessory position (key position 1). Most K-bus users wake from here [TIS-BUS] |
| **KL15** | ignition on (key position 2). Wakes the DME (via fuse F34) and the main relay [TIS-EMS] |
| **KL50** | starter (cranking, key position 3) |
| **KL58** / 58g | lighting / instrument-illumination dimmer feed |
| **KL61** | alternator "D+" / charge-indicator line (engine running) |
| *Klemmenstatus* | terminal status (which of R/15/50 is on) |

## Module abbreviations

| Abbr. | German | English |
|---|---|---|
| **DME** | *Digitale Motor-Elektronik* | petrol engine ECU. On this car: Siemens **MS5150**, SGBD `EMS2K` (see [architecture](architecture.md#5-modules-sgbds-and-addresses)) |
| EMS2000 / EMS2K | — | Siemens engine management of the early R50/R53. Also the name of the SGBD that serves both EMS2000 and MS5150 |
| **DDE** | *Digitale Diesel-Elektronik* | diesel ECU (not this car) |
| **EGS** | *Elektronische Getriebesteuerung* | automatic transmission control (`GSF21`, Aisin). Not fitted on this manual car |
| GIU / ECVT | — | gearbox interface unit / CVT (Cooper CVT only) |
| **DSC** | *Dynamische Stabilitäts-Control* | stability control (Teves MK60), includes ABS/ASC |
| **ASC** (ASC+T) | *Automatische Stabilitäts-Control* | traction control (brake + engine torque) |
| **ABS** | *Antiblockiersystem* | anti-lock brakes |
| **MSR** | *Motor-Schleppmomentregelung* | engine drag-torque control. Raises torque to stop the wheels locking under engine braking [TIS-EMS] |
| ASR | *Antriebsschlupfregelung* | traction (wheel-spin) control |
| EBV | *Elektronische Bremskraftverteilung* | electronic brake-force distribution (EBD) |
| **MRS** | *Multiple Rückhaltesystem* | airbag / restraint control (MRS4, MRS5) |
| **EWS** | *Elektronische Wegfahrsperre* | immobiliser (EWS 3) |
| **IHKA** | *Integrierte Heiz-Klima-Automatik* | automatic climate control. **IHKS/IHKR** = manual variants (exact R50 naming uncertain) |
| **KOMBI** | *Instrumentenkombination* | instrument cluster, the **gateway**. TIS calls it **IKE** |
| **BC1** | — | MINI body controller (BMW "ZKE/GM" role): lights, wipers, locking, K-bus master |
| ZKE / GM | *Zentrale Karosserie-Elektronik / Grundmodul* | BMW central body electronics / general module |
| **LWS** | *Lenkwinkelsensor* | steering-angle sensor |
| **LWR** | *Leuchtweitenregulierung* | headlight-range (levelling) control |
| **RLS** | *Regen-Licht-Sensor* | rain/light sensor |
| **PDC** | *Park Distance Control* | parking sensors |
| **SHD** | *Schiebehebedach* | sliding/tilting sunroof |
| **MFL** | *Multifunktionslenkrad* | multi-function steering wheel |
| CVM | *Cabrio-Verdeck-Modul* | convertible top module (R52) |
| DWS / RPA | *Reifenpannenanzeige* | deflation warning system |
| RDC | *Reifendruck-Control* | tyre-pressure monitoring. *Radelektronik* = wheel electronics (the tyre sensor). *Restlebensdauer* = remaining (battery) life |
| EHPS | — | electro-hydraulic power steering pump |
| OC3 | — | occupant classification (seat mat, US) |
| DWA | *Diebstahlwarnanlage* | alarm system |
| ZV | *Zentralverriegelung* | central locking |
| BMBT | *Bordmonitor* | on-board monitor (nav screen) |

## Engine vocabulary (DME / EMS2K)

| German | English |
|---|---|
| ***Drosselklappe*** (DK) | **throttle valve**. EDK/MDK = electric/motorised throttle. MINI TIS calls the actuator **EDR** |
| DK-Poti, *Potentiometer* | throttle position sensor (two tracks) |
| **PWG** (*Pedalwertgeber*) | accelerator pedal sensor |
| ***Saugrohr*** | **intake manifold**. *Saugrohrdruck* = manifold pressure (MAP) |
| *Ladedruck* / *Lader* / *Kompressor* | boost pressure / charger / supercharger |
| **TMAP** | temperature + manifold absolute pressure sensor (Cooper S has two) |
| *Umgebungsdruck* / *Höhe* | ambient (barometric) pressure / altitude |
| ***Lambdasonde*** | **O2 (lambda) sensor**. *vor Kat* = upstream (pre-cat), *nach Kat* = downstream (post-cat) |
| *Lambdaregelung* | closed-loop mixture control |
| *Sondenheizung* | O2 sensor heater |
| *Gemischadaption*, *additiv / multiplikativ* | mixture (fuel-trim) adaptation, additive (idle, in ms) / multiplicative (load, in %) |
| ***Klopf***, *Klopfsensor*, *Klopfregelung* | **knock**, knock sensor, knock control |
| ***Zündwinkel*** | **ignition angle** (timing). *Zündwinkelrücknahme* = knock retard |
| *Zündung*, *Zündspule* | ignition, ignition coil |
| ***Einspritzzeit*** (ti) | **injection time** (pulse width, ms) |
| *Einspritzventil* (EV) | injector |
| ***Laufunruhe*** | **rough running**: per-cylinder crank-speed variation used for misfire detection |
| *Aussetzer*, *Verbrennungsaussetzer* | misfire |
| ***Geberrad***, *Geberradadaption* | **trigger (tone) wheel** on the crank, and its learned tooth-error correction (needed for misfire detection) |
| *Kurbelwelle (KW)* / *Nockenwelle (NW)* | crankshaft / camshaft |
| ***Kühlmittel***, *Kühlmitteltemperatur*, *Motortemperatur* | **coolant**, coolant temperature, engine temperature |
| ***Ansaugluft***, *Ansauglufttemperatur* | **intake air**, intake air temperature |
| *Öltemperatur* | oil temperature |
| ***Leerlauf***, *Leerlaufregelung* (LLR) | **idle**, idle speed control |
| *Drehzahl* | engine speed (rpm, unit `1/min`) |
| *Last*, *relative Last* | load |
| *Vollast* / *Teillast* / *Schub* (*Schubabschaltung*) | full load / part load / overrun (overrun fuel cut-off) |
| ***Stellglied*** | **actuator** |
| ***Ansteuerung*** | **activation** / drive signal (to an actuator) |
| *Endstufe* | output (driver) stage |
| *Hauptrelais* | main relay |
| *Kraftstoffpumpe* (EKP), *Kraftstoffpumpenrelais* | fuel pump, fuel pump relay |
| *Kraftstoff* / ***Tankinhalt*** | fuel / **fuel tank level** |
| *Tankentlüftung*, TEV (*Tankentlüftungsventil*) | evaporative purge, purge valve |
| LDP / DMTL | leak diagnosis pump (BMW: *Diagnosemodul Tankleckage*) |
| *Kat(alysator)* | catalytic converter |
| *Kühlerlüfter* / *E-Lüfter* | radiator fan |
| *Klimakompressor*, *Klimadruck* | A/C compressor, A/C pressure |
| *Generator* | alternator |
| *Batteriespannung* / UBatt | battery voltage |
| *Bremslichtschalter* (BLS), *Bremslichttestschalter* | brake light switch, redundant brake test switch |
| *Kupplungsschalter* | clutch switch |
| FGR / *Tempomat* | cruise control (*Fahrgeschwindigkeitsregelung*) |
| *Notlauf* | limp-home / emergency mode |
| *Readiness*, *Bereitschaft* | OBD readiness monitors |
| *Fahrzyklus* | drive cycle |
| *Lernwerte* | learned values (adaptations) |

## Body / chassis vocabulary

| German | English |
|---|---|
| *Geschwindigkeit*, *Fahrzeuggeschwindigkeit* | (vehicle) speed |
| *Raddrehzahl* | wheel speed |
| *Gang* | gear |
| *Außentemperatur* | outside (ambient) temperature |
| *Verdampfer(temperatur)* | (A/C) evaporator (temperature) |
| *Gebläse* | blower |
| *Umluft* | recirculation |
| *Luftverteilung* | air distribution |
| *Heckscheibenheizung* (HHS) | heated rear window |
| *Fahrer / Beifahrer* | driver / passenger |
| *Gurtschloss*, *Gurtkontakt*, *Gurtstraffer* | seat-belt buckle, buckle switch, pretensioner |
| *Seitenairbag*, *Zündpille / Zündkreis* | side airbag, airbag squib / firing circuit |
| *Sitzbelegung* | seat occupancy |
| *Schlüssel*, *Wechselcode* | key, rolling code (EWS) |
| *Fensterheber* | window lifter |
| *Blinker*, *Warnblinker* | turn signal, hazard lights |
| *Abblendlicht / Fernlicht / Nebelscheinwerfer* | low beam / high beam / fog lights |
| *Scheibenwischer*, *Intervall* | wiper, intermittent |
| *Schalter / Taster* | switch / push-button |
| *Verbaut* / *vorhanden* | fitted (installed) / present |
| *aktiv / inaktiv*, *ein / aus*, *ja / nein* | active / inactive, on / off, yes / no |
| *Zähler*, *Anzahl*, *Dauer*, *Zeit*, *Tage*, *Monate* | counter, count, duration, time, days, months |
| *Spannung*, *Strom*, *Widerstand* | voltage, current, resistance |
| *Wertebereich*, *Schwellenwert* | value range, threshold |
| *Werkstatt*, *Transportmodus* | workshop, transport (shipping) mode |
| *Zeitinspektion*, *Ölservice* | time-based inspection, oil service (SIA) |

## OBD / scan-tool terms

| Term | Meaning |
|---|---|
| P-code | SAE J2012 powertrain DTC (`P0xxx` generic, `P1xxx` manufacturer). See [reference/obd-p-codes.md](reference/obd-p-codes.md) |
| MIL | Malfunction indicator lamp ("check engine"). Driven by the DME over CAN |
| EML | *Elektronische Motorleistungsregelung* lamp. On MINI: the amber drive-by-wire / engine-safety warning, separate from the MIL [TIS-EMS] |
| Freeze frame | SAE snapshot stored with a P-code. Less detailed than the BMW environment conditions (UW) |
| Readiness | Bit flags showing which OBD monitors have completed since the last clear |

Sources: `research/sgbd_desc/*.txt` (SGBD job, result and comment strings) [local].
[FAQ] = BMW *FAQ regarding EDIABAS, INPA and ToolSet* v2.12.
[TIS-EMS] / [TIS-BUS] = TIS *Engine Management – Overview* /
*Bus Systems – Overview* (see [reference/](reference/README.md)).
Peake R5/EMX manual glossary (third party, for MSR/EML/TEV/QL usage).
