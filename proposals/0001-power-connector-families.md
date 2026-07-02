# CONAS-RFC 0001 — Missing power-connector families (wireToWire, busbar, acInlet, lugs)

- **Status:** Partially implemented 2026-07-02 — `wireToWire`, `busbar`, `acInlet` branches added to
  `familyDetails` (+ `designRequirements.connectorFamily`, docs, examples). `lugs` still pending design;
  the TAS/data migration pass for the misfiled parts is a separate follow-up.
- **Created:** 2026-07-02

## Problem

Power-converter builds need connector families the `familyDetails` oneOf lacks:

1. **wireToWire** — 2,584+ wire-to-wire parts currently squeezed into `wireToBoard`/others.
2. **busbar** — laminated/stamped busbars are unrepresentable (busbar exists only as a
   powerStyle/termination enum value); 190 A bus-bar parts sit misrouted in `pinHeaderSocket`.
3. **acInlet** — IEC 60320 appliance inlets/outlets (C13/C14/C20…).
4. **lugs / quick-connect tabs** — orderable parts today only expressible as `termination`
   values on `power`.

## Direction (to be designed)

Four new closed `familyDetails` branches following the existing pattern (distinct `family`
consts). Migration pass over TAS/data/connectors.ndjson to re-route the misfiled parts
(149 busbar-described parts identified in the review; importer routing rules updated).
