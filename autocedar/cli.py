"""Command-line entry point for AutoCedar and the v1 harness."""

from __future__ import annotations

import argparse
import datetime
import getpass
import os
import sys
from pathlib import Path
from typing import Sequence

from autocedar import __version__
from autocedar.api_key import (
    format_api_key_validation_error,
    mask_api_key_for_display,
    normalize_anthropic_api_key,
    validate_anthropic_api_key,
)
from autocedar.env import (
    ANTHROPIC_API_KEY,
    is_real_anthropic_api_key,
    load_dotenv,
    remove_dotenv_value,
    remove_user_config_value,
    user_config_env_path,
    write_dotenv_value,
    write_user_config_value,
)
from autocedar.harness_adapter import make_harness_synthesizer
from autocedar.llm import DEFAULT_EFFORT, LLMClient, default_model_for_provider, default_provider
from autocedar.pipeline import author as author_pipeline
from autocedar.property_atomizer import propose_property_atom
from autocedar.schema_atomizer import propose_schema_atoms
from autocedar.ui.terminal import auto_approve, interactive_review_loop


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        from autocedar.tui import run_tui

        _prompt_for_missing_api_key(allow_skip=True)
        return run_tui()
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autocedar",
        description="Human-in-the-loop Cedar policy authoring and verification.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    version_p = sub.add_parser(
        "version",
        help="Print the installed AutoCedar version.",
    )
    version_p.set_defaults(func=_cmd_version)

    tui_p = sub.add_parser(
        "tui",
        help="Open the interactive AutoCedar shell.",
    )
    tui_p.set_defaults(func=_cmd_tui)

    doctor_p = sub.add_parser(
        "doctor",
        help="Check API-key, Cedar SymCC, and CVC5 setup before authoring.",
    )
    doctor_p.add_argument(
        "--no-live-symcc",
        action="store_true",
        help="Skip the live SymCC smoke test.",
    )
    doctor_p.set_defaults(func=_cmd_doctor)

    setup_p = sub.add_parser(
        "setup",
        help="Install or print install steps for Cedar CLI and CVC5.",
    )
    setup_p.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Run available install commands without prompting.",
    )
    setup_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the detected setup plan.",
    )
    setup_p.add_argument(
        "--skip-cedar",
        action="store_true",
        help="Do not install or check Cedar CLI.",
    )
    setup_p.add_argument(
        "--skip-cvc5",
        action="store_true",
        help="Do not install or check CVC5.",
    )
    setup_p.set_defaults(func=_cmd_setup)

    api_p = sub.add_parser(
        "apikey",
        aliases=["api-key"],
        help="Save, update, or clear ANTHROPIC_API_KEY in the user config.",
    )
    api_p.add_argument(
        "key",
        nargs="?",
        help="Anthropic API key. Omit to enter it securely; use `clear` to remove it.",
    )
    api_p.add_argument(
        "--env",
        type=Path,
        default=None,
        help="Write to this .env path instead of the user-level AutoCedar config.",
    )
    api_p.add_argument(
        "--clear",
        action="store_true",
        help="Remove ANTHROPIC_API_KEY from .env and this process.",
    )
    api_p.add_argument(
        "--no-validate",
        action="store_true",
        help="Save the key without making a live Anthropic validation request.",
    )
    api_p.set_defaults(func=_cmd_apikey)

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
    author_p.add_argument(
        "--max-schema-gap-repairs",
        type=int,
        default=None,
        help=(
            "Optional maximum Stage 2 schema-repair loops before stopping "
            "(default: no cap)."
        ),
    )
    author_p.set_defaults(func=_cmd_author)

    resume_p = sub.add_parser(
        "resume",
        help="Resume an incomplete AutoCedar authoring session from its logs.",
    )
    resume_p.add_argument("session", help="Prior session directory to resume.")
    resume_p.add_argument("--out", required=True, help="Directory for the resumed session output.")
    resume_p.add_argument("--session-id", default=None, help="Stable resumed session id.")
    resume_p.add_argument(
        "--model",
        default=default_model_for_provider(),
        help=(
            "Model for continued atomization and Stage 3 synthesis "
            f"(default: {default_model_for_provider()})."
        ),
    )
    resume_p.add_argument(
        "--effort",
        choices=["low", "medium", "high", "max"],
        default=os.environ.get("AUTOCEDAR_EFFORT", DEFAULT_EFFORT),
        help=f"Adaptive thinking effort for continued authoring (default: {DEFAULT_EFFORT}).",
    )
    resume_p.add_argument(
        "--auto-approve",
        action="store_true",
        help="Approve newly proposed atoms without interactive review, for plumbing tests only.",
    )
    resume_p.add_argument(
        "--max-schema-gap-repairs",
        type=int,
        default=None,
        help=(
            "Optional maximum Stage 2 schema-repair loops before stopping "
            "(default: no cap)."
        ),
    )
    resume_p.set_defaults(func=_cmd_resume)

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


