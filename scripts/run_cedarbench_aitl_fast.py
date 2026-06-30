#!/usr/bin/env python3
"""Run CedarBench through the fast AutoCedar-AITL evaluation path.

This driver intentionally does not regenerate Phase 1 with an API planner.
It treats each CedarBench scenario's checked-in schema, verification plan, and
reference policies as the expert/AITL formal target, then runs the verifier-
guided synthesis loop with the requested model. Results are checkpointed after
each scenario so long benchmark runs can be resumed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autocedar.harness.eval_harness import run_scenario  # noqa: E402


def _scenario_paths() -> list[Path]:
    return sorted(p.parent for p in (ROOT / "cedarbench" / "scenarios").rglob("policy_spec.md"))


def _load_completed(results_path: Path) -> set[str]:
    completed: set[str] = set()
    if not results_path.exists():
        return completed
    for line in results_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        scenario_path = item.get("scenario_path")
        if isinstance(scenario_path, str):
            completed.add(scenario_path)
    return completed


def _write_summary(results_path: Path, summary_json: Path, summary_md: Path) -> None:
    rows: list[dict] = []
    if results_path.exists():
        for line in results_path.read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
    converged = [r for r in rows if r.get("converged")]
    failed = [r for r in rows if not r.get("converged")]
    summary = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_completed": len(rows),
        "converged": len(converged),
        "failed_or_incomplete": len(failed),
        "total_time_s": round(sum(float(r.get("total_time_s") or 0) for r in rows), 2),
        "total_tokens": sum(int(r.get("total_tokens") or 0) for r in rows),
        "estimated_cost_usd": round(sum(float(r.get("estimated_cost_usd") or 0) for r in rows), 6),
        "failures": [
            {
                "scenario": r.get("scenario"),
                "scenario_path": r.get("scenario_path"),
                "final_loss": r.get("final_loss"),
                "error": r.get("error", ""),
            }
            for r in failed
        ],
    }
    summary_json.write_text(json.dumps(summary, indent=2) + "\n")
    lines = [
        "# CedarBench AutoCedar-AITL Fast Run",
        "",
        f"Updated: `{summary['updated_at']}`",
        f"Completed: `{summary['total_completed']}`",
        f"Converged: `{summary['converged']}`",
        f"Failed/incomplete: `{summary['failed_or_incomplete']}`",
        f"Total wall time: `{summary['total_time_s']}s`",
        f"Total tokens: `{summary['total_tokens']}`",
        f"Estimated cost: `${summary['estimated_cost_usd']}`",
        "",
        "## Failures",
        "",
    ]
    if failed:
        lines.extend(
            f"- `{r.get('scenario_path')}`: loss `{r.get('final_loss')}`, error `{r.get('error', '')}`"
            for r in failed
        )
    else:
        lines.append("- None.")
    summary_md.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("cedarbench-aitl-fast-%Y%m%dT%H%M%SZ"))
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--effort", default="low", choices=["low", "medium", "high", "max"])
    parser.add_argument("--max-iters", type=int, default=20)
    parser.add_argument("--limit", type=int, default=0, help="Optional first-N scenario limit for smoke testing.")
    parser.add_argument("--resume", action="store_true", help="Skip scenarios already present in scenario_results.jsonl.")
    args = parser.parse_args()

    os.environ["AUTOCEDAR_PROVIDER"] = "codex"
    os.environ["AUTOCEDAR_HARNESS_EFFORT"] = args.effort

    out_root = ROOT / "experiments" / "cedarbench_aitl_fast" / args.run_id
    workspaces = out_root / "workspaces"
    out_root.mkdir(parents=True, exist_ok=True)
    workspaces.mkdir(parents=True, exist_ok=True)
    results_path = out_root / "scenario_results.jsonl"
    summary_json = out_root / "summary.json"
    summary_md = out_root / "SUMMARY.md"

    scenarios = _scenario_paths()
    if args.limit:
        scenarios = scenarios[: args.limit]
    completed = _load_completed(results_path) if args.resume else set()

    manifest = {
        "run_id": args.run_id,
        "mode": "AutoCedar-AITL fast path",
        "model": args.model,
        "effort": args.effort,
        "max_iters": args.max_iters,
        "scenario_count": len(scenarios),
        "description": (
            "Uses CedarBench checked-in schemas, verification plans, and reference "
            "policies as the expert/AITL formal target; runs verifier-guided "
            "synthesis with the requested model."
        ),
    }
    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(json.dumps(manifest, indent=2))
    with results_path.open("a") as out:
        for idx, scenario in enumerate(scenarios, 1):
            rel = str(scenario.relative_to(ROOT))
            if rel in completed:
                print(f"[{idx}/{len(scenarios)}] SKIP {rel}")
                continue
            print(f"[{idx}/{len(scenarios)}] RUN  {rel}", flush=True)
            result = run_scenario(
                scenario_path=str(scenario),
                run_dir=str(workspaces),
                phase1_model=args.model,
                phase2_model=args.model,
                max_iters=args.max_iters,
                gen_references=False,
                no_review=True,
            )
            row = asdict(result)
            row["scenario_path"] = rel
            out.write(json.dumps(row) + "\n")
            out.flush()
            _write_summary(results_path, summary_json, summary_md)
            status = "PASS" if row.get("converged") else "FAIL"
            print(
                f"[{idx}/{len(scenarios)}] {status} {rel} "
                f"iters={row.get('iterations')} loss={row.get('final_loss')} "
                f"time={row.get('total_time_s')}s",
                flush=True,
            )
    _write_summary(results_path, summary_json, summary_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
