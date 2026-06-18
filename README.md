# COAS — Connector Agnostic Structure

Vendor-neutral JSON Schema (draft 2020-12) data model for electrical/electronic **connectors**, part of the OpenConverters / PEAS family. A COAS document is `{ inputs, connector, outputs }` and is also a valid PEAS document.

- **Tier 1 (catalog):** `connector.datasheetInfo` — parametric data with a family-discriminated union (`familyDetails`) covering pin headers, board-to-board, wire-to-board, terminal blocks, FFC/FPC, card edge, circular, RF, and standardized data interfaces.
- **Tier 2 (simulation):** optional `geometry` (parametric body + external CAD refs + PCB footprint) and `contactSystem` (per-contact geometry, net map, mating interface) for 3D / FEA / thermal.
- **`coas-materials`** — shared general-purpose material registry (NDJSON), referenced by id, so electrical/thermal/mechanical/environmental/cost properties live once and are reused across datasheet, selection, SPICE and simulation.

See [`docs/schema.md`](docs/schema.md) for the full field reference.

```bash
pip install jsonschema referencing
python3 scripts/validate.py
```

> Requires the sibling PEAS repo checked out alongside this one (cross-repo `$ref`s resolve by absolute `https://psma.com/...` `$id`).