def _cmd_version(args: argparse.Namespace) -> int:
    _ = args
    print(f"autocedar {__version__}")
    return 0


def _cmd_tui(args: argparse.Namespace) -> int:
    from autocedar.tui import run_tui

    _prompt_for_missing_api_key(allow_skip=True)
    return run_tui()


def _cmd_doctor(args: argparse.Namespace) -> int:
    from autocedar.doctor import format_doctor_report, run_doctor

    report = run_doctor(live_symcc=not args.no_live_symcc)
    print(format_doctor_report(report))
    return 1 if report.failed else 0


def _cmd_setup(args: argparse.Namespace) -> int:
    from autocedar.setup_tools import (
        build_setup_plan,
        format_setup_plan,
        format_setup_results,
        run_setup_plan,
    )

    plan = build_setup_plan(
        install_cedar=not args.skip_cedar,
        install_cvc5=not args.skip_cvc5,
    )
    print(format_setup_plan(plan))
    if args.dry_run or not plan.needs_install:
        return 1 if plan.blocked else 0
    if plan.blocked:
        return 1
    if not args.yes:
        if not sys.stdin.isatty():
            print("\nRun `autocedar setup --yes` to execute the install commands.")
            return 1
        answer = input("\nRun these install commands now? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Cancelled. No changes made.")
            return 1
    results = run_setup_plan(plan)
    print()
    print(format_setup_results(results))
    return 1 if any(step.status == "FAIL" for step in results) else 0


def _cmd_apikey(args: argparse.Namespace) -> int:
    value = normalize_anthropic_api_key(args.key or "")
    if args.clear or value.lower() in {"clear", "unset", "remove", "delete"}:
        path = (
            remove_dotenv_value(ANTHROPIC_API_KEY, env_path=args.env)
            if args.env
            else remove_user_config_value(ANTHROPIC_API_KEY)
        )
        print(f"Removed ANTHROPIC_API_KEY from {path}.")
        return 0

    if not value:
        if not _can_prompt_for_secret():
            raise SystemExit(
                "ANTHROPIC_API_KEY is not configured. Run "
                "`autocedar apikey sk-ant-...` or rerun from an interactive terminal.",
            )
        value = normalize_anthropic_api_key(
            getpass.getpass("Paste Anthropic API key (input hidden): "),
        )

    if not is_real_anthropic_api_key(value):
        raise SystemExit(
            "That does not look like a real Anthropic API key. "
            "Run `autocedar apikey` again and paste the full key.",
        )

    if not args.no_validate:
        model = default_model_for_provider("anthropic")
        try:
            validate_anthropic_api_key(value, model=model)
        except Exception as exc:
            raise SystemExit(format_api_key_validation_error(exc, model=model)) from exc

    path = (
        write_dotenv_value(ANTHROPIC_API_KEY, value, env_path=args.env)
        if args.env
        else write_user_config_value(ANTHROPIC_API_KEY, value)
    )
    print(f"Saved ANTHROPIC_API_KEY to {path} ({mask_api_key_for_display(value)}).")
    return 0


