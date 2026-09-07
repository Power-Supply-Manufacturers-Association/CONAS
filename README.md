# CONAS — Connector Agnostic Structure

Vendor-neutral JSON Schema (draft 2020-12) data model for electrical/electronic **connectors** and the **accessories** that belong to a connector system, part of the OpenConverters / PEAS family. A CONAS document is `{ inputs, outputs }` plus exactly one component — `connector` **or** `connectorAccessory` — and is also a valid PEAS document.

- **Tier 1 (catalog):** `connector.datasheetInfo` — parametric data with a family-discriminated union (`familyDetails`) covering pin headers, board-to-board, wire-to-board, wire-to-wire, terminal blocks, FFC/FPC, card edge, circular, RF, standardized data interfaces, power connectors, busbars, IEC 60320 AC inlets, and bare solder pads.
- **Tier 2 (simulation):** optional `geometry` (parametric body + external CAD refs + PCB footprint) and `contactSystem` (per-contact geometry, net map, mating interface) for 3D / FEA / thermal.
- **`connectorAccessory`** — the second component branch: real, orderable connector-system parts that are **not** mated connectors (backshells, bare crimp/solder contacts, hoods, caps, marker cards, TPA retainers, glands, seals, mounting hardware, jumper bars, splices, contact inserts, transceiver cages, RF adapters, tooling, coding keys, EMI shields, LED holders, sealing plugs, IC sockets). They cannot use `connector.json`, which requires `part` + `electrical` + `mechanical` + `familyDetails`: measured over 18,995 such parts, 80% carry an empty `electrical`, 84% an empty `mechanical` and 100% have no connector family. `accessoryDetails` is a two-branch `oneOf` — one shared shape whose `kind` enumerates the twenty classes with a common field profile, plus a distinct `contact` branch for bare contacts, which do carry real ratings.
- **`conas-materials`** — shared general-purpose material registry (NDJSON), referenced by id, so electrical/thermal/mechanical/environmental/cost properties live once and are reused across datasheet, selection, SPICE and simulation.

See [`docs/schema.md`](docs/schema.md) for the at-a-glance structure diagram and the full field-by-field reference.

## Repository layout

```
schemas/
  CONAS.json               top-level container: { inputs, outputs } + oneOf[ connector | connectorAccessory ]
  connector.json          the connector component (Tier-1 datasheetInfo + Tier-2 geometry/contactSystem)
  connectorAccessory.json  the accessory component (identity + hostSystem + accessoryDetails oneOf)
  utils.json              shared defs: mechanical, deratingCurve, familyDetails (oneOf), geometry, contactSystem
  conas-materials.json     one general-purpose material record (conductor/plating/dielectric/elastomer)
  inputs.json             operatingPoints[] + designRequirements
  inputs/
    designRequirements.json
  outputs.json            per-operating-point results (losses, thermal, derating, SI, life)
data/
  conas-materials.ndjson   material registry, one JSON record per line, referenced by id
examples/
  pin-header-2x5-254.json          worked WR-PHD doc exercising both tiers
  wire-to-wire-minifit-jr-6.json   Molex Mini-Fit Jr. 5557 receptacle (wireToWire)
  busbar-littelfuse-880118.json    Littelfuse 250 A stud busbar (busbar)
  ac-inlet-schurter-6100-4115.json SCHURTER IEC C14 snap-in inlet (acInlet)
  backshell-molex-2047230010.json  Molex Mini-Fit Jr. hermaphroditic backshell (accessory, kind backshell)
  contact-molex-1727040142.json    Molex FCT high-power crimp contact (accessory, kind contact)
docs/
  schema.md               structure diagram + field reference
scripts/
  validate.py             meta-validates schemas, resolves cross-refs, validates examples + PEAS citizenship
```

## Validate

```bash
pip install jsonschema referencing
python3 scripts/validate.py
```

Runs three gates: every schema meta-validates and its `$ref`s resolve; each `examples/*.json` validates against `CONAS.json`; and each example is confirmed to be a valid **PEAS** document (the `connector` / `connectorAccessory` branch).

## Conventions

- JSON Schema **draft 2020-12**; `$id`s under `https://psma.com/conas/`.
- **Closed objects** (`additionalProperties: false`) everywhere; **complete discriminated unions** (`oneOf` with a `family` const) on every type break.
- **A required object must carry something**: `required` alone is satisfied by the key being present, so required blocks that would otherwise accept `{}` also declare `minProperties: 1` (`connector.datasheetInfo.electrical`, `connector.datasheetInfo.mechanical`). Empty *arrays* are left alone — an empty list can be a real statement. `connectorAccessory` carries **no** such guard, and needs none: its `electrical` and `mechanical` blocks are optional, so the family never asks for an empty object and never has to reject one.
- **No derived/computed values** in the datasheet layer — extracted model parameters are simulation *outputs*, not catalog inputs.
- **Material properties live once** on the referenced `conas-materials` record, never copied onto the part.
- Three orthogonal attachment axes kept separate: `mechanical.mountingStyle` (board attach), `environmental.solderProcess` (solder), family-specific wire-side `termination`.

> Requires the sibling PEAS repo checked out alongside this one (cross-repo `$ref`s resolve by absolute `https://psma.com/...` `$id`).
