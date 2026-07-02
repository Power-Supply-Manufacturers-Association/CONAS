#!/usr/bin/env python3
"""Validate CONAS schemas + example against the PSMA cross-repo registry.

Three gates, all of which FAIL loudly (a gate that cannot run is an error, never a skip):
  1. every schema meta-validates and EVERY $ref in it resolves through the registry
  2. every example validates against CONAS.json
  3. citizenship: every example is also a valid PEAS document (connector branch)
"""
import json
import glob
import os
import sys
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PSMA = os.path.dirname(HERE)

# PEAS's oneOf reaches every family: all siblings must be in the registry or
# gate 3 cannot run (and failing to run is a FAILURE, not a skip).
REPOS = ("PEAS", "MAS", "CAS", "SAS", "RAS", "CTAS", "CONAS", "AAS", "TAS", "CIAS", "COAS")


def load_all():
    resources = []
    for repo in REPOS:
        for f in glob.glob(os.path.join(PSMA, repo, "schemas", "**", "*.json"), recursive=True):
            try:
                doc = json.load(open(f))
            except (json.JSONDecodeError, OSError):
                continue
            if "$id" in doc:
                resources.append((doc["$id"], Resource.from_contents(doc)))
    return Registry().with_resources(resources)


def iter_refs(node):
    if isinstance(node, dict):
        if "$ref" in node:
            yield node["$ref"]
        for v in node.values():
            yield from iter_refs(v)
    elif isinstance(node, list):
        for v in node:
            yield from iter_refs(v)


def main():
    registry = load_all()
    errors = 0

    # 1. every schema meta-validates and every $ref resolves (draft 2020-12 refs are
    #    lazy, so we walk and look each one up explicitly instead of trusting a no-op).
    for f in glob.glob(os.path.join(HERE, "schemas", "**", "*.json"), recursive=True):
        doc = json.load(open(f))
        Draft202012Validator.check_schema(doc)
        resolver = registry.resolver(base_uri=doc.get("$id", ""))
        bad = []
        for ref in iter_refs(doc):
            try:
                resolver.lookup(ref)
            except Exception as exc:
                bad.append((ref, exc))
        if bad:
            errors += len(bad)
            print(f"\nFAIL refs in {os.path.relpath(f, HERE)}:")
            for ref, exc in bad:
                print(f"    {ref} -> {exc}")
        else:
            print(f"  schema OK (meta + {sum(1 for _ in iter_refs(doc))} refs): {os.path.relpath(f, HERE)}")

    # 2. examples validate against CONAS.json
    conas = registry.get_or_retrieve("https://psma.com/conas/CONAS.json").value.contents
    validator = Draft202012Validator(conas, registry=registry)
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

    # 3. citizenship — a gate that cannot run is a FAILURE, not a skip.
    try:
        peas = registry.get_or_retrieve("https://psma.com/peas/peas.json").value.contents
        peas_validator = Draft202012Validator(peas, registry=registry)
    except Exception as exc:
        errors += 1
        print(f"\nFAIL: citizenship gate cannot run (PEAS not resolvable): {exc}")
    else:
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

    print("\n" + ("PASS" if errors == 0 else f"FAIL ({errors} errors)"))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
