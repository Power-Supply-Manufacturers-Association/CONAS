# CONAS — Connector Agnostic Structure

Vendor-neutral JSON Schema (draft 2020-12) data model for electrical/electronic **connectors**, part of the OpenConverters / PEAS family. A CONAS document is `{ inputs, connector, outputs }` and is also a valid PEAS document.

- **Tier 1 (catalog):** `connector.datasheetInfo` — parametric data with a family-discriminated union (`familyDetails`) covering pin headers, board-to-board, wire-to-board, terminal blocks, FFC/FPC, card edge, circular, RF, standardized data interfaces, and power connectors.
- **Tier 2 (simulation):** optional `geometry` (parametric body + external CAD refs + PCB footprint) and `contactSystem` (per-contact geometry, net map, mating interface) for 3D / FEA / thermal.
- **`conas-materials`** — shared general-purpose material registry (NDJSON), referenced by id, so electrical/thermal/mechanical/environmental/cost properties live once and are reused across datasheet, selection, SPICE and simulation.

See [`docs/schema.md`](docs/schema.md) for the at-a-glance structure diagram and the full field-by-field reference.

## Repository layout

```
schemas/
  CONAS.json               top-level container: { inputs, connector, outputs }
  connector.json          the connector component (Tier-1 datasheetInfo + Tier-2 geometry/contactSystem)
  utils.json              shared defs: mechanical, deratingCurve, familyDetails (oneOf), geometry, contactSystem
  conas-materials.json     one general-purpose material record (conductor/plating/dielectric/elastomer)
  inputs.json             operatingPoints[] + designRequirements
  inputs/
    designRequirements.json
  outputs.json            per-operating-point results (losses, thermal, derating, SI, life)
data/
  conas-materials.ndjson   material registry, one JSON record per line, referenced by id
examples/
  pin-header-2x5-254.json worked WR-PHD doc exercising both tiers
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

Runs three gates: every schema meta-validates and its `$ref`s resolve; each `examples/*.json` validates against `CONAS.json`; and each example is confirmed to be a valid **PEAS** document (the `connector` branch).

## Conventions

- JSON Schema **draft 2020-12**; `$id`s under `https://psma.com/conas/`.
- **Closed objects** (`additionalProperties: false`) everywhere; **complete discriminated unions** (`oneOf` with a `family` const) on every type break.
- **No derived/computed values** in the datasheet layer — extracted model parameters are simulation *outputs*, not catalog inputs.
- **Material properties live once** on the referenced `conas-materials` record, never copied onto the part.
- Three orthogonal attachment axes kept separate: `mechanical.mountingStyle` (board attach), `environmental.solderProcess` (solder), family-specific wire-side `termination`.

> Requires the sibling PEAS repo checked out alongside this one (cross-repo `$ref`s resolve by absolute `https://psma.com/...` `$id`).
