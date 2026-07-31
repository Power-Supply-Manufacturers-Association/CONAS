#!/usr/bin/env python3
"""Extend the conas-materials registry with the materials real connectors are made of.

WHY: the registry defined 10 materials. Harvesting Würth's 5,135 connector datasheets
turned up 25 distinct housing materials and 13 contact metals, and only 13 of ~3,400 parts
carrying material data could store it — every other part named something the registry has
no id for. A material ref that does not resolve is worse than no ref, so the fix is to
define the materials, not to point at ids that do not exist.

SOURCING. Every number here comes from a cited published table, never from recall:

  Dielectrics — Professional Plastics, "Electrical Properties of Plastic Materials"
  (dielectric constant, dielectric strength in kV/mm, volume resistivity in Ohm-cm).
  One table for all of them, so the values are mutually consistent rather than stitched
  together from per-material pages using different test standards.
  Volume resistivity is converted Ohm-cm -> Ohm-m (x0.01) for SI.

  LCP — Celanese Vectra glass-reinforced grade, dielectric strength per IEC 60243-1.
  Not in the Professional Plastics table.

  Phosphor bronze — MakeItFrom UNS C51000. Its 18% IACS and 77 W/m-K are mutually
  consistent (Wiedemann-Franz gives ~18.6% IACS from 77 W/m-K); other datasheets quote
  15% IACS for softer tempers, which is recorded in the description rather than averaged.

DELIBERATELY NOT ADDED:
  - "Copper Alloy" (1,746 Würth parts). Not a material — WE does not say which alloy, and
    conductivity is the defining property of a conductor entry. Inventing one would put a
    number on a part nobody specified.
  - PA9T / PA6T / PA4T (695 parts). Semi-aromatic polyamides whose electrical properties
    I could not find in a citable table. They need a manufacturer datasheet (Kuraray
    Genestar, DSM ForTii) before they can be defined.

  add_materials_2026_07.py [--apply]
"""
import argparse
import json
import sys
from pathlib import Path

CONAS = Path(__file__).resolve().parent.parent
REG = CONAS / "data" / "conas-materials.ndjson"

PP = ("Professional Plastics, 'Electrical Properties of Plastic Materials' "
      "(dielectric constant @1MHz unless noted, dielectric strength kV/mm, "
      "volume resistivity Ohm-cm)")

