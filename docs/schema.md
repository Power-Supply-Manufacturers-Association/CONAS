# COAS — Connector Agnostic Structure

Vendor-neutral JSON Schema (draft 2020-12) data model for electrical/electronic **connectors**, part of the OpenConverters / PEAS family. Every valid COAS document is also a valid PEAS document (`inputs` + `connector` + `outputs`).

`$id` namespace: `https://psma.com/coas/...`. Cross-repo `$ref`s resolve by absolute `$id` URI against the sibling repos checked out alongside this one (PEAS in particular). COAS reuses the PEAS shared primitives (`dimensionWithTolerance`, `manufacturerInfo`, `distributorInfo`, `datasheetInfoPartBase`, `datasheetInfoMechanical`, `multiPortOperatingPoint`, `outputBase`, `designRequirementsBase`) — it is **not** self-contained the way MAS is.

## Why a single `connector` field (not RAS-style per-type discriminators)

RAS splits at the top level (`resistor` | `varistor`) because the two device types share almost no parametrics. Connectors are the opposite: every family shares a large parametric core (positions, pitch, current/voltage rating, mating cycles, plating, mount) and differs only in a small block. So COAS keeps **one** `connector` field and discriminates the **family internally** on `connector.datasheetInfo.familyDetails.family`. That field is the single source of truth for the family (catalog filtering reads it there).

## Two tiers

### Tier 1 — catalog / parametric (`connector.manufacturerInfo.datasheetInfo`)
Mirrors the RAS/CAS datasheet pattern. Blocks:

