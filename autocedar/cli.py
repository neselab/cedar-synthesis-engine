"""Command-line entry point for AutoCedar and the v1 harness."""

from __future__ import annotations

import argparse
import datetime
import getpass
import json
import os
import shutil
import subprocess
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
    write_dotenv_value,
)
from autocedar.harness_adapter import make_harness_synthesizer
from autocedar.llm import (
    ANTHROPIC_API_KEY_VALIDATION_MODEL,
    DEFAULT_EFFORT,
    LLMClient,
)
from autocedar.pipeline import author as author_pipeline
from autocedar.progress import format_property_progress
from autocedar.property_atomizer import propose_property_atom
from autocedar.schema_atomizer import propose_schema_atoms
from autocedar.ui.terminal import auto_approve, interactive_review_loop
from autocedar.providers import (
    AuthStore,
    CANONICAL_PROVIDER_IDS,
    ProviderOptions,
    SessionOverrides,
    SettingsStore,
    canonical_provider_id,
    get_provider_definition,
    resolve_api_key,
    resolve_provider_config,
)


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
        help="Check provider authentication, Cedar SymCC, and CVC5 setup.",
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

    config_p = sub.add_parser(
        "config",
        help="Show or persist provider, model, effort, and endpoint settings.",
    )
    config_p.add_argument(
        "--provider",
        choices=CANONICAL_PROVIDER_IDS,
        help="Set the default provider and select which provider to configure.",
    )
    config_p.add_argument("--model", help="Save the model for the selected provider.")
    config_p.add_argument(
        "--effort",
        choices=["low", "medium", "high", "max"],
        help="Save the reasoning effort for the selected provider.",
    )
    config_p.add_argument(
        "--endpoint",
        help="Save an OpenAI-compatible endpoint for the local provider.",
    )
    config_p.set_defaults(func=_cmd_config)

    auth_p = sub.add_parser(
        "auth",
        help="Inspect, add, or remove authentication for a provider.",
    )
    auth_sub = auth_p.add_subparsers(dest="auth_action", required=True)
    auth_status_p = auth_sub.add_parser("status", help="Show provider authentication status.")
    auth_status_p.add_argument("provider", nargs="?", choices=CANONICAL_PROVIDER_IDS)
    auth_status_p.set_defaults(func=_cmd_auth_status)
    auth_login_p = auth_sub.add_parser("login", help="Authenticate the selected provider.")
    auth_login_p.add_argument("provider", nargs="?", choices=CANONICAL_PROVIDER_IDS)
    auth_login_p.add_argument(
        "--api-key",
        help="API key for anthropic, openai, or local; omit to enter it securely.",
    )
    auth_login_p.set_defaults(func=_cmd_auth_login)
    auth_logout_p = auth_sub.add_parser("logout", help="Remove provider authentication.")
    auth_logout_p.add_argument("provider", nargs="?", choices=CANONICAL_PROVIDER_IDS)
    auth_logout_p.set_defaults(func=_cmd_auth_logout)

    api_p = sub.add_parser(
        "apikey",
        aliases=["api-key"],
        help="Deprecated alias for `auth login anthropic`.",
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
        help="Remove the saved provider API key.",
    )
    api_p.add_argument(
        "--no-validate",
        action="store_true",
        help="Save the key without making a live Anthropic validation request.",
    )
    api_p.add_argument(
        "--provider",
        choices=["anthropic", "openai", "local"],
        default="anthropic",
        help="API-key provider to configure (default: anthropic).",
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
        "--provider",
        choices=CANONICAL_PROVIDER_IDS,
        default=None,
        help="Provider for this run without changing saved settings.",
    )
    author_p.add_argument(
        "--model",
        default=None,
        help="Model for schema/property atomization and Stage 3 synthesis (default: provider default).",
    )
    author_p.add_argument(
        "--effort",
        choices=["low", "medium", "high", "max"],
        default=None,
        help="Adaptive thinking effort for Stage 1/2 atomization (default: provider setting).",
    )
    author_p.add_argument(
        "--auto-approve",
        action="store_true",
        help=(
            "Advance atoms without interactive review, for plumbing tests only; "
            "this does not count as human semantic approval."
        ),
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
        "--provider",
        choices=CANONICAL_PROVIDER_IDS,
        default=None,
        help="Provider for this run without changing saved settings.",
    )
    resume_p.add_argument(
        "--model",
        default=None,
        help="Model for continued atomization and Stage 3 synthesis (default: provider default).",
    )
    resume_p.add_argument(
        "--effort",
        choices=["low", "medium", "high", "max"],
        default=None,
        help="Adaptive thinking effort for continued authoring (default: provider setting).",
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
    synth_p.add_argument(
        "--provider",
        choices=CANONICAL_PROVIDER_IDS,
        default=None,
        help="Provider for this run without changing saved settings.",
    )
    synth_p.add_argument(
        "--model",
        default=None,
        help="Model for both synthesis phases unless a phase-specific model is set.",
    )
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


def _cmd_config(args: argparse.Namespace) -> int:
    """Show or persist non-secret provider settings."""

    store = SettingsStore()
    settings = store.load()
    effective = resolve_provider_config(settings=settings)
    provider = canonical_provider_id(args.provider or effective.provider)
    changed = any((args.provider, args.model, args.effort, args.endpoint))
    if args.provider:
        settings = settings.with_default_provider(provider)
    if any((args.model, args.effort, args.endpoint)):
        if args.endpoint and provider != "local":
            raise SystemExit("--endpoint is only supported for --provider local.")
        current = settings.options_for(provider)
        settings = settings.with_provider_options(
            provider,
            ProviderOptions(
                model=args.model or current.model,
                base_url=args.endpoint or current.base_url,
                reasoning_effort=args.effort or current.reasoning_effort,
            ),
        )
    if changed:
        store.save(settings)

    session = SessionOverrides(provider=provider) if args.provider else None
    resolved = resolve_provider_config(session=session, settings=settings)
    print(f"settings: {store.path}")
    print(f"provider: {resolved.provider} ({resolved.source_for('provider')})")
    print(f"model:    {resolved.model} ({resolved.source_for('model')})")
    print(
        "effort:   "
        f"{resolved.reasoning_effort or '(provider default)'} "
        f"({resolved.source_for('reasoning_effort')})",
    )
    print(
        "endpoint: "
        f"{resolved.base_url or '(provider managed)'} "
        f"({resolved.source_for('base_url')})",
    )
    if changed:
        print("Saved non-secret provider settings.")
    return 0


def _cmd_auth_status(args: argparse.Namespace) -> int:
    providers = (
        [canonical_provider_id(args.provider)]
        if args.provider
        else [_selected_provider(None)]
    )
    failed = False
    for provider in providers:
        ready, detail = _provider_auth_status(provider)
        print(f"{provider}: {'ready' if ready else 'not ready'} ({detail})")
        if provider != "local" and not ready:
            failed = True
    return 1 if failed else 0


def _cmd_auth_login(args: argparse.Namespace) -> int:
    provider = _selected_provider(args.provider)
    definition = get_provider_definition(provider)
    if provider in {"codex", "claude-cli"}:
        command = ["codex", "login"] if provider == "codex" else ["claude", "auth", "login"]
        executable = shutil.which(command[0])
        if executable is None:
            raise SystemExit(
                f"{definition.display_name} CLI is not installed or is not on PATH.",
            )
        completed = subprocess.run([executable, *command[1:]], check=False)
        return completed.returncode

    value = (args.api_key or "").strip()
    if not value:
        if not _can_prompt_for_secret():
            raise SystemExit(
                f"No {definition.display_name} API key was provided. Use --api-key or run interactively.",
            )
        value = getpass.getpass(f"Paste {definition.display_name} API key (input hidden): ").strip()
    if not value:
        raise SystemExit("API key cannot be empty.")
    if provider == "anthropic":
        value = normalize_anthropic_api_key(value)
        if not is_real_anthropic_api_key(value):
            raise SystemExit(
                "That does not look like a real Anthropic API key. Paste the full key, "
                "not a placeholder or redacted value.",
            )
        model = ANTHROPIC_API_KEY_VALIDATION_MODEL
        try:
            validate_anthropic_api_key(value, model=model)
        except Exception as exc:
            raise SystemExit(format_api_key_validation_error(exc, model=model)) from exc
    path = AuthStore().path
    AuthStore(path).set_api_key(provider, value)
    print(f"Saved {definition.display_name} API key to {path} ({_mask_secret(value)}).")
    return 0


def _cmd_auth_logout(args: argparse.Namespace) -> int:
    provider = _selected_provider(args.provider)
    definition = get_provider_definition(provider)
    if provider in {"codex", "claude-cli"}:
        command = ["codex", "logout"] if provider == "codex" else ["claude", "auth", "logout"]
        executable = shutil.which(command[0])
        if executable is None:
            raise SystemExit(
                f"{definition.display_name} CLI is not installed or is not on PATH.",
            )
        completed = subprocess.run([executable, *command[1:]], check=False)
        return completed.returncode

    store = AuthStore()
    store.remove_api_key(provider)
    print(f"Removed the saved {definition.display_name} API key from {store.path}.")
    credential = resolve_api_key(provider)
    if credential.api_key:
        print(f"An API key is still active from {credential.source}; unset it there to fully log out.")
    return 0


def _selected_provider(value: str | None) -> str:
    if value:
        return canonical_provider_id(value)
    return resolve_provider_config().provider


def _provider_auth_status(provider: str) -> tuple[bool, str]:
    """Return provider auth state without reading external credential files."""

    canonical = canonical_provider_id(provider)
    if canonical == "codex":
        return _external_auth_status(["codex", "login", "status"], json_output=False)
    if canonical == "claude-cli":
        return _external_auth_status(
            ["claude", "auth", "status", "--json"],
            json_output=True,
        )
    credential = resolve_api_key(canonical)
    if credential.api_key:
        return True, credential.source
    if canonical == "local":
        return True, "API key optional; endpoint authentication is unset"
    return False, "API key unset"


def _external_auth_status(
    command: list[str],
    *,
    json_output: bool,
) -> tuple[bool, str]:
    executable = shutil.which(command[0])
    if executable is None:
        return False, f"{command[0]} CLI not found"
    try:
        completed = subprocess.run(
            [executable, *command[1:]],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (completed.stdout or completed.stderr).strip()
    if completed.returncode != 0:
        return False, _compact_cli_output(output) or "not logged in"
    if json_output:
        try:
            payload = json.loads(completed.stdout)
        except (TypeError, json.JSONDecodeError):
            return False, "CLI returned invalid authentication status"
        if payload.get("loggedIn") is not True:
            return False, "not logged in"
        method = str(payload.get("authMethod") or payload.get("subscriptionType") or "CLI login")
        return True, method
    return True, _compact_cli_output(output) or "CLI login available"


def _compact_cli_output(value: str, *, limit: int = 180) -> str:
    text = " ".join(value.split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _mask_secret(value: str) -> str:
    if len(value) <= 10:
        return "[set]"
    return f"{value[:4]}...{value[-4:]}"


def _cmd_apikey(args: argparse.Namespace) -> int:
    provider = canonical_provider_id(getattr(args, "provider", "anthropic"))
    env_key = {
        "anthropic": ANTHROPIC_API_KEY,
        "openai": "OPENAI_API_KEY",
        "local": "AUTOCEDAR_LOCAL_API_KEY",
    }[provider]
    value = (
        normalize_anthropic_api_key(args.key or "")
        if provider == "anthropic"
        else (args.key or "").strip()
    )
    if args.clear or value.lower() in {"clear", "unset", "remove", "delete"}:
        if args.env:
            path = remove_dotenv_value(env_key, env_path=args.env)
        else:
            store = AuthStore()
            store.remove_api_key(provider)
            path = store.path
        print(f"Removed the saved {provider} API key from {path}.")
        return 0

    if not value:
        if not _can_prompt_for_secret():
            raise SystemExit(
                f"The {provider} API key is not configured. Run "
                f"`autocedar auth login {provider}` or rerun from an interactive terminal.",
            )
        entered = getpass.getpass(f"Paste {provider} API key (input hidden): ")
        value = normalize_anthropic_api_key(entered) if provider == "anthropic" else entered.strip()

    if provider == "anthropic" and not is_real_anthropic_api_key(value):
        raise SystemExit(
            "That does not look like a real Anthropic API key. "
            "Run `autocedar apikey` again and paste the full key.",
        )

    if provider == "anthropic" and not args.no_validate:
        model = ANTHROPIC_API_KEY_VALIDATION_MODEL
        try:
            validate_anthropic_api_key(value, model=model)
        except Exception as exc:
            raise SystemExit(format_api_key_validation_error(exc, model=model)) from exc

    if args.env:
        path = write_dotenv_value(env_key, value, env_path=args.env)
    else:
        store = AuthStore()
        try:
            store.set_api_key(provider, value)
        except Exception as exc:
            raise SystemExit(f"Could not save API key: {exc}") from exc
        path = store.path
    masked = mask_api_key_for_display(value) if provider == "anthropic" else _mask_secret(value)
    print(f"Saved {provider} API key to {path} ({masked}).")
    return 0


def _cmd_author(args: argparse.Namespace) -> int:
    config = _command_provider_config(args)
    _require_provider_auth(config.provider)
    spec_path = Path(args.spec)
    if not spec_path.exists():
        raise SystemExit(f"spec not found: {spec_path}")

    model = config.model
    effort = config.reasoning_effort or DEFAULT_EFFORT
    llm = LLMClient(provider=config.provider, model=model, effort=effort)

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

    def property_progress(payload):
        print(f"property progress: {format_property_progress(payload)}", flush=True)

    reviewer.property_progress = property_progress  # type: ignore[attr-defined]

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
            phase1_model=model,
            phase2_model=model,
            provider=config.provider,
            no_review=True,
        ),
        schema_path_override=args.schema,
        run_incremental_checks=False,
        max_schema_gap_repairs=getattr(args, "max_schema_gap_repairs", None),
    )

    completed = _authoring_completed(result)
    print(f"session:   {result.session_dir}")
    if completed:
        print(f"candidate: {result.candidate_path}")
    print(f"approved:  {result.final_user_approved}")
    if result.notes:
        print("notes:")
        for note in result.notes:
            print(f"  - {note}")
    return 0 if completed else 1


def _cmd_resume(args: argparse.Namespace) -> int:
    config = _command_provider_config(args)
    _require_provider_auth(config.provider)
    session_dir = Path(args.session)
    if not session_dir.exists():
        raise SystemExit(f"session not found: {session_dir}")
    input_files = sorted((session_dir / "input").glob("*"))
    if not input_files:
        raise SystemExit(f"resume session has no input spec under: {session_dir / 'input'}")
    spec_path = input_files[0]

    model = config.model
    effort = config.reasoning_effort or DEFAULT_EFFORT
    llm = LLMClient(provider=config.provider, model=model, effort=effort)
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

    def property_progress(payload):
        print(f"property progress: {format_property_progress(payload)}", flush=True)

    reviewer.property_progress = property_progress  # type: ignore[attr-defined]

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
            phase1_model=model,
            phase2_model=model,
            provider=config.provider,
            no_review=True,
        ),
        resume_from=session_dir,
        run_incremental_checks=False,
        max_schema_gap_repairs=getattr(args, "max_schema_gap_repairs", None),
    )

    completed = _authoring_completed(result)
    print(f"session:   {result.session_dir}")
    if completed:
        print(f"candidate: {result.candidate_path}")
    print(f"approved:  {result.final_user_approved}")
    if result.notes:
        print("notes:")
        for note in result.notes:
            print(f"  - {note}")
    return 0 if completed else 1


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
    config = _command_provider_config(args)
    _require_provider_auth(config.provider)
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

    shared_model = getattr(args, "model", None) or config.model
    phase1_model = args.phase1_model or shared_model or DEFAULT_PHASE1_MODEL
    phase2_model = args.phase2_model or shared_model or DEFAULT_MODEL
    max_iters = args.max_iters or MAX_ITERATIONS

    results = []
    for scenario in args.scenario:
        result = run_scenario(
            scenario_path=os.path.abspath(scenario),
            run_dir=str(run_dir),
            phase1_model=phase1_model,
            phase2_model=phase2_model,
            provider=config.provider,
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
    return resolve_provider_config().provider == "anthropic"


def _command_provider_config(args: argparse.Namespace):
    return resolve_provider_config(
        session=SessionOverrides(
            provider=getattr(args, "provider", None),
            model=getattr(args, "model", None),
            reasoning_effort=getattr(args, "effort", None),
        ),
    )


def _authoring_completed(result: object) -> bool:
    """Return true when the pipeline produced its final candidate artifact.

    Process completion and human semantic approval are intentionally separate:
    an ``--auto-approve`` plumbing run may complete successfully while its
    ``final_user_approved`` field remains false.
    """
    candidate_path = getattr(result, "candidate_path", None)
    if candidate_path is None:
        return False
    try:
        return Path(candidate_path).is_file()
    except TypeError:
        return False


def _can_prompt_for_secret() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _prompt_for_missing_api_key(*, allow_skip: bool) -> bool:
    provider = resolve_provider_config().provider
    if provider not in {"anthropic", "openai"}:
        return True
    credential = resolve_api_key(provider)
    if credential.api_key:
        return True
    if not _can_prompt_for_secret():
        return False

    print(
        f"The {provider} API key is not configured in the environment, project .env, "
        f"or user auth store ({AuthStore().path}).",
    )
    entered = getpass.getpass(
        f"Paste {provider} API key to save, or press Enter to continue without it: ",
    )
    value = normalize_anthropic_api_key(entered) if provider == "anthropic" else entered.strip()
    if not value:
        if allow_skip:
            print("Continuing without an API key. Open-ended chat/model calls will be limited.")
            return False
        raise SystemExit(f"Cancelled. Run `autocedar auth login {provider}` when you have the key.")
    if provider == "anthropic" and not is_real_anthropic_api_key(value):
        raise SystemExit(
            "That does not look like a real Anthropic API key. "
            "Run `autocedar apikey` again and paste the full key.",
        )
    if provider == "anthropic":
        model = ANTHROPIC_API_KEY_VALIDATION_MODEL
        try:
            validate_anthropic_api_key(value, model=model)
        except Exception as exc:
            raise SystemExit(format_api_key_validation_error(exc, model=model)) from exc
    store = AuthStore()
    store.set_api_key(provider, value)
    print(f"Saved {provider} API key to {store.path} ({_mask_secret(value)}).")
    return True


def _require_api_key_for_llm_command() -> None:
    _require_provider_auth(resolve_provider_config().provider)


def _require_provider_auth(provider: str) -> None:
    canonical = canonical_provider_id(provider)
    if canonical not in {"anthropic", "openai"}:
        return
    credential = resolve_api_key(canonical)
    if credential.api_key:
        return
    if canonical == resolve_provider_config().provider and _prompt_for_missing_api_key(allow_skip=False):
        return
    raise SystemExit(
        f"{canonical} API authentication is not configured. "
        f"Run `autocedar auth login {canonical}`, choose codex/claude-cli, "
        "or configure the local provider.",
    )


if __name__ == "__main__":
    raise SystemExit(main())