MATERIALS = [
    {
        "id": "ptfe",
        "name": "PTFE (polytetrafluoroethylene, unfilled)",
        "category": "dielectric",
        "description": (
            "Coaxial/RF connector insulator. Dielectric strength is quoted as a 50-170 "
            "kV/mm range because breakdown scales with specimen thickness; the low end is "
            "recorded here as the conservative bulk figure. Source: " + PP),
        "electrical": {
            "relativePermittivity": 2.05,
            "dielectricStrength": 50e6,
            "lossTangent": 0.0005,
            "characterizationFrequency": 1e6,
            "volumeResistivity": 1e16,
        },
        "thermal": {"thermalConductivity": 0.25, "meltingTemperature": 327},
        "mechanical": {"density": 2200},
    },
    {
        "id": "pbt",
        "name": "PBT (polybutylene terephthalate)",
        "category": "dielectric",
        "description": "Common connector housing thermoplastic. Dk quoted @1kHz. Source: " + PP,
        "electrical": {
            "relativePermittivity": 3.2,
            "dielectricStrength": 20e6,
            "lossTangent": 0.002,
            "characterizationFrequency": 1e3,
            "volumeResistivity": 1e13,
        },
        "thermal": {"meltingTemperature": 225},
        "mechanical": {"density": 1310},
    },
    {
        "id": "pet-polyester",
        "name": "PET (polyethylene terephthalate, polyester)",
        "category": "dielectric",
        "description": "Source: " + PP,
        "electrical": {
            "relativePermittivity": 3.0,
            "dielectricStrength": 17e6,
            "lossTangent": 0.002,
            "characterizationFrequency": 1e6,
            "volumeResistivity": 1e12,
        },
        "thermal": {"meltingTemperature": 250},
        "mechanical": {"density": 1380},
    },
    {
        "id": "pvc-rigid",
        "name": "PVC-U (unplasticized polyvinyl chloride)",
        "category": "dielectric",
        "description": "Dk range 2.7-3.1; midpoint recorded. Source: " + PP,
        "electrical": {
            "relativePermittivity": 2.9,
            "dielectricStrength": 14e6,
            "lossTangent": 0.025,
            "characterizationFrequency": 1e3,
            "volumeResistivity": 1e14,
        },
        "mechanical": {"density": 1400},
    },
    {
        "id": "pc-polycarbonate",
        "name": "PC (polycarbonate)",
        "category": "dielectric",
        "description": (
            "Dielectric strength published as 15-67 kV/mm (thickness dependent); the "
            "conservative bulk figure is recorded. Source: " + PP),
        "electrical": {
            "relativePermittivity": 2.9,
            "dielectricStrength": 15e6,
            "lossTangent": 0.01,
            "characterizationFrequency": 1e6,
            "volumeResistivity": 1e12,
        },
        "thermal": {"thermalConductivity": 0.2},
        "mechanical": {"density": 1200},
    },
    {
        "id": "pps-gf40",
        "name": "PPS GF40 (polyphenylene sulfide, 40% glass fibre)",
        "category": "dielectric",
        "description": "Dk range 3.8-4.2; midpoint recorded. Source: " + PP,
        "electrical": {
            "relativePermittivity": 4.0,
            "dielectricStrength": 18e6,
            "lossTangent": 0.0025,
            "characterizationFrequency": 1e6,
            "volumeResistivity": 1e14,
        },
        "thermal": {"meltingTemperature": 280},
        "mechanical": {"density": 1650},
    },
    {
        "id": "lcp",
        "name": "LCP (liquid crystal polymer, glass reinforced)",
        "category": "dielectric",
        "standardRef": "IEC-60243-1",
        "description": (
            "High-temperature connector housing for SMT reflow. Source: Celanese Vectra "
            "LCP glass-reinforced grade; dielectric strength per IEC 60243-1."),
        "electrical": {
            "relativePermittivity": 3.7,
            "dielectricStrength": 34e6,
            "lossTangent": 0.018,
            "characterizationFrequency": 1e6,
        },
        "thermal": {"meltingTemperature": 280},
        "mechanical": {"density": 1600},
    },
    {
        "id": "ppa-pa6t-gf",
        "name": "PPA / PA6T (polyphthalamide, glass reinforced)",
        "category": "dielectric",
        "standardRef": "ASTM-D149",
        "description": (
            "High-temperature semi-aromatic polyamide used for SMT-reflow connector "
            "housings; WE labels it 'PA6T'. Source: Solvay Amodel AS-1145 HS technical "
            "data sheet (dry): dielectric constant 4.40 @1 MHz and 4.60 @60 Hz per ASTM "
            "D150, dielectric strength 22 kV/mm per ASTM D149, volume resistivity "
            "1.0e16 Ohm-cm per ASTM D257, CTI 550 V per UL 746A."),
        "electrical": {
            "relativePermittivity": 4.40,
            "dielectricStrength": 22e6,
            "lossTangent": 0.016,
            "characterizationFrequency": 1e6,
            "volumeResistivity": 1e14,
        },
        "thermal": {"meltingTemperature": 312},
    },
    {
        "id": "pa9t",
        "name": "PA9T (polyamide 9T, semi-aromatic, glass reinforced)",
        "category": "dielectric",
        "standardRef": "IEC-60243-1",
        "description": (
            "Kuraray GENESTAR. The dominant Würth connector housing polymer (450 parts). "
            "Source: Material Data Center datasheet GENESTAR GN2330-1 — dielectric "
            "strength 30 kV/mm per IEC 60243-1 (and ASTM D149), volume resistivity "
            ">1e15 Ohm-cm per ASTM D257, density 1620 kg/m3 per ASTM D792, melting 306 C "
            "per ISO 11357. RELATIVE PERMITTIVITY IS DELIBERATELY ABSENT: Kuraray does "
            "not publish it in any freely available source (Material Data Center, "
            "SpecialChem, their own PA9T catalogue and the CAMPUS public page were all "
            "checked, and the datasheet was queried directly for permittivity under IEC "
            "62631-2-1). It is NOT estimated from PA6T or from PPA generally — PA9T is a "
            "C9 diamine and PA6T a C6, and their measured strengths already differ "
            "(30 vs 22 kV/mm). Add the figure if Kuraray ever publishes it."),
        "electrical": {
            "dielectricStrength": 30e6,
            "volumeResistivity": 1e13,
        },
        "thermal": {"meltingTemperature": 306},
        "mechanical": {"density": 1620},
    },
    {
        "id": "pa4t",
        "name": "PA4T (polyamide 4T, semi-aromatic PPA, glass reinforced)",
        "category": "dielectric",
        "standardRef": "IEC-60243-1",
        "description": (
            "Envalior ForTii F11 (PA4T, 30% glass), as-molded. The best-documented entry "
            "in this registry: dielectric strength 33 kV/mm per IEC 60243-1, relative "
            "permittivity 4.2 @100 Hz / 3.9 @1 MHz / 3.8 @1 GHz per IEC 62631-2-1, volume "
            "resistivity >1e13 Ohm-m per IEC 62631-3-1, CTI >=800 V per IEC 60112, "
            "density 1460 kg/m3 per ISO 1183, melting 325 C per ISO 11357."),
        "electrical": {
            "relativePermittivity": 3.9,
            "dielectricStrength": 33e6,
            "characterizationFrequency": 1e6,
            "volumeResistivity": 1e13,
        },
        "thermal": {"meltingTemperature": 325},
        "mechanical": {"density": 1460},
    },
    {
        "id": "pa46",
        "name": "PA46 (polyamide 4,6)",
        "category": "dielectric",
        "standardRef": "IEC-60243-1",
        "description": (
            "DSM/Envalior Stanyl TW341-N, DRY (as-molded). Dielectric strength 25 kV/mm "
            "per IEC 60243-1, volume resistivity 1e15 Ohm-cm per IEC 60093, CTI 400 V per "
            "IEC 60112, density 1180 kg/m3 per ISO 1183, melting 295 C per ISO 11357. "
            "Polyamides absorb moisture and the conditioned figures are materially lower "
            "(15 kV/mm, 1e9 Ohm-cm); the dry values are recorded to stay consistent with "
            "the other polyamide entries here, and the conditioned pair is noted so the "
            "difference is not mistaken for a discrepancy. No permittivity published."),
        "electrical": {
            "dielectricStrength": 25e6,
            "volumeResistivity": 1e13,
        },
        "thermal": {"meltingTemperature": 295},
        "mechanical": {"density": 1180},
    },
    {
        "id": "abs",
        "name": "ABS (acrylonitrile butadiene styrene)",
        "category": "dielectric",
        "description": (
            "Dk published as 3.2-3.3 and strength as 20-25 kV/mm; the midpoint Dk and the "
            "conservative strength are stored. Source: " + PP),
        "electrical": {
            "relativePermittivity": 3.25,
            "dielectricStrength": 20e6,
            "lossTangent": 0.02,
            "characterizationFrequency": 1e6,
            "volumeResistivity": 1e13,
        },
        "mechanical": {"density": 1050},
    },
    {
        "id": "pom-acetal",
        "name": "POM (acetal homopolymer)",
        "category": "dielectric",
        "description": "Source: " + PP,
        "electrical": {
            "relativePermittivity": 3.7,
            "dielectricStrength": 20e6,
            "lossTangent": 0.005,
            "characterizationFrequency": 1e6,
            "volumeResistivity": 1e13,
        },
        "mechanical": {"density": 1410},
    },
    {
        "id": "cusnp-phosphorBronze",
        "name": "Phosphor bronze C51000 (CuSn5P, contact spring)",
        "category": "conductor",
        "standardRef": "UNS-C51000",
        "description": (
            "The default connector contact spring alloy. 18% IACS = 1.044e7 S/m, "
            "internally consistent with the 77 W/m-K thermal conductivity recorded here "
            "(Wiedemann-Franz implies ~18.6% IACS). Softer tempers are published at 15% "
            "IACS (~8.7e6 S/m). Source: MakeItFrom UNS C51000 (CW451K)."),
        "electrical": {"electricalConductivity": 1.044e7},
        "thermal": {"thermalConductivity": 77, "meltingTemperature": 960},
        "mechanical": {"density": 8800, "youngsModulus": 110e9},
    },
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    from jsonschema import Draft202012Validator
    schema = json.loads((CONAS / "schemas" / "conas-materials.json").read_text())
    v = Draft202012Validator(schema)

    existing = {}
    for ln in REG.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            o = json.loads(ln)
            existing[o["id"]] = o
    print(f"registry currently holds {len(existing)} materials")

    add, bad, dupe = [], [], []
    for m in MATERIALS:
        errs = sorted(v.iter_errors(m), key=lambda e: e.path)
        if errs:
            bad.append(f"{m['id']}: {errs[0].message[:140]}")
            continue
        if m["id"] in existing:
            dupe.append(m["id"])
            continue
        add.append(m)

    print(f"valid and new : {len(add)}")
    print(f"already present: {len(dupe)} {dupe}")
    print(f"INVALID        : {len(bad)}")
    for b in bad:
        print("   ", b)
    for m in add:
        print(f"   + {m['id']:<24} {m['category']:<11} {m['name']}")
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
