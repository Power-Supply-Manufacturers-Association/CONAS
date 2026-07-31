#!/usr/bin/env python3
"""Add the three materials the Sullins + WAGO parametric imports name and cannot store.

WHY: mapping Sullins' and WAGO's own material columns onto the registry covers 98,227
connectors, but three strings have no id to point at, so those parts would keep nothing:

  silver plating   209 WAGO parts
  PEEK           2,541 Sullins parts
  spinodal CuNiSn  622 Sullins parts

Each is an unambiguous, named material — unlike "Copper alloy" (9,934 WAGO parts), which
stays unmapped for exactly the reason it always has: the vendor does not say which alloy,
and conductivity is the defining property of a conductor entry.

SOURCING, same discipline as add_materials_2026_07.py — cited tables, not recall:

  Silver — CRC/ASM room-temperature metal tables (6.30e7 S/m = 108% IACS, 429 W/m-K,
  10 490 kg/m3, 962 C). Electrodeposited engineering silver is ASTM B700. Hardness is
  annealed fine silver (~25 HV); hard-bright deposits run far higher and are not recorded
  here because the deposit temper is not what a part number states.

  PEEK — Professional Plastics, "Electrical Properties of Plastic Materials", the same
  table the 2026-07 dielectrics came from, so the values stay mutually consistent
  (Dk 3.2 @ 1 MHz, 480 V/mil = 1.89e7 V/m, 4.9e16 Ohm-cm -> 4.9e14 Ohm-m). Tg 143 C and
  Tm 343 C are the standard unfilled-PEEK transitions (Victrex 450G).

  Spinodal — Sullins says only "Spinodal". The connector spinodal alloy is Cu-15Ni-8Sn,
  UNS C72900 (Materion ToughMet 3), and that is what the record describes; the temper is
  NOT stated by Sullins, so only temper-independent properties are recorded (conductivity,
  density, modulus). Strength and hardness vary ~2x across TS95/TS160 tempers and are
  deliberately absent rather than pinned to a temper nobody specified.

  add_materials_2026_08.py [--apply]
"""
import argparse
import json
import sys
from pathlib import Path

CONAS = Path(__file__).resolve().parent.parent
REG = CONAS / "data" / "conas-materials.ndjson"
SCHEMA = CONAS / "schemas" / "conas-materials.json"

MATERIALS = [
    {
        "id": "ag-silver",
        "name": "Silver (mating-area plating)",
        "category": "plating",
        "standardRef": "ASTM-B700",
        "description": "Highest-conductivity plating in common connector use (108% IACS), "
                       "chosen for high-current and RF contacts. Hardness is annealed fine "
                       "silver; hard-bright deposits are considerably harder and the "
                       "deposit temper is not stated by a part number. Source: CRC/ASM "
                       "room-temperature metal property tables.",
        "electrical": {
            "electricalConductivity": 63000000.0,
            "temperatureCoefficientOfResistance": 0.0038,
        },
        "thermal": {
            "thermalConductivity": 429,
            "specificHeat": 235,
            "coefficientOfThermalExpansion": 1.89e-05,
            "emissivity": 0.02,
            "meltingTemperature": 962,
        },
        "mechanical": {
            "density": 10490,
            "hardnessVickers": 25,
        },
    },
    {
        "id": "peek",
        "name": "PEEK (polyetheretherketone, unfilled)",
        "category": "dielectric",
        "description": "High-temperature semi-crystalline thermoplastic used for "
                       "reflow- and autoclave-surviving connector insulators. Source: "
                       "Professional Plastics, 'Electrical Properties of Plastic "
                       "Materials' (Dk @ 1 MHz, dielectric strength V/mil, volume "
                       "resistivity Ohm-cm converted to Ohm-m); Tg/Tm per Victrex 450G.",
        "electrical": {
            "relativePermittivity": 3.2,
            "dielectricStrength": 18900000.0,
            "lossTangent": 0.003,
            "characterizationFrequency": 1000000.0,
            "volumeResistivity": 490000000000000.0,
        },
        "thermal": {
            "glassTransitionTemperature": 143,
            "meltingTemperature": 343,
            "maxOperatingTemperature": 250,
        },
        "mechanical": {
            "density": 1320,
        },
        "environmental": {
            "ul94Rating": "V-0",
        },
    },
    {
        "id": "cuniSn-spinodal",
        "name": "Spinodal Cu-15Ni-8Sn (C72900, high-strength contact spring)",
        "category": "conductor",
        "standardRef": "UNS-C72900",
        "description": "Spinodally hardened copper-nickel-tin, the beryllium-free "
                       "high-cycle contact spring alloy (Materion ToughMet 3). Sullins "
                       "names only 'Spinodal', so the temper is unknown: yield, tensile "
                       "and hardness vary about 2x between the TS95 and TS160 tempers and "
                       "are omitted rather than pinned to one. Conductivity 11% IACS. "
                       "Source: Materion ToughMet 3 alloy datasheet.",
        "electrical": {
            "electricalConductivity": 6380000.0,
        },
        "thermal": {
            "thermalConductivity": 40,
        },
        "mechanical": {
            "density": 8940,
            "youngsModulus": 131000000000.0,
        },
    },
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012

    by_id = {}
    for repo in ("PEAS", "CONAS"):
        d = CONAS.parent / repo / "schemas"
        for p in d.rglob("*.json"):
            try:
                s = json.loads(p.read_text())
            except json.JSONDecodeError:
                continue
            if s.get("$id"):
                by_id[s["$id"]] = s
    reg = Registry().with_resources(
        [(k, Resource(contents=s, specification=DRAFT202012)) for k, s in by_id.items()])
    v = Draft202012Validator(json.loads(SCHEMA.read_text()), registry=reg)

    existing = {json.loads(l)["id"] for l in REG.read_text(encoding="utf-8").splitlines()
                if l.strip()}
    add, dupe, bad = [], [], []
    for m in MATERIALS:
        errs = sorted(v.iter_errors(m), key=lambda e: e.path)
        if errs:
            bad.append(f"{m['id']}: {errs[0].message[:140]}")
            continue
        if m["id"] in existing:
            dupe.append(m["id"])
            continue
        add.append(m)

    print(f"registry has     : {len(existing)}")
    print(f"valid and new    : {len(add)}")
    print(f"already present  : {len(dupe)} {dupe}")
    print(f"INVALID          : {len(bad)}")
    for b in bad:
        print("   ", b)
    for m in add:
        print(f"   + {m['id']:<20} {m['category']:<11} {m['name']}")
    if bad:
        return 1
    if not a.apply:
        print("\nDRY RUN — pass --apply to write")
        return 0
    with REG.open("a", encoding="utf-8") as fh:
        for m in add:
            fh.write(json.dumps(m, ensure_ascii=False) + "\n")
    print(f"\nappended {len(add)} materials -> {REG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
