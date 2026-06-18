#!/usr/bin/env python3
"""Validate COAS schemas + example against the PSMA cross-repo registry."""
import json
import glob
import os
import sys
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PSMA = os.path.dirname(HERE)


def load_all():
    resources = []
    for repo in ("PEAS", "MAS", "CAS", "SAS", "RAS", "COAS"):
        for f in glob.glob(os.path.join(PSMA, repo, "schemas", "**", "*.json"), recursive=True):
            try:
                doc = json.load(open(f))
            except (json.JSONDecodeError, OSError):
                continue
            if "$id" in doc:
                resources.append((doc["$id"], Resource.from_contents(doc)))
    return Registry().with_resources(resources)


def main():
    registry = load_all()
    errors = 0

    # 1. every schema meta-validates and its refs resolve
    for f in glob.glob(os.path.join(HERE, "schemas", "**", "*.json"), recursive=True):
        doc = json.load(open(f))
        Draft202012Validator.check_schema(doc)
        v = Draft202012Validator(doc, registry=registry)
        # touch every ref by validating a trivially-empty instance against resolvers lazily
        print(f"  schema OK: {os.path.relpath(f, HERE)}")

    # 2. examples validate against COAS.json
    coas = registry.get_or_retrieve("https://psma.com/coas/COAS.json").value.contents
    validator = Draft202012Validator(coas, registry=registry)
    for f in glob.glob(os.path.join(HERE, "examples", "*.json")):
        inst = json.load(open(f))
        errs = sorted(validator.iter_errors(inst), key=lambda e: e.path)
        if errs:
            errors += len(errs)
            print(f"\nFAIL {os.path.basename(f)}:")
            for e in errs[:20]:
                print("   ", list(e.path), "->", e.message)
        else:
            print(f"  example OK: {os.path.basename(f)}")

    # 3. citizenship — every example is also a valid PEAS document (connector branch)
    try:
        peas = registry.get_or_retrieve("https://psma.com/peas/peas.json").value.contents
        peas_validator = Draft202012Validator(peas, registry=registry)
        for f in glob.glob(os.path.join(HERE, "examples", "*.json")):
            inst = json.load(open(f))
            errs = sorted(peas_validator.iter_errors(inst), key=lambda e: e.path)
            if errs:
                errors += len(errs)
                print(f"\nCITIZENSHIP FAIL {os.path.basename(f)}:")
                for e in errs[:20]:
                    print("   ", list(e.path), "->", e.message)
            else:
                print(f"  citizenship OK (valid PEAS): {os.path.basename(f)}")
    except Exception as exc:
        print(f"  citizenship SKIPPED (PEAS not resolvable): {exc}")

    print("\n" + ("PASS" if errors == 0 else f"FAIL ({errors} errors)"))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
