"""Recompile the saved gold-reference cases using only their packaged inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from compiler import compile_spec, load_registry


ROOT = Path(__file__).resolve().parent
EXPECTED_FILES = {
    "requirement.md",
    "controlled-source.txt",
    "gold/spec.json",
    "gold/registry.json",
    "gold/gold.cedar",
    "gold/schema.cedarschema",
    "gold/predicate_ast.json",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def verify_case(case: Path) -> None:
    actual_files = {
        path.relative_to(case).as_posix()
        for path in case.rglob("*")
        if path.is_file()
    }
    if actual_files != EXPECTED_FILES:
        missing = sorted(EXPECTED_FILES - actual_files)
        extra = sorted(actual_files - EXPECTED_FILES)
        raise ValueError(f"{case.name}: missing files {missing}; extra files {extra}")

    gold = case / "gold"
    compiled = compile_spec(
        read_json(gold / "spec.json"), load_registry(gold / "registry.json")
    )
    expected = {
        "policy": (gold / "gold.cedar").read_text(),
        "schema": (gold / "schema.cedarschema").read_text(),
        "predicate_ast": read_json(gold / "predicate_ast.json"),
    }
    for output, saved in expected.items():
        if compiled[output] != saved:
            raise ValueError(f"{case.name}: compiled {output} differs from saved output")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", help="Verify one saved case, for example case-100")
    args = parser.parse_args()

    cases = sorted(path for path in (ROOT / "cases").iterdir() if path.is_dir())
    if len(cases) != 200:
        raise ValueError(f"Expected 200 case directories, found {len(cases)}")
    if args.case:
        cases = [path for path in cases if path.name == args.case]
        if not cases:
            parser.error(f"Unknown case: {args.case}")

    for case in cases:
        verify_case(case)
    print(
        f"Verified {len(cases)} case(s): gold policies, schemas, "
        "and predicate ASTs match."
    )


if __name__ == "__main__":
    main()
