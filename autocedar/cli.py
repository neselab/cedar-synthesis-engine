"""Command-line entry point for AutoCedar and the v1 harness."""

from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path
from typing import Sequence

from autocedar.env import load_dotenv
from autocedar.harness_adapter import make_harness_synthesizer
from autocedar.llm import DEFAULT_EFFORT, LLMClient, default_model_for_provider, default_provider
from autocedar.pipeline import author as author_pipeline
from autocedar.property_atomizer import propose_property_atoms
from autocedar.schema_atomizer import propose_schema_atoms
from autocedar.ui.terminal import auto_approve, interactive_review_loop


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        from autocedar.tui import run_tui

        return run_tui()
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autocedar",
        description="Human-in-the-loop Cedar policy authoring and verification.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    tui_p = sub.add_parser(
        "tui",
        help="Open the interactive AutoCedar shell.",
    )
    tui_p.set_defaults(func=_cmd_tui)

    author_p = sub.add_parser(
        "author",
        help="Run the HITL authoring pipeline for a prose spec.",
    )
    author_p.add_argument("spec", help="Path to the prose policy specification.")
    author_p.add_argument("--out", required=True, help="Directory for session output.")
    author_p.add_argument("--session-id", default=None, help="Stable session id.")
    author_p.add_argument(
        "--schema",
        default=None,
        help="Use an existing schema and skip Stage 1 atom proposal.",
    )
    author_p.add_argument(
        "--model",
        default=default_model_for_provider(),
        help=(
            "Model for schema/property atomization and Stage 3 synthesis "
            f"(default: {default_model_for_provider()})."
        ),
    )
    author_p.add_argument(
        "--effort",
        choices=["low", "medium", "high", "max"],
        default=os.environ.get("AUTOCEDAR_EFFORT", DEFAULT_EFFORT),
        help=f"Adaptive thinking effort for Stage 1/2 atomization (default: {DEFAULT_EFFORT}).",
    )
    author_p.add_argument(
        "--auto-approve",
        action="store_true",
        help="Approve atoms without interactive review, for scripted runs.",
    )
    author_p.set_defaults(func=_cmd_author)

    verify_p = sub.add_parser(
        "verify",
        help="Verify an existing scenario/workspace candidate with cedar symcc.",
    )
    verify_p.add_argument("workspace", help="Directory with schema, candidate, and verification_plan.py.")
    verify_p.set_defaults(func=_cmd_verify)

    synth_p = sub.add_parser(
        "synthesize",
        help="Run the v1 CEGIS synthesis harness for one or more scenarios.",
    )
    synth_p.add_argument("scenario", nargs="+", help="Scenario directory path(s).")
    synth_p.add_argument("--out", default="eval_runs", help="Output directory for runs.")
    synth_p.add_argument("--run-id", default=None, help="Run id directory name.")
    synth_p.add_argument(
        "--phase1-model",
        default=None,
        help="Model for reference generation when --gen-references is used.",
    )
    synth_p.add_argument(
        "--phase2-model",
        default=None,
        help="Model for iterative policy synthesis.",
    )
    synth_p.add_argument("--max-iters", type=int, default=None, help="Max CEGIS iterations.")
    synth_p.add_argument(
        "--gen-references",
        action="store_true",
        help="Regenerate verification plan and references before synthesis.",
    )
    synth_p.add_argument(
        "--no-review",
        action="store_true",
        help="Skip Phase 1 reference review.",
    )
    synth_p.set_defaults(func=_cmd_synthesize)

    return parser


def _cmd_tui(args: argparse.Namespace) -> int:
    from autocedar.tui import run_tui

    return run_tui()


def _cmd_author(args: argparse.Namespace) -> int:
    spec_path = Path(args.spec)
    if not spec_path.exists():
        raise SystemExit(f"spec not found: {spec_path}")

    llm = LLMClient(provider=default_provider(), model=args.model, effort=args.effort)

    spec_text = spec_path.read_text()

    def schema_proposer(text: str):
        return propose_schema_atoms(text, llm)

    def property_proposer(text: str, schema_path: str):
        return propose_property_atoms(text, schema_path, llm)

    def reviewer(atom):
        if args.auto_approve:
            return auto_approve(atom)
        reviewed = interactive_review_loop(
            [atom],
            llm=llm,
            spec_text=spec_text,
        )
        return reviewed[0]

    author_kwargs = {}
    if args.schema is None:
        author_kwargs["propose_schema_atoms"] = schema_proposer

    result = author_pipeline(
        spec_path=spec_path,
        output_dir=Path(args.out),
        session_id=args.session_id,
        review_atom=reviewer,
        propose_property_atoms=property_proposer,
        synthesize=make_harness_synthesizer(
            phase1_model=args.model,
            phase2_model=args.model,
            no_review=True,
        ),
        schema_path_override=args.schema,
        **author_kwargs,
    )

    print(f"session:   {result.session_dir}")
    if result.candidate_path:
        print(f"candidate: {result.candidate_path}")
    print(f"approved:  {result.final_user_approved}")
    if result.notes:
        print("notes:")
        for note in result.notes:
            print(f"  - {note}")
    return 0 if result.final_user_approved else 1


def _cmd_verify(args: argparse.Namespace) -> int:
    from autocedar.harness.orchestrator import run_verification

    workspace = Path(args.workspace)
    if not workspace.exists():
        raise SystemExit(f"workspace not found: {workspace}")
    candidate = workspace / "candidate.cedar"
    if not candidate.exists():
        raise SystemExit(f"candidate not found: {candidate}")

    vr = run_verification(str(workspace))
    for result in vr.results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{result.check_name}: {status} ({result.check_type})")
        if not result.passed and result.counterexample:
            print(result.counterexample)
    print(f"loss: {vr.loss}")
    return 0 if vr.loss == 0 else 1


def _cmd_synthesize(args: argparse.Namespace) -> int:
    from autocedar.harness.eval_harness import (
        DEFAULT_MODEL,
        DEFAULT_PHASE1_MODEL,
        MAX_ITERATIONS,
        run_scenario,
    )

    run_id = args.run_id or datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ",
    )
    run_dir = Path(args.out) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    phase1_model = args.phase1_model or DEFAULT_PHASE1_MODEL
    phase2_model = args.phase2_model or DEFAULT_MODEL
    max_iters = args.max_iters or MAX_ITERATIONS

    results = []
    for scenario in args.scenario:
        result = run_scenario(
            scenario_path=os.path.abspath(scenario),
            run_dir=str(run_dir),
            phase1_model=phase1_model,
            phase2_model=phase2_model,
            max_iters=max_iters,
            gen_references=args.gen_references,
            no_review=args.no_review,
        )
        results.append(result)

    print("")
    print("summary:")
    for result in results:
        status = "PASS" if result.converged else "FAIL"
        if result.error:
            status = "ERROR"
        print(
            f"  {result.scenario}: {status} "
            f"iters={result.iterations}/{result.max_iterations} "
            f"loss={result.final_loss} cost=${result.estimated_cost_usd:.4f}",
        )
        if result.error:
            print(f"    {result.error}")
    print(f"output: {run_dir}")
    return 0 if all(r.converged for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