def _cmd_author(args: argparse.Namespace) -> int:
    _require_api_key_for_llm_command()
    spec_path = Path(args.spec)
    if not spec_path.exists():
        raise SystemExit(f"spec not found: {spec_path}")

    llm = LLMClient(provider=default_provider(), model=args.model, effort=args.effort)

    spec_text = spec_path.read_text()

    def schema_proposer(text: str):
        return propose_schema_atoms(text, llm)

    def property_proposer(text: str, schema_path: str, prior_atoms, prior_decisions):
        return propose_property_atom(text, schema_path, llm, prior_atoms, prior_decisions)

    def schema_repairer(text: str, rejected_atom, reason: str, prior_atoms):
        _ = prior_atoms
        return llm.propose_alternative_atom(rejected_atom, reason, text)

    def schema_fixer(schema_text: str, cedar_error: str, text: str) -> str:
        return llm.fix_schema(schema_text, cedar_error, text)

    def property_repairer(
        text: str,
        schema_path: str,
        rejected_atom,
        reason: str,
        prior_atoms,
    ):
        schema_text = Path(schema_path).read_text()
        return llm.propose_alternative_property_atom(
            rejected_atom,
            reason,
            text,
            schema_text,
            prior_atoms,
        )

    def property_repair_planner(
        text: str,
        schema_path: str,
        current_atom,
        decision,
        prior_atoms,
        schema_text: str,
        symbolic_log,
    ):
        response = llm.plan_property_rejection(
            current_atom=current_atom,
            user_reason=decision.reason,
            spec_text=text,
            schema_text=schema_text,
            prior_atoms=prior_atoms,
            symbolic_log=symbolic_log,
        )
        from autocedar.pipeline import PropertyRepairPlan

        return PropertyRepairPlan(
            action=response.action,
            target_atom=response.target_atom,
            reason=response.reason,
            repair_instruction=response.repair_instruction,
            schema_gap_summary=response.schema_gap_summary,
        )

    def reviewer(atom):
        if args.auto_approve:
            return auto_approve(atom)
        reviewed = interactive_review_loop(
            [atom],
            llm=llm,
            spec_text=spec_text,
        )
        return reviewed[0]

    result = author_pipeline(
        spec_path=spec_path,
        output_dir=Path(args.out),
        session_id=args.session_id,
        review_atom=reviewer,
        propose_schema_atoms=schema_proposer,
        propose_property_atom=property_proposer,
        repair_schema_atom=schema_repairer,
        fix_schema=schema_fixer,
        plan_property_repair=property_repair_planner,
        repair_property_atom=property_repairer,
        synthesize=make_harness_synthesizer(
            phase1_model=args.model,
            phase2_model=args.model,
            no_review=True,
        ),
        schema_path_override=args.schema,
        max_schema_gap_repairs=getattr(args, "max_schema_gap_repairs", None),
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


def _cmd_resume(args: argparse.Namespace) -> int:
    _require_api_key_for_llm_command()
    session_dir = Path(args.session)
    if not session_dir.exists():
        raise SystemExit(f"session not found: {session_dir}")
    input_files = sorted((session_dir / "input").glob("*"))
    if not input_files:
        raise SystemExit(f"resume session has no input spec under: {session_dir / 'input'}")
    spec_path = input_files[0]

    llm = LLMClient(provider=default_provider(), model=args.model, effort=args.effort)
    spec_text = spec_path.read_text()

    def schema_proposer(text: str):
        return propose_schema_atoms(text, llm)

    def property_proposer(text: str, schema_path: str, prior_atoms, prior_decisions):
        return propose_property_atom(text, schema_path, llm, prior_atoms, prior_decisions)

    def schema_repairer(text: str, rejected_atom, reason: str, prior_atoms):
        _ = prior_atoms
        return llm.propose_alternative_atom(rejected_atom, reason, text)

    def schema_fixer(schema_text: str, cedar_error: str, text: str) -> str:
        return llm.fix_schema(schema_text, cedar_error, text)

    def property_repairer(
        text: str,
        schema_path: str,
        rejected_atom,
        reason: str,
        prior_atoms,
    ):
        schema_text = Path(schema_path).read_text()
        return llm.propose_alternative_property_atom(
            rejected_atom,
            reason,
            text,
            schema_text,
            prior_atoms,
        )

    def property_repair_planner(
        text: str,
        schema_path: str,
        current_atom,
        decision,
        prior_atoms,
        schema_text: str,
        symbolic_log,
    ):
        response = llm.plan_property_rejection(
            current_atom=current_atom,
            user_reason=decision.reason,
            spec_text=text,
            schema_text=schema_text,
            prior_atoms=prior_atoms,
            symbolic_log=symbolic_log,
        )
        from autocedar.pipeline import PropertyRepairPlan

        return PropertyRepairPlan(
            action=response.action,
            target_atom=response.target_atom,
            reason=response.reason,
            repair_instruction=response.repair_instruction,
            schema_gap_summary=response.schema_gap_summary,
        )

    def reviewer(atom):
        if args.auto_approve:
            return auto_approve(atom)
        reviewed = interactive_review_loop(
            [atom],
            llm=llm,
            spec_text=spec_text,
        )
        return reviewed[0]

    result = author_pipeline(
        spec_path=spec_path,
        output_dir=Path(args.out),
        session_id=args.session_id,
        review_atom=reviewer,
        propose_schema_atoms=schema_proposer,
        propose_property_atom=property_proposer,
        repair_schema_atom=schema_repairer,
        fix_schema=schema_fixer,
        plan_property_repair=property_repair_planner,
        repair_property_atom=property_repairer,
        synthesize=make_harness_synthesizer(
            phase1_model=args.model,
            phase2_model=args.model,
            no_review=True,
        ),
        resume_from=session_dir,
        run_incremental_checks=False,
        max_schema_gap_repairs=getattr(args, "max_schema_gap_repairs", None),
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
    _require_api_key_for_llm_command()
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


def _provider_uses_anthropic_key() -> bool:
    return default_provider() not in {"codex", "openai-codex"}


def _can_prompt_for_secret() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _prompt_for_missing_api_key(*, allow_skip: bool) -> bool:
    if not _provider_uses_anthropic_key():
        return True
    if is_real_anthropic_api_key(os.environ.get(ANTHROPIC_API_KEY)):
        return True
    if not _can_prompt_for_secret():
        return False

    print(
        "ANTHROPIC_API_KEY is not configured in the environment, project .env, "
        f"or user config ({user_config_env_path()}).",
    )
    value = normalize_anthropic_api_key(
        getpass.getpass(
            "Paste Anthropic API key to save to user config, or press Enter to continue without it: ",
        ),
    )
    if not value:
        if allow_skip:
            print("Continuing without an API key. Open-ended chat/model calls will be limited.")
            return False
        raise SystemExit("Cancelled. Run `autocedar apikey` when you have the key.")
    if not is_real_anthropic_api_key(value):
        raise SystemExit(
            "That does not look like a real Anthropic API key. "
            "Run `autocedar apikey` again and paste the full key.",
        )
    model = default_model_for_provider("anthropic")
    try:
        validate_anthropic_api_key(value, model=model)
    except Exception as exc:
        raise SystemExit(format_api_key_validation_error(exc, model=model)) from exc
    path = write_user_config_value(ANTHROPIC_API_KEY, value)
    print(f"Saved ANTHROPIC_API_KEY to {path} ({mask_api_key_for_display(value)}).")
    return True


def _require_api_key_for_llm_command() -> None:
    if _prompt_for_missing_api_key(allow_skip=False):
        return
    raise SystemExit(
        "ANTHROPIC_API_KEY is not configured. Run `autocedar apikey`, "
        "or set AUTOCEDAR_PROVIDER=codex if you are using local Codex auth.",
    )


if __name__ == "__main__":
    raise SystemExit(main())
