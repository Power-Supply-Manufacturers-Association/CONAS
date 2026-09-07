# CONAS — Connector Agnostic Structure

Vendor-neutral JSON Schema (draft 2020-12) data model for electrical/electronic **connectors** and the **accessories** that belong to a connector system, part of the OpenConverters / PEAS family. A CONAS document is `inputs` + `outputs` + exactly one component — either a `connector` or a `connectorAccessory` — and is also a valid PEAS document.

`$id` namespace: `https://psma.com/conas/...`. Cross-repo `$ref`s resolve by absolute `$id` URI against the sibling repos checked out alongside this one (PEAS in particular). CONAS reuses the PEAS shared primitives (`dimensionWithTolerance`, `manufacturerInfo`, `distributorInfo`, `datasheetInfoPartBase`, `datasheetInfoMechanical`, `multiPortOperatingPoint`, `outputBase`, `designRequirementsBase`) — it is **not** self-contained the way MAS is.

## At a glance

```
CONAS  (https://psma.com/conas/CONAS.json)   { inputs, outputs, oneOf[ connector | connectorAccessory ] }
│
├─ inputs
│   ├─ operatingPoints[]        → PEAS multiPortOperatingPoint (per-net current/voltage + ambient)
│   └─ designRequirements        → designRequirementsBase + {connectorFamily, minimumPositions,
│                                    requiredCurrentPerContact, requiredVoltageRating,
│                                    minimumMatingCycles, requiredPitch, requiredIpRating, ...}
│
├─ connector
│   ├─ manufacturerInfo
│   │   ├─ name / orderCode / datasheetUrl / ...        (PEAS shared)
│   │   └─ datasheetInfo                ◄── TIER 1: catalog / parametric
│   │       ├─ part            { partNumber, series, case, matingPolarity* }
│   │       ├─ electrical      { ratedCurrentPerContact, ratedVoltage, contactResistance,
│   │       │                    insulationResistance, dielectricWithstandingVoltage,
│   │       │                    clearance, creepage }            (IEC 60664)
│   │       ├─ mechanical      { positions, rows, pitch, orientation, mountingStyle,
│   │       │                    matingCycles, insertion/withdrawal/contactNormalForce, ... }
│   │       ├─ material        { contactBaseMaterialRef, housingMaterialRef, shieldRef,
│   │       │                    sealRef, plating{mating/termination/underplating + thickness} }
│   │       ├─ environmental   { operatingTemperature, ipRating, sealed, solderProcess,
│   │       │                    pollutionDegree, overvoltageCategory, MSL, RoHS/REACH }
│   │       ├─ derating        { currentVsAmbient, currentVsEnergizedContacts, maxTempRise }
│   │       ├─ mating          { matesWith[]{manufacturer, series, relation, matedHeight},
│   │       │                    intermateabilityStandard }
│   │       └─ familyDetails   ◄── oneOf, discriminated by `family` const  (14 variants)
│   │             pinHeaderSocket │ boardToBoard │ wireToBoard │ wireToWire │ terminalBlock │
│   │             fpcFfc │ cardEdge │ circular │ rf │ dataInterface │ power │ busbar │
│   │             acInlet │ solderPad
│   │             (each adds only its unique fields, e.g. rf → characteristicImpedance,
│   │              frequencyRange, maxVswr; terminalBlock → clampType, wireGaugeRange;
│   │              acInlet → standardSheet C1..C24, fuse/switch/filter flags)
│   │
│   ├─ distributorsInfo[]
│   ├─ geometry                ◄── TIER 2: 3D (optional)
│   │   { coordinateSystem, boundingEnvelope, matedHeight, keepOut, pcbFootprint,
│   │     mountingFeatures, parametric{housingExtrusion, contactArray}, cadModels[] (STEP/glTF) }
│   └─ contactSystem           ◄── TIER 2: simulation (optional)
│       { contacts[]{id, signalRole, position, currentRating, contactResistance,
│                    normalForce, materialRef, crossSection, pathLength},
│         nets[] (contact→net map), matingInterface, shield }
│
├─ connectorAccessory   ◄── the OTHER component branch: a connector-system part that is
│   │                        not itself a mated connector (backshell, bare contact, hood,
│   │                        cap, marker card, TPA retainer, gland, seal, cage, tool, …)
│   ├─ manufacturerInfo
│   │   └─ datasheetInfo
│   │       ├─ part              { partNumber, series, case, description, matingPolarity }
│   │       ├─ hostSystem        { series, manufacturer, standard, matesWithPartNumbers[],
│   │       │                      shellSize }   ◄── the compatibility pointer
│   │       ├─ mechanical        → the SAME conas/utils mechanical block, no minProperties
│   │       ├─ electrical        { ratedCurrentPerContact, ratedCurrentReferenceTemperature,
│   │       │                      ratedVoltage, contactResistance, characteristicImpedance }
│   │       ├─ material          → connector.json#/$defs/material   (reused verbatim)
│   │       ├─ environmental     → connector.json#/$defs/environmental (reused verbatim)
│   │       ├─ accessoryDetails  ◄── oneOf, TWO branches, each pinning `kind`
│   │       │     accessoryGeneric  kind ∈ 20 classes  │  accessoryContact  kind = contact
│   │       └─ provenance[]
│   ├─ distributorsInfo[]
│   └─ geometry                ◄── TIER 2: 3D (optional, same type as connector.geometry)
│
└─ outputs[]   (outputs[i] ↔ operatingPoints[i], each with PEAS outputBase provenance)
     contactLosses │ thermal │ currentDerating │ insulationStress │ signalIntegrity │ mechanicalLife

conas-materials.json  ◄── shared general-purpose material registry (NDJSON, referenced by id)
   { id, name, category: conductor|plating|dielectric|elastomer,
     electrical{σ, TCR, εᵣ, dielectricStrength, ...}, thermal{k, cp, CTE, emissivity, ...},
     mechanical{density, modulus, hardness, ...}, environmental{UL94, CTI, ...}, cost }
```

