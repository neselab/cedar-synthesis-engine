#!/usr/bin/env python3
"""Run CedarBench layer ablations on a CedarBench scenario slice.

The experiment reuses the same authoritative Stage 3 harness path as the main
AutoCedar run. The default modes form a clean layer ladder:

1. schema only
2. schema + formal target, one shot
3. native Cedar/SymCC verifier feedback loop
4. full AutoCedar signal layer
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autocedar.harness.eval_harness import run_scenario  # noqa: E402

DEFAULT_FULL_RUN = (
    ROOT
    / "experiments"
    / "cedarbench_aitl_fast"
    / "cedarbench-aitl-fast-gpt55-low-20260630"
    / "scenario_results.jsonl"
)

ABLATION_MODES = [
    "schema_only",
    "formal_target_one_shot",
    "native_verifier_cegis",
    "full",
]

PAPER_LABELS = {
    "schema_only": "Schema only",
    "formal_target_one_shot": "Schema + property atoms, one-shot",
    "native_verifier_cegis": "Native Cedar/SymCC verifier feedback loop",
    "full": "Full AutoCedar signal stack",
    "no_structured_signal": "Native Cedar/SymCC verifier signal only",
    "no_direction": "No explicit floor/ceiling/liveness direction",
    "no_witness": "No witness/localization augmentation",
    "no_oscillation": "No temporal oscillation memory",
    "one_shot_same_target": "One-shot from same formal target",
}

HARD_ANCHORS = [
    "cedarbench/scenarios/realworld/decoy_trivial_properties",
    "cedarbench/scenarios/realworld/grace_period_three_tier",
    "cedarbench/scenarios/realworld/if_then_else_decision_tree",
    "cedarbench/scenarios/tags_remove_all_wildcard",
    "cedarbench/scenarios/tags_add_owner_bypass",
    "cedarbench/scenarios/tags_add_sensitivity",
    "cedarbench/scenarios/tags_sensitivity_and_owner",
]


class ScenarioTimeout(TimeoutError):
    pass


def _timeout_handler(signum, frame):  # noqa: ANN001
    raise ScenarioTimeout("scenario exceeded timeout")


def _scenario_paths() -> list[Path]:
    return sorted(p.parent for p in (ROOT / "cedarbench" / "scenarios").rglob("policy_spec.md"))


def _bucket(path: Path) -> str:
    rel = path.relative_to(ROOT / "cedarbench" / "scenarios")
    if len(rel.parts) > 1:
        return rel.parts[0]
    return path.name.split("_", 1)[0]


def _select_stratified(paths: list[Path], n: int) -> list[Path]:
    """Deterministically choose a proportional, category-stratified slice."""
    if n <= 0:
        return []
    if n >= len(paths):
        return list(paths)
    by_bucket: dict[str, list[Path]] = defaultdict(list)
    for path in paths:
        by_bucket[_bucket(path)].append(path)
    total = len(paths)
    quotas: dict[str, int] = {}
    remainders: list[tuple[float, str]] = []
    for bucket, items in by_bucket.items():
        exact = n * len(items) / total
        base = int(exact)
        if n >= len(by_bucket) and items and base == 0:
            base = 1
        quotas[bucket] = min(base, len(items))
        remainders.append((exact - int(exact), bucket))

    while sum(quotas.values()) < n:
        for _, bucket in sorted(remainders, reverse=True):
            if quotas[bucket] < len(by_bucket[bucket]):
                quotas[bucket] += 1
                break
        else:
            break
    while sum(quotas.values()) > n:
        for _, bucket in sorted(remainders):
            if quotas[bucket] > 1:
                quotas[bucket] -= 1
                break
        else:
            break

    selected: list[Path] = []
    for bucket in sorted(by_bucket):
        items = by_bucket[bucket]
        k = quotas[bucket]
        if k >= len(items):
            selected.extend(items)
            continue
        # Evenly spaced deterministic sample inside each bucket.
        if k == 1:
            idxs = [len(items) // 2]
        else:
            idxs = [round(i * (len(items) - 1) / (k - 1)) for i in range(k)]
        selected.extend(items[i] for i in idxs)
    return sorted(dict.fromkeys(selected))


def _select_hard(paths: list[Path], n: int, full_rows_path: Path) -> list[Path]:
    """Choose a deterministic hard/adversarial slice for signal ablations.

    The score intentionally uses observable benchmark structure rather than
    outcome labels from any ablated run: high check count, prior full-run repair
    iterations, known AutoCedar stress anchors, realworld placement, and names
    that mark planner traps, precedence, role intersections,
    temporal/lifecycle boundaries, scale, or adversarial cases.
    """
    row_index = _full_row_index(full_rows_path)
    by_rel = {str(path.relative_to(ROOT)): path for path in paths}
    anchors = [by_rel[rel] for rel in HARD_ANCHORS if rel in by_rel]
    hard_terms = {
        "adversarial": 35,
        "oscillation": 35,
        "trap": 32,
        "contradiction": 30,
        "ambiguous": 28,
        "ambiguity": 28,
        "counterintuitive": 26,
        "hidden": 24,
        "decoy": 24,
        "red_herring": 24,
        "priority": 24,
        "override": 22,
        "exception": 22,
        "conflicting": 22,
        "conflict": 22,
        "forbid": 20,
        "revocation": 20,
        "delegation": 20,
        "role": 20,
        "intersection": 20,
        "separation": 20,
        "sod": 20,
        "temporal": 18,
        "expiry": 18,
        "grace": 18,
        "cascading": 18,
        "recurring": 18,
        "rolling": 18,
        "quiescence": 18,
        "optional": 16,
        "hierarchy": 16,
        "multi": 14,
        "compound": 14,
        "quorum": 14,
        "attestation": 14,
        "mega": 14,
        "hundred": 14,
        "fifty": 14,
        "twenty": 14,
        "fifteen": 14,
        "ten_level": 14,
        "wide": 12,
        "scale": 12,
        "if_then_else": 12,
        "wildcard": 12,
        "bypass": 12,
    }

    scored: list[tuple[float, str, Path]] = []
    for path in paths:
        rel = str(path.relative_to(ROOT))
        row = row_index.get(rel, {})
        name = "/".join(path.relative_to(ROOT / "cedarbench" / "scenarios").parts)
        score = 0.0
        if _bucket(path) == "realworld":
            score += 45
        if row.get("final_artifact_repaired"):
            score += 80
        if row.get("converged") is False:
            score += 80
        score += float(row.get("checks_total") or 0) * 0.7
        score += max(float(row.get("iterations") or 1) - 1, 0) * 18
        for term, weight in hard_terms.items():
            if term in name:
                score += weight
        scored.append((score, rel, path))

    selected = list(anchors[:n])
    seen = {str(path.relative_to(ROOT)) for path in selected}
    if len(selected) >= n:
        return sorted(selected)
    for _, _, path in sorted(scored, reverse=True):
        rel = str(path.relative_to(ROOT))
        if rel in seen:
            continue
        selected.append(path)
        seen.add(rel)
        if len(selected) >= n:
            break
    return sorted(selected)


def _load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _completed(results_path: Path) -> set[tuple[str, str]]:
    done: set[tuple[str, str]] = set()
    for row in _load_rows(results_path):
        mode = row.get("ablation_mode")
        scenario_path = row.get("scenario_path")
        if isinstance(mode, str) and isinstance(scenario_path, str):
            done.add((mode, scenario_path))
    return done


def _full_row_index(path: Path) -> dict[str, dict]:
    return {
        row["scenario_path"]: row
        for row in _load_rows(path)
        if isinstance(row.get("scenario_path"), str)
    }


def _write_summary(out_root: Path, results_path: Path) -> None:
    rows = _load_rows(results_path)
    by_mode: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_mode[str(row.get("ablation_mode", "unknown"))].append(row)

    summary = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_rows": len(rows),
        "modes": {},
    }
    for mode in sorted(by_mode):
        mode_rows = by_mode[mode]
        summary["modes"][mode] = {
            "label": PAPER_LABELS.get(mode, mode),
            "completed": len(mode_rows),
            "converged": sum(1 for r in mode_rows if r.get("converged")),
            "failed_or_incomplete": sum(1 for r in mode_rows if not r.get("converged")),
            "total_time_s": round(sum(float(r.get("total_time_s") or 0) for r in mode_rows), 2),
            "total_tokens": sum(int(r.get("total_tokens") or 0) for r in mode_rows),
            "estimated_cost_usd": round(sum(float(r.get("estimated_cost_usd") or 0) for r in mode_rows), 6),
            "mean_iterations": round(
                sum(float(r.get("iterations") or 0) for r in mode_rows) / max(len(mode_rows), 1),
                3,
            ),
            "mean_final_loss": round(
                sum(float(r.get("final_loss") or 0) for r in mode_rows) / max(len(mode_rows), 1),
                3,
            ),
        }

    (out_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    lines = [
        "# CedarBench AutoCedar Layer Ablation",
        "",
        f"Updated: `{summary['updated_at']}`",
        f"Rows: `{summary['total_rows']}`",
        "",
        "| Mode | Completed | Converged | Failed | Time (s) | Tokens | Cost | Mean iters | Mean loss |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for mode, data in summary["modes"].items():
        lines.append(
            f"| {data['label']} (`{mode}`) | {data['completed']} | {data['converged']} | "
            f"{data['failed_or_incomplete']} | {data['total_time_s']} | "
            f"{data['total_tokens']} | ${data['estimated_cost_usd']} | "
            f"{data['mean_iterations']} | {data['mean_final_loss']} |"
        )
    lines.append("")
    lines.append(
        "`Schema only` exposes only the approved Cedar schema and prose spec. "
        "`Schema + property atoms, one-shot` also exposes the approved formal "
        "target but gives no repair loop. `Native Cedar/SymCC verifier feedback "
        "loop` keeps CEGIS repair with native verifier output. `Full AutoCedar "
        "signal stack` adds AutoCedar's repair-oriented signal shaping over the "
        "same Cedar validator and SymCC oracle."
    )
    (out_root / "SUMMARY.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("signal-ablation-%Y%m%dT%H%M%SZ"))
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--effort", default="low", choices=["low", "medium", "high", "max"])
    parser.add_argument("--max-iters", type=int, default=20)
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--selection", choices=["stratified", "hard"], default="stratified")
    parser.add_argument("--modes", nargs="+", default=ABLATION_MODES, choices=ABLATION_MODES)
    parser.add_argument("--reuse-full-from", type=Path, default=DEFAULT_FULL_RUN)
    parser.add_argument(
        "--scenario-timeout-s",
        type=int,
        default=480,
        help="Wall-clock timeout per scenario/mode row. 0 disables.",
    )
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    os.environ["AUTOCEDAR_PROVIDER"] = "codex"
    os.environ["AUTOCEDAR_HARNESS_EFFORT"] = args.effort

    out_root = ROOT / "experiments" / "cedarbench_signal_ablation" / args.run_id
    out_root.mkdir(parents=True, exist_ok=True)
    results_path = out_root / "scenario_results.jsonl"
    selected_path = out_root / "selected_scenarios.json"
    workspaces = out_root / "workspaces"
    workspaces.mkdir(parents=True, exist_ok=True)

    all_scenarios = _scenario_paths()
    if args.selection == "hard":
        selected = _select_hard(all_scenarios, args.sample_size, args.reuse_full_from)
    else:
        selected = _select_stratified(all_scenarios, args.sample_size)
    selected_rels = [str(p.relative_to(ROOT)) for p in selected]
    selected_path.write_text(json.dumps(selected_rels, indent=2) + "\n")

    manifest = {
        "run_id": args.run_id,
        "model": args.model,
        "effort": args.effort,
        "sample_size": len(selected),
        "selection": args.selection,
        "max_iters": args.max_iters,
        "modes": args.modes,
        "reuse_full_from": str(args.reuse_full_from),
        "scenario_timeout_s": args.scenario_timeout_s,
        "bucket_counts": dict(Counter(_bucket(p) for p in selected)),
    }
    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2), flush=True)

    done = _completed(results_path) if args.resume else set()
    full_rows = _full_row_index(args.reuse_full_from) if "full" in args.modes else {}

    original_mode = os.environ.get("AUTOCEDAR_ABLATION_MODE")
    original_prompt_mode = os.environ.get("AUTOCEDAR_PROMPT_MODE")
    try:
        with results_path.open("a") as out:
            for mode in args.modes:
                mode_workspace_root = workspaces / mode
                mode_workspace_root.mkdir(parents=True, exist_ok=True)
                for idx, scenario in enumerate(selected, 1):
                    rel = str(scenario.relative_to(ROOT))
                    if (mode, rel) in done:
                        print(f"[{mode} {idx}/{len(selected)}] SKIP {rel}", flush=True)
                        continue

                    if mode == "full" and rel in full_rows:
                        row = dict(full_rows[rel])
                        row["ablation_mode"] = mode
                        row["ablation_label"] = PAPER_LABELS.get(mode, mode)
                        row["reused_from"] = str(args.reuse_full_from)
                        out.write(json.dumps(row) + "\n")
                        out.flush()
                        _write_summary(out_root, results_path)
                        print(f"[{mode} {idx}/{len(selected)}] REUSE {rel}", flush=True)
                        continue

                    if mode == "schema_only":
                        os.environ["AUTOCEDAR_PROMPT_MODE"] = "schema_only"
                        os.environ["AUTOCEDAR_ABLATION_MODE"] = "full"
                        effective_max_iters = 1
                    elif mode == "formal_target_one_shot":
                        os.environ["AUTOCEDAR_PROMPT_MODE"] = "formal_target"
                        os.environ["AUTOCEDAR_ABLATION_MODE"] = "full"
                        effective_max_iters = 1
                    elif mode == "native_verifier_cegis":
                        os.environ["AUTOCEDAR_PROMPT_MODE"] = "formal_target"
                        os.environ["AUTOCEDAR_ABLATION_MODE"] = "no_structured_signal"
                        effective_max_iters = args.max_iters
                    else:
                        os.environ["AUTOCEDAR_PROMPT_MODE"] = "formal_target"
                        os.environ["AUTOCEDAR_ABLATION_MODE"] = mode
                        effective_max_iters = args.max_iters
                    print(f"[{mode} {idx}/{len(selected)}] RUN  {rel}", flush=True)
                    t0 = time.monotonic()
                    previous_handler = signal.getsignal(signal.SIGALRM)
                    try:
                        if args.scenario_timeout_s > 0:
                            signal.signal(signal.SIGALRM, _timeout_handler)
                            signal.alarm(args.scenario_timeout_s)
                        result = run_scenario(
                            scenario_path=str(scenario),
                            run_dir=str(mode_workspace_root),
                            phase1_model=args.model,
                            phase2_model=args.model,
                            max_iters=effective_max_iters,
                            gen_references=False,
                            no_review=True,
                        )
                        row = asdict(result)
                    except ScenarioTimeout as exc:
                        row = {
                            "scenario": scenario.name,
                            "model": args.model,
                            "phase1_model": args.model,
                            "phase2_model": args.model,
                            "converged": False,
                            "iterations": effective_max_iters,
                            "max_iterations": effective_max_iters,
                            "total_time_s": round(time.monotonic() - t0, 2),
                            "phase1_time_s": 0.0,
                            "phase2_time_s": round(time.monotonic() - t0, 2),
                            "final_loss": -1,
                            "checks_total": 0,
                            "iteration_log": [],
                            "error": f"scenario timeout after {args.scenario_timeout_s}s: {exc}",
                            "phase1_input_tokens": 0,
                            "phase1_output_tokens": 0,
                            "phase2_input_tokens": 0,
                            "phase2_output_tokens": 0,
                            "total_input_tokens": 0,
                            "total_output_tokens": 0,
                            "total_tokens": 0,
                            "estimated_cost_usd": 0.0,
                        }
                        print(
                            f"[{mode} {idx}/{len(selected)}] TIMEOUT {rel} "
                            f"after {args.scenario_timeout_s}s",
                            flush=True,
                        )
                    finally:
                        if args.scenario_timeout_s > 0:
                            signal.alarm(0)
                            signal.signal(signal.SIGALRM, previous_handler)
                    row["ablation_mode"] = mode
                    row["ablation_label"] = PAPER_LABELS.get(mode, mode)
                    row["scenario_path"] = rel
                    out.write(json.dumps(row) + "\n")
                    out.flush()
                    _write_summary(out_root, results_path)
                    status = "PASS" if row.get("converged") else "FAIL"
                    print(
                        f"[{mode} {idx}/{len(selected)}] {status} {rel} "
                        f"iters={row.get('iterations')} loss={row.get('final_loss')} "
                        f"time={row.get('total_time_s')}s",
                        flush=True,
                    )
    finally:
        if original_mode is None:
            os.environ.pop("AUTOCEDAR_ABLATION_MODE", None)
        else:
            os.environ["AUTOCEDAR_ABLATION_MODE"] = original_mode
        if original_prompt_mode is None:
            os.environ.pop("AUTOCEDAR_PROMPT_MODE", None)
        else:
            os.environ["AUTOCEDAR_PROMPT_MODE"] = original_prompt_mode

    _write_summary(out_root, results_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