| Block | Holds |
|---|---|
| `part` | partNumber, series, case, description, **matingPolarity** (male/female/hermaphroditic/genderless — physical polarity only; form factor is encoded by family + mountingStyle) |
| `electrical` | ratedCurrentPerContact (+ reference temp), ratedVoltage, contactResistance, insulationResistance, dielectricWithstandingVoltage, **clearance**, **creepage** (IEC 60664 selection ratings) |
| `mechanical` | positions, rows, pitch/rowPitch, orientation, **mountingStyle** (board-attach axis only), matingCycles, insertion/withdrawal/**contactNormalForce**, locking, body dimensions |
| `material` | `*Ref` ids into `coas-materials` for contact base / housing / shield / seal, the `plating` stack (mating + termination + underplating, with thicknesses), UL-94 class |
| `environmental` | operatingTemperature range, ipRating, sealed, **solderProcess** (solder axis only), **pollutionDegree** + **overvoltageCategory** (IEC 60664), MSL, RoHS/REACH |
| `derating` | currentVsAmbient curve **and** currentVsEnergizedContacts curve, maxTemperatureRise — thermal-simulation validation target |
| `familyDetails` | the discriminated union — see below |

Three orthogonal attachment axes are kept separate (no overlapping enums): **mountingStyle** (how the board side attaches: tht/smt/pressFit/skedd/panel/cable), **solderProcess** (reflow/wave/selective/handSolder/throughHoleReflow — only when soldered), and **family-specific wire-side termination** (crimp/idc/screw/busbar… in `familyDetails`). Derived/extracted lumped model values (per-contact L/C, extracted impedance) are **not** stored in the datasheet layer — they are simulation outputs (`outputs.signalIntegrity`); only genuinely datasheet-published impedance lives on the relevant family (`familyRf`, `familyDataInterface`).

**`familyDetails`** is a `oneOf` over closed variants, each tagged by a `family` const:
`pinHeaderSocket`, `boardToBoard`, `wireToBoard`, `terminalBlock`, `fpcFfc`, `cardEdge`, `circular`, `rf`, `dataInterface`, `power`. Each variant carries only what is unique (e.g. `rf` adds characteristicImpedance + frequencyRange + maxVswr; `terminalBlock` adds clampType + wireGaugeRange; `circular` adds shellSize + coding + couplingType; `power` covers WR-MPC/NPC high-current and WR-DC barrel jacks, adding powerStyle + barrel dimensions). The enum is reconciled against the Würth Connectivity catalog (WR-* series). SKEDD press-in is a *termination*, not a family — it appears in the termination/mountingStyle enums.

### Tier 2 — 3D + simulation (`connector.geometry`, `connector.contactSystem`)
Optional, closed blocks populated only for parts you model in 3D, render, or simulate. They never dilute the Tier-1 catalog.

- **`geometry`** — hybrid 3D body: `coordinateSystem` (units + origin datum + mate axis), `boundingEnvelope`, `matedHeight`, `keepOut`, `pcbFootprint` (pad/hole pattern, pad ids match contact ids), `mountingFeatures`, a `parametric` generator (housing extrusion profile + contact array) for the regular families, and `cadModels[]` references to external STEP/IGES/glTF/3MF/STL with units, LOD and checksum. Parametric and CAD are complementary — parametric reconstructs regular bodies; CAD carries the exact organic housing.
- **`contactSystem`** — the conductive system (consumed by SI extraction and EM/thermal simulation): `contacts[]` (id, pinName, signalRole, position, per-contact currentRating/contactResistance/normalForce, base+plating material refs, cross-section, path length), `nets[]` (contact→net map for current/voltage injection), `matingInterface` (partner part, contact type, mate/unmate force, wipe), `shield`.

## `coas-materials` — shared general-purpose material registry

Material properties are **not inlined per part**. They live in `coas-materials.json` records (stored as NDJSON in `data/coas-materials.ndjson`, like MAS `core_materials.ndjson`) and are referenced by `id` string. The registry is **general-purpose, not simulation-specific** — the same record serves datasheet documentation, part selection/filtering, cost/compliance, SPICE / signal-integrity extraction, and electromagnetic/thermal/structural simulation.

Properties are grouped: `electrical`, `thermal`, `mechanical`, `environmental`, `cost`. `category` ∈ {`conductor`, `plating`, `dielectric`, `elastomer`} drives only the **required defining property**; everything else is optional, so a material catalogued for one purpose (e.g. electrical only) still validates.

- **conductor / plating** — require `electrical.electricalConductivity`; commonly also TCR, thermal (k, cₚ, CTE, emissivity, melting point), mechanical (modulus, yield, Vickers hardness).
- **dielectric** — require `electrical.relativePermittivity` + `electrical.dielectricStrength`; commonly also lossTangent, volume resistivity, thermal (k, cₚ, CTE, Tg, max service temp), mechanical, UL-94, CTI, water absorption.
- **elastomer** (seals/gaskets) — defined mechanically (Shore A hardness, elongation, density); environmental sealing/temperature.

Consumers read the subset they need and throw if a required property is absent (no fabricated defaults), so a thermal solve simply requires the thermal block be populated for the materials it touches.

## Outputs (`outputs[i]` ↔ `operatingPoints[i]`)

Each block carries the PEAS `outputBase` provenance shell: `contactLosses`, `thermal` (contact temperature rise, hot-spot), `currentDerating` (applied vs derated limit, pass/fail), `insulationStress` (clearance/creepage vs applied), `signalIntegrity` (impedance, insertion/return loss), `mechanicalLife`. The `thermal`/`currentDerating` blocks are what an FEA run produces and what the datasheet `derating` curve checks.

## Validate

```bash
pip install jsonschema referencing
python3 scripts/validate.py     # schemas meta-validate, refs resolve, examples validate
```

## Standards leaned on

- Field inventory cross-referenced to **eCl@ss / IEC 61360 CDD** connector classes (the only ISO 13584/IEC 61360-conformant vendor-neutral data dictionary).
- Family taxonomy and test-defined fields (mating cycles, dielectric withstanding voltage, derating) follow **IEC 61076** / **IEC 60603**.
- IP codes per **IEC 60529**, flammability per **UL 94**, CTI per **IEC 60112**, MSL per **JEDEC J-STD-020**.