`*` `matingPolarity` is physical only (male/female/hermaphroditic/genderless); form factor is encoded by `family` + `mountingStyle`.

## Why a single `connector` field (not RAS-style per-type discriminators)

RAS splits at the top level (`resistor` | `varistor`) because the two device types share almost no parametrics. Connectors are the opposite: every family shares a large parametric core (positions, pitch, current/voltage rating, mating cycles, plating, mount) and differs only in a small block. So CONAS keeps **one** `connector` field and discriminates the **family internally** on `connector.datasheetInfo.familyDetails.family`. That field is the single source of truth for the family (catalog filtering reads it there).

That argument covers *connectors*. It does **not** stretch to the accessories that ship with a connector system — a backshell shares none of that parametric core, because it carries no current and has no contacts. Those are a second top-level component, `connectorAccessory`, described below.

## Two tiers

### Tier 1 — catalog / parametric (`connector.manufacturerInfo.datasheetInfo`)
Mirrors the RAS/CAS datasheet pattern. Four blocks are **required** — `part`, `electrical`, `mechanical`, `familyDetails` — and required here means *populated*, not merely present. Draft 2020-12 satisfies `required` by the key existing, so `"electrical": {}` and `"mechanical": {}` used to validate while carrying nothing; both now also carry **`minProperties: 1`**, so an empty block is rejected. (`part` and `familyDetails` need no such guard: they cannot be empty already — `part` requires `partNumber` through the PEAS part base, and every `familyDetails` variant requires its `family` const.) Blocks:

