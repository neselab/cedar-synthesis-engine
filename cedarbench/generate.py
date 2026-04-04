#!/usr/bin/env python3
"""
CedarBench — Mutation-based benchmark generator.

Discovers all registered mutations, applies them to base scenarios,
and writes output directories with schema + policy_spec for each.

Usage:
    python -m cedarbench.generate                     # Generate all
    python -m cedarbench.generate --domain github     # Single domain
    python -m cedarbench.generate --difficulty easy    # Filter by tier
    python -m cedarbench.generate --list               # List without generating
    python -m cedarbench.generate --output /path/to/dir
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure the repo root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cedarbench.base_scenarios import BASE_SCENARIOS, get_repo_root
from cedarbench.mutation import get_all_mutations, MutationMeta

# Import all domain modules to trigger registration
from cedarbench.mutations import (  # noqa: F401
    github, doccloud, streaming, clinical, hotel, tags, tax, sales,
)


DEFAULT_OUTPUT = "cedarbench/scenarios"


def generate_base_scenarios(repo_root: Path, output_dir: Path) -> list[dict]:
    """Copy base scenarios into the output as {domain}_base directories."""
    entries = []
    for key, base in BASE_SCENARIOS.items():
        scenario_id = f"{key}_base"
        scenario_dir = output_dir / scenario_id
        scenario_dir.mkdir(parents=True, exist_ok=True)

        # Write schema
        schema = base.load_schema(repo_root)
        (scenario_dir / "schema.cedarschema").write_text(schema)

        # Write policy spec if the experiment has one
        spec_path = repo_root / base.schema_path.parent / "policy_spec.md"
        if spec_path.exists():
            (scenario_dir / "policy_spec.md").write_text(spec_path.read_text())
        else:
            # For dataset scenarios, generate a minimal spec note
            (scenario_dir / "policy_spec.md").write_text(
                f"# {base.description}\n\n"
                f"See the ground-truth policy in `{base.policy_path}` for reference.\n"
            )

        entries.append({
            "id": scenario_id,
            "domain": key,
            "base_scenario": None,
            "difficulty": "base",
            "mutation_description": f"Unmodified {base.description}",
            "operators_applied": [],
            "features_tested": [],
            "path": f"scenarios/{scenario_id}/",
        })
    return entries


def generate_mutations(
    repo_root: Path,
    output_dir: Path,
    domain_filter: str | None = None,
    difficulty_filter: str | None = None,
) -> list[dict]:
    """Apply all registered mutations and write output directories."""
    mutations = get_all_mutations()
    entries = []
    errors = []

    for mutation_id, mutation in sorted(mutations.items()):
        meta = mutation.meta()

        # Apply filters
        if domain_filter and not mutation_id.startswith(domain_filter):
            continue
        if difficulty_filter and meta.difficulty != difficulty_filter:
            continue

        # Load base schema
        base = BASE_SCENARIOS.get(meta.base_scenario)
        if not base:
            errors.append(f"  {mutation_id}: unknown base_scenario '{meta.base_scenario}'")
            continue

        try:
            base_schema = base.load_schema(repo_root)
            result = mutation.apply(base_schema)
        except Exception as e:
            errors.append(f"  {mutation_id}: {e}")
            continue

        # Write output
        scenario_dir = output_dir / meta.id
        scenario_dir.mkdir(parents=True, exist_ok=True)
        (scenario_dir / "schema.cedarschema").write_text(result.schema)
        (scenario_dir / "policy_spec.md").write_text(result.policy_spec)

        entries.append({
            "id": meta.id,
            "domain": meta.base_scenario,
            "base_scenario": f"{meta.base_scenario}_base",
            "difficulty": meta.difficulty,
            "mutation_description": meta.description,
            "operators_applied": meta.operators,
            "features_tested": meta.features_tested,
            "path": f"scenarios/{meta.id}/",
        })

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(e)

    return entries


def write_manifest(output_dir: Path, entries: list[dict]) -> Path:
    """Write manifest.json with all scenario metadata."""
    manifest = {
        "version": "1.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_scenarios": len(entries),
        "by_difficulty": {},
        "by_domain": {},
        "scenarios": entries,
    }

    # Compute summary counts
    for e in entries:
        d = e["difficulty"]
        manifest["by_difficulty"][d] = manifest["by_difficulty"].get(d, 0) + 1
        dom = e["domain"]
        manifest["by_domain"][dom] = manifest["by_domain"].get(dom, 0) + 1

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest_path


def list_mutations():
    """Print all registered mutations without generating."""
    mutations = get_all_mutations()
    by_domain: dict[str, list[MutationMeta]] = {}

    for mutation in mutations.values():
        meta = mutation.meta()
        by_domain.setdefault(meta.base_scenario, []).append(meta)

    total = 0
    for domain in sorted(by_domain):
        muts = sorted(by_domain[domain], key=lambda m: (
            {"easy": 0, "medium": 1, "hard": 2}.get(m.difficulty, 3), m.id
        ))
        print(f"\n{domain} ({len(muts)} mutations):")
        for m in muts:
            print(f"  [{m.difficulty:<6}] {m.id}")
            print(f"           {m.description}")
        total += len(muts)

    print(f"\nTotal: {total} mutations + {len(BASE_SCENARIOS)} base scenarios = {total + len(BASE_SCENARIOS)} scenarios")


def main():
    parser = argparse.ArgumentParser(
        description="CedarBench mutation-based benchmark generator",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help=f"Output directory (default: <repo>/{DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--domain", type=str, default=None,
        help="Only generate mutations for this domain (e.g., github, clinical)",
    )
    parser.add_argument(
        "--difficulty", type=str, choices=["easy", "medium", "hard"],
        help="Only generate mutations of this difficulty tier",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List all mutations without generating",
    )
    parser.add_argument(
        "--no-base", action="store_true",
        help="Skip generating base (unmodified) scenarios",
    )
    args = parser.parse_args()

    if args.list:
        list_mutations()
        return

    repo_root = get_repo_root()
    output_dir = Path(args.output) if args.output else repo_root / DEFAULT_OUTPUT
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("CEDARBENCH — Mutation Generator")
    print("=" * 60)
    print(f"Repo root:  {repo_root}")
    print(f"Output:     {output_dir}")
    if args.domain:
        print(f"Domain:     {args.domain}")
    if args.difficulty:
        print(f"Difficulty: {args.difficulty}")

    all_entries = []

    # Base scenarios
    if not args.no_base and not args.domain and not args.difficulty:
        print(f"\n--- Base scenarios ({len(BASE_SCENARIOS)}) ---")
        base_entries = generate_base_scenarios(repo_root, output_dir)
        all_entries.extend(base_entries)
        print(f"  Generated {len(base_entries)} base scenarios")

    # Mutations
    print("\n--- Mutations ---")
    mut_entries = generate_mutations(
        repo_root, output_dir,
        domain_filter=args.domain,
        difficulty_filter=args.difficulty,
    )
    all_entries.extend(mut_entries)
    print(f"  Generated {len(mut_entries)} mutations")

    # Manifest
    manifest_path = write_manifest(output_dir, all_entries)

    # Summary
    by_diff = {}
    by_domain = {}
    for e in all_entries:
        by_diff[e["difficulty"]] = by_diff.get(e["difficulty"], 0) + 1
        by_domain[e["domain"]] = by_domain.get(e["domain"], 0) + 1

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total scenarios: {len(all_entries)}")
    print(f"\nBy difficulty:")
    for d in ["base", "easy", "medium", "hard"]:
        if d in by_diff:
            print(f"  {d:<8} {by_diff[d]}")
    print(f"\nBy domain:")
    for dom in sorted(by_domain):
        print(f"  {dom:<12} {by_domain[dom]}")
    print(f"\nManifest: {manifest_path}")


if __name__ == "__main__":
    main()