| Block | Holds |
|---|---|
| `part` | partNumber, series, case, description, **matingPolarity** (male/female/hermaphroditic/genderless — physical polarity only; form factor is encoded by family + mountingStyle) |
| `electrical` | ratedCurrentPerContact (+ reference temp), ratedVoltage, contactResistance, insulationResistance, dielectricWithstandingVoltage, **clearance**, **creepage** (IEC 60664 selection ratings), **pairRatings[]** (per-counterpart current/voltage/IP rows — several connector ratings are pair properties, not part properties; the scalars stay as the standalone/worst-case figures), **insulationPaths[]** (approved 2026-08, ABT #468: per-conductor-pair IEC 60664-1 chain — from/to, creepage, clearance, workingVoltage, ratedImpulseVoltage, pollutionDegree, overvoltageCategory, materialGroup, ratingContext — making the chain's inputs co-resident by construction; the bare clearance/creepage scalars are legacy, with no reference pair). `ratedCurrentPerContact` is required for every family **except `rf`** — RF/coaxial connectors are defined by `familyRf.characteristicImpedance`, frequency and VSWR, not a published per-contact DC current |
| `mechanical` | positions, rows, pitch/rowPitch, orientation, **mountingStyle** (board-attach axis only), matingCycles, insertion/withdrawal/**contactNormalForce**, locking, body dimensions |
| `material` | `*Ref` ids into `conas-materials` for contact base / housing / shield / seal, plus the `plating` stack (mating + termination + underplating, with thicknesses). Material properties (UL-94, σ, εᵣ, …) live once on the referenced `conas-materials` record, never copied here |
| `environmental` | operatingTemperature range, ipRating, sealed, **solderProcess** (solder axis only), **pollutionDegree** + **overvoltageCategory** (IEC 60664), MSL, RoHS/REACH |
| `derating` | currentVsAmbient curve **and** currentVsEnergizedContacts curve, maxTemperatureRise — thermal-simulation validation target |
| `mating` | the interchangeability surface: **matesWith[]** (series-level counterpart relations — mates / intermateableStandard / mandatoryCompanion / optionalCompanion, optional per-pair matedHeight) and **intermateabilityStandard** (e.g. 'IEC 61076-2-101' for M12 — the strongest cross-vendor signal). The other interchange axes already have homes: durability = `mechanical.matingCycles`, board attach = `mechanical.mountingStyle`, plating = `material.plating`, circular keying = `familyDetails.coding` |
| `familyDetails` | the discriminated union — see below |

Three orthogonal attachment axes are kept separate (no overlapping enums): **mountingStyle** (how the board side attaches: tht/smt/pressFit/skedd/panel/cable), **solderProcess** (reflow/wave/selective/handSolder/throughHoleReflow — only when soldered), and **family-specific wire-side termination** (crimp/idc/screw/busbar… in `familyDetails`). Derived/extracted lumped model values (per-contact L/C, extracted impedance) are **not** stored in the datasheet layer — they are simulation outputs (`outputs.signalIntegrity`); only genuinely datasheet-published impedance lives on the relevant family (`familyRf`, `familyDataInterface`).

**`familyDetails`** is a `oneOf` over closed variants, each tagged by a `family` const:
`pinHeaderSocket`, `boardToBoard`, `wireToBoard`, `wireToWire`, `terminalBlock`, `fpcFfc`, `cardEdge`, `circular`, `rf`, `dataInterface`, `power`, `busbar`, `acInlet`, `solderPad`. Each variant carries only what is unique (e.g. `rf` adds characteristicImpedance + frequencyRange + maxVswr; `terminalBlock` adds clampType + wireGaugeRange; `circular` adds shellSize + coding + couplingType; `power` covers WR-MPC/NPC high-current and WR-DC barrel jacks, adding powerStyle + barrel dimensions; `solderPad` is the bare-PCB-pad boundary sentinel). The enum is reconciled against the Würth Connectivity catalog (WR-* series). SKEDD press-in is a *termination*, not a family — it appears in the termination/mountingStyle enums.

Notes on the three families added 2026-07 (field surface chosen from live distributor/vendor parametric filters — DigiKey "Rectangular Connectors — Free Hanging, Panel Mount", "Power Entry Connectors — Inlets, Outlets, Modules"; Molex Mini-Fit Jr., Littelfuse Common BusBar, SCHURTER 6100 datasheets):

- **`wireToWire`** — in-line plug/receptacle pairs joining two cable harnesses with no board side (Molex Mini-Fit Jr., JST SM, TE AMP Superseal). Adds only `housingStyle` (plug/receptacle — a *housing* role, independent of `part.matingPolarity`: a plug housing commonly carries female terminals), `termination` (crimp/idc/poke-in/solderCup, same axis as `wireToBoard`), `wireGaugeRange`, `secondaryLock` (TPA). Free-hanging vs panel-mount is `mechanical.mountingStyle` (`cable` vs `panel`); sealing (Superseal-style IP67) is `environmental.ipRating`/`sealed`.
- **`busbar`** — solid/laminated/flexible bare distribution conductors with bolted hole/stud connection points. Adds `construction`, `barMaterialRef` + `platingMaterialRef` (conas-materials ids — busbars have **no housing**, so the shared `material` block, whose `housingMaterialRef` is required, does not apply), `crossSection` {width, thickness, area}, and the connection pattern `holeCount`/`holeDiameter`/`holeSpacing`/`studThread`. The bar's rated current is `electrical.ratedCurrentPerContact`; overall length is `mechanical.length`. **No `pitch`** — a busbar is not a pitched contact array (that miscategorization is what this family fixes).
- **`acInlet`** — IEC 60320 appliance couplers for power entry. `standardSheet` (required) is a closed enum of the 60320 sheets C1–C24 (even = appliance inlets C2/C6/C8/C14/C16/C16A/C18/C20/C22/C24; odd = connectors/outlets — equipment-mounted C13/C15/C19 bodies are the IEC 60320-2-2 appliance outlets universally named by their sheet). Adds `mounting` (screwFlange/snapIn/pcb — refines `mechanical.mountingStyle`), `terminalStyle` (quickConnect/solder/pcb), and the power-entry-module flags `integratedFuseHolder`/`integratedSwitch`/`integratedFilter`. Rated current/voltage stay in the shared `electrical` block (fixed per sheet, restated by vendors — e.g. C14 = 10 A / 250 VAC IEC).

### Tier 2 — 3D + simulation (`connector.geometry`, `connector.contactSystem`)
Optional, closed blocks populated only for parts you model in 3D, render, or simulate. They never dilute the Tier-1 catalog.

- **`geometry`** — hybrid 3D body: `coordinateSystem` (units + origin datum + mate axis), `boundingEnvelope` (all three axes optional since 2026-08 — length is often a per-series formula and is implied by the contactArray), `matedHeight`, `keepOut`, `pcbFootprint` (the shared **PEAS `landPattern`** type — hoisted 2026-08; pad ids match contact ids; shape is pure geometry, through-board character is `drill`/`plated`), `mountingFeatures`, a `parametric` generator (housing extrusion profile + contact array) for the regular families, and `cadModels[]` references to external STEP/IGES/glTF/3MF/STL with units, LOD and checksum. Parametric and CAD are complementary — parametric reconstructs regular bodies; CAD carries the exact organic housing.
- **`contactSystem`** — the conductive system (consumed by SI extraction and EM/thermal simulation): `contacts[]` (id, pinName, signalRole — the shared **PEAS `pinFunction`** vocabulary, position, per-contact currentRating/contactResistance/normalForce, base+plating material refs, cross-section, path length), `nets[]` (contact→net map for current/voltage injection), `matingInterface` (partner part, contact type, mate/unmate force, wipe), `shield`.

## `connectorAccessory` — the second component branch

A connector system is sold as more than its mated connectors. Backshells, loose crimp
contacts, hoods, protective caps, marker cards, TPA retainers, cable glands, wire seals,
screwlocks, jumper bars, splices, contact inserts, SFP cages, RF adapters, insertion
tools, coding keys, EMI shields, LED holders, cavity plugs and IC sockets are all real,
orderable parts with part numbers, temperature ratings and datasheets — and **none of
them is a connector**.

### Why they are not a fifteenth `familyDetails` branch

`connector.datasheetInfo` requires four blocks: `part`, `electrical`, `mechanical`,
`familyDetails`. Measured over the 18,995 such parts sitting in the TAS connector
quarantine, an accessory is missing three of the four *structurally*, not for want of
sourcing:

| what `connector.json` requires | accessories that can supply it |
|---|---|
| `electrical` (with `minProperties: 1`) | 3,716 of 18,995 — **80% carry `"electrical": {}`**, literally empty |
| `mechanical` (with `minProperties: 1`) | 3,008 of 18,995 — **84% carry `"mechanical": {}`** |
| `familyDetails` (14-branch `oneOf`) | **0 of 18,995** |

A backshell has no current rating because a backshell carries no current. A marker card
has no pitch, no mating cycles and no insertion force. A TPA retainer is not a
`wireToBoard` connector; it is a plastic part that clips into one. No amount of datasheet
work changes any of that.

Admitting them as a fifteenth family would have meant relaxing `electrical` and
`mechanical` from required to optional on `connector.json` — re-opening exactly the
empty-block hole `minProperties: 1` was added to close, for all fourteen real families.
So accessories get their own top-level component, a sibling of `connector`, and
`CONAS.json` becomes a closed two-branch `oneOf`: a document carries a `connector` **or**
a `connectorAccessory`, never both and never neither.

### Why TWO union branches, not twenty-one

The obvious shape is one `oneOf` branch per accessory class. It is the wrong shape here:
the measured field profile is **near-constant across the classes** — identity, plus a
host-system pointer, plus (sometimes) a temperature range and a position count, differing
by only three or four descriptors. Twenty-one branches would be twenty-one copies of one
object, and the house DRY rule cuts against that.

So `accessoryDetails` is a `oneOf` over **two** branches:

- **`accessoryGeneric`** — one shared shape whose `kind` enumerates the twenty classes
  that share that profile.
- **`accessoryContact`** — a distinct branch for bare crimp/solder/coax contacts
  (`kind: "contact"`), because their shape genuinely differs: 3,944 rows, 84% with a real
  per-contact current rating, 89% with a mating polarity, plus a termination, a wire
  gauge and a contact size.

The two branches are **disjoint by construction**: the generic enum excludes `contact`
and the contact branch pins `kind` to the `const` `"contact"`. No record can match both,
so nothing misclassifies — a TPA retainer cannot be silently validated as a cage, and a
contact cannot be validated as a backshell (the MAS wire-union lesson). The union is a
real discriminator, not decoration.

### `connectorAccessory` blocks

Only `part` and `accessoryDetails` are required inside `datasheetInfo`. There is **no
`minProperties` guard** anywhere in this family, and that is deliberate: for a connector
an empty `electrical` block is a defect, for an accessory the *absence* of the block is
the truth. The family never asks for an empty object, so it never has to reject one.

| Block | Required | Holds |
|---|---|---|
| `part` | **yes** | `allOf` over the PEAS `datasheetInfoPartBase` (partNumber, series, case, description) plus `matingPolarity` (male/female/hermaphroditic/genderless — meaningful mainly on bare contacts and hermaphroditic backshells), sealed with top-level `unevaluatedProperties: false`. The accessory class is **not** here: it lives on `accessoryDetails.kind`, the single source of truth, exactly as the connector family lives on `familyDetails.family` |
| `hostSystem` | no | **The compatibility pointer, and the field that makes an accessory orderable** — "the backshell for Mini-Fit Jr., 10 circuits". `series` (the vendor SERIES string: `Mini-Fit Jr.`, `Micro-Fit+`, `AMPLIMITE`, `SFP-DD` — populated on 18,993 of 18,995 measured rows), `manufacturer` (when the host is another vendor's system), `standard` (`SFP-DD`, `Zhaga Book 18`, `MIL-DTL-38999`), `matesWithPartNumbers[]`, `shellSize`. Note this is a *vendor series*, **not** a CONAS family const |
| `mechanical` | no | `$ref` to `conas/utils.json#/$defs/mechanical` — the **same block the connector uses**, reused unchanged and without `minProperties`. Position count, rows, pitch, mounting style and body dimensions all live here, so `accessoryDetails` never restates them |
| `electrical` | no | A small, accessory-specific block — `ratedCurrentPerContact`, `ratedCurrentReferenceTemperature`, `ratedVoltage`, `contactResistance`, `characteristicImpedance`. Deliberately **not** the connector `electrical` block: no vendor publishes pairRatings, insulationPaths, clearance/creepage or dielectric withstanding for a backshell. Populated on the carrying classes only — bare contacts, contact inserts, jumper bars, IC sockets, coaxial contacts and RF adapters |
| `material` | no | `$ref` to `connector.json#/$defs/material`, **reused verbatim** — the `*Ref` ids into `conas-materials` for contact base / housing / shield / seal plus the `plating` stack. An accessory's housing polymer and contact plating are the same vocabulary, so plating is *not* restated on the contact branch |
| `environmental` | no | `$ref` to `connector.json#/$defs/environmental`, **reused verbatim**. `operatingTemperature` is the single most commonly published accessory rating (61% of measured rows) |
| `accessoryDetails` | **yes** | The two-branch discriminated union — below |
| `provenance` | no | `$ref` to the PEAS `provenance` type; same trail as every other part |
| `geometry` (component level, Tier 2) | no | `$ref` to `conas/utils.json#/$defs/geometry` — the same 3D type as `connector.geometry`, for the accessories that are worth modelling (cages and IC sockets have PCB footprints; backshells and hoods have bodies) |

### `accessoryDetails` branch 1 — `accessoryGeneric`

`kind` is required; **every other field is optional**, because the whole point of the
family is that these parts publish an identity and a host system and often nothing else.
The descriptors are the union of what the twenty classes distinguish themselves by; a
class populates the three or four that apply to it.

`kind` ∈ `backshell` · `hoodShell` · `capCover` · `identificationLabel` ·
`terminalPositionAssurance` · `cableEntry` · `sealGasket` · `sealingPlug` ·
`mountingHardware` · `busbarJumper` · `cableSplice` · `contactInsert` ·
`transceiverCage` · `rfAdapter` · `tooling` · `codingKey` · `emiShield` ·
`lightingHolder` · `icSocket` · `other`

`other` is an explicit, **closed and empty-of-obligation** escape hatch for the long tail
of one-off accessories (grounding blocks, shunts, backplates, motor connection kits) —
a named class, not an open door.

| Field | Unit / type | Used by |
|---|---|---|
| `kind` | enum, **required** | all |
| `shellSize` | string (alphanumeric vendor code, not a length) | hoods, backshells, cable clamp kits |
| `cableExit` | enum `straight` · `rightAngle` · `angled45` · `angled30` · `variable` | backshells, hoods, glands |
| `cableDiameterRange` | `{minimum, maximum}` in **m** (a single published diameter sets both) | glands, backshells, clamp kits, splices |
| `threadDesignation` | string, as published (`M20 x 1.5`, `PG16`, `4-40 UNC`) | glands, screwlocks, nuts, studs |
| `sealType` | enum `oRing` · `wireSeal` · `cavitySeal` · `panelGasket` · `interfaceSeal` · `emiGasket` · `boot` · `sleeve` | sealGasket, sealingPlug |
| `shielded` | boolean | metallised backshells, EMI hoods and shields |
| `tethered` | boolean (captive on a lanyard vs loose) | capCover |
| `markingText` | string, the pre-printed legend verbatim (`11-20`, `L1 L2 L3 N PE`) | identificationLabel (blank strips omit it) |
| `portsWide` / `portsHigh` | integer | transceiverCage (the 4 and the 1 of a 1-by-4 cage) |
| `interfaceA` / `interfaceB` | string (`SMA`, `N`, `BNC`); equal for an in-series adapter | rfAdapter |
| `hardwareType` | enum `nut` · `screw` · `screwlock` · `jackscrew` · `washer` · `bracket` · `rail` · `threadedInsert` · `clip` · `standoff` · `stud` · `other` | mountingHardware |
| `toolType` | enum `insertion` · `extraction` · `crimp` · `applicator` · `press` · `die` · `gauge` · `other` | tooling |
| `codingPosition` | string, as published (`A`, `1-4`) | codingKey |

### `accessoryDetails` branch 2 — `accessoryContact`

A bare contact — crimp, solder, IDC, press-fit or coaxial terminals sold loose, to be
loaded into a housing. `kind` is pinned to the const `"contact"`.

| Field | Unit / type |
|---|---|
| `kind` | `const: "contact"`, **required** |
| `terminationStyle` | enum `crimp` · `solder` · `solderCup` · `idc` · `pressFit` · `screw` · `wireWrap` · `weld` · `pierce` · `pokeIn` |
| `wireGaugeRange` | `$ref` to `conas/utils.json#/$defs/wireGaugeRange` — the terminal-block type, reused unchanged (AWG and/or SI area in m²) |
| `contactSize` | string — a size **code** (`16`, `22`, `0`), not a length: the MIL/AMP scale is ordinal and vendors also publish letters |
| `contactRetention` | enum `lockingLance` · `retentionClip` · `shoulder` · `screwMachine` · `none` |

Ratings live in the shared `electrical` block and plating in the shared `material` block,
so neither is restated here.

**A contact must say something that makes it a contact.** Beyond `kind`, the branch
carries an `anyOf` requiring **at least one** of `terminationStyle`, `wireGaugeRange`,
`contactSize` or `contactRetention`. A record carrying only `{"kind": "contact"}` names a
class and describes nothing — it is indistinguishable from an unsourced seed while
claiming to be a real orderable terminal, so it is rejected. This is the branch's whole
reason for existing, and it is the one gate in the family that has a residue (see below).

### Requirement side

`inputs/designRequirements.json` gains two accessory-side fields alongside
`connectorFamily`:

- **`accessoryKind`** — `$ref`s the part-side anchor
  `connectorAccessory.json#/$defs/accessoryKind` (the twenty generic classes plus
  `contact`, defined as *one* list, not a second copy), so the selection vocabulary
  cannot drift from the part vocabulary.
- **`hostSeries`** — the host connector system the accessory must fit. This, not the
  class, is what actually selects an accessory: a backshell only fits the series it was
  drawn for.

A requirements document constrains `connectorFamily` **or** the accessory pair, never
both.

### Coverage against real data

Converted from the 18,995 accessory rows measured in `TAS/data/quarantine.ndjson`
(the cohort of ABT #1138), with per-`kind` descriptors mined from the vendor description
strings:

| | rows |
|---|---:|
| accessory cohort | 18,995 |
| **validate as `connectorAccessory`** | **18,375 (96.7%)** |
| residue | 620 (3.3%) |

The residue is **entirely** bare contacts — 620 of the 3,944 — whose vendor description
names no termination, no wire gauge, no contact size and no retention (`"Gold (Au),
Socket Contact"`, `"Cable Contact Tube"`, `"Power Contact Assembly, Phosphor Bronze"`).
They are real parts; they are held out by the `anyOf` gate above, on purpose, until one
of those four fields is sourced from the drawing. Every one of the other twenty classes
converts at 100%.

## `conas-materials` — shared general-purpose material registry

Material properties are **not inlined per part**. They live in `conas-materials.json` records (stored as NDJSON in `data/conas-materials.ndjson`, like MAS `core_materials.ndjson`) and are referenced by `id` string. The registry is **general-purpose, not simulation-specific** — the same record serves datasheet documentation, part selection/filtering, cost/compliance, SPICE / signal-integrity extraction, and electromagnetic/thermal/structural simulation.

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
## Provenance (data-source trail)

Every `datasheetInfo` carries an optional `provenance` array recording where its data
came from. Optional and closed, so records without it remain valid. Each entry:

| field | meaning |
|---|---|
| `source` | `manufacturerDatasheet` · `manufacturerParametric` · `manufacturerDatabase` · `distributor` · `librarianEnrichment` · `scrape` · `manual` |
| `sourceName` | human-readable source, e.g. `"TI parametric API"`, `"WE - Passive Components.mdb"`, `"DigiKey"` |
| `sourceUrl` | URL the value came from (optional) |
| `retrievedDate` | `YYYY-MM-DD` (optional) |
| `fields` | which `datasheetInfo` fields this source supplied — for mixed-source records (optional) |

It is a **list**: a record may combine sources (e.g. specs from the datasheet, a rated
voltage from a distributor, a missing field back-filled by librarian enrichment). The
canonical definition lives in `PEAS/schemas/utils.json#/$defs/provenance` (mirrored in
`MAS/schemas/utils.json`, which is self-contained).
