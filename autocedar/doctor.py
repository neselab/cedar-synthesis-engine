"""Environment preflight checks for AutoCedar.

The doctor command makes verifier setup failures explicit before a user
enters an authoring session. It checks the actual paths AutoCedar will use,
not just whatever happens to be first on the shell PATH.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from autocedar.env import find_dotenv
from autocedar.grounding import CEDAR_PATH, CVC5_PATH, _run_symcc
from autocedar.openai_compatible import list_openai_models
from autocedar.providers import (
    ProviderConfigurationError,
    create_backend,
    get_provider_definition,
    resolve_api_key,
    resolve_provider_config,
)
from autocedar.providers import ResolvedProviderConfig


@dataclass
class DoctorCheck:
    name: str
    status: str
    detail: str
    fix: str = ""


@dataclass
class DoctorReport:
    checks: list[DoctorCheck] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return any(check.status == "FAIL" for check in self.checks)

    @property
    def warned(self) -> bool:
        return any(check.status == "WARN" for check in self.checks)


def run_doctor(
    *,
    live_symcc: bool = True,
    cwd: Path | None = None,
    provider_config: ResolvedProviderConfig | None = None,
) -> DoctorReport:
    """Run local setup checks and return a structured report."""
    cwd = cwd or Path.cwd()
    report = DoctorReport()

    report.checks.append(DoctorCheck(
        name="Python",
        status="OK",
        detail=sys.version.split()[0],
    ))
    report.checks.append(_dotenv_check(cwd))
    report.checks.append(_llm_check(provider_config))
    report.checks.extend(_cedar_checks())
    report.checks.append(_cvc5_check())
    if live_symcc:
        report.checks.append(_symcc_smoke_check())
    return report


def format_doctor_report(report: DoctorReport) -> str:
    """Render a report for CLI output."""
    lines = ["AutoCedar doctor", ""]
    for check in report.checks:
        lines.append(f"[{check.status}] {check.name}: {check.detail}")
        if check.fix:
            lines.append(f"      fix: {check.fix}")
    lines.append("")
    if report.failed:
        lines.append("Result: FAIL. Fix the failed checks above, then rerun `uv run autocedar doctor`.")
    elif report.warned:
        lines.append("Result: OK with warnings. Verifier setup works, but review the warnings before authoring.")
    else:
        lines.append("Result: OK. AutoCedar verifier setup is ready.")
    return "\n".join(lines)


def _dotenv_check(cwd: Path) -> DoctorCheck:
    env_path = find_dotenv(cwd)
    if env_path is None:
        return DoctorCheck(
            name=".env",
            status="OK",
            detail="not found (optional); using saved settings, shell values, and defaults",
        )
    return DoctorCheck(name=".env", status="OK", detail=str(env_path))


def _llm_check(config: ResolvedProviderConfig | None = None) -> DoctorCheck:
    try:
        config = config or resolve_provider_config()
    except ProviderConfigurationError as exc:
        return DoctorCheck(
            name="LLM provider",
            status="FAIL",
            detail=str(exc),
            fix=(
                "run `autocedar config --provider codex`, or choose one of: "
                "codex, claude-cli, anthropic, openai, local"
            ),
        )
    provider = config.provider
    model = config.model
    if provider == "codex":
        executable = shutil.which("codex")
        if executable is None:
            return DoctorCheck(
                name="LLM provider",
                status="FAIL",
                detail=f"codex using model {model}; codex CLI is not on PATH",
                fix="install the Codex CLI, then run `autocedar auth login codex`",
            )
        status = _run_text([executable, "login", "status"], timeout=30)
        if status.returncode == 0:
            return DoctorCheck(
                name="LLM provider",
                status="OK",
                detail=f"codex using model {model}; {_compact(status.output) or 'CLI login available'}",
            )
        return DoctorCheck(
            name="LLM provider",
            status="FAIL",
            detail=f"codex using model {model}; {_compact(status.output) or 'not logged in'}",
            fix="run `autocedar auth login codex`, then retry `autocedar doctor`",
        )

    if provider == "claude-cli":
        try:
            backend = create_backend("claude-cli")
            status = backend.auth_status()  # type: ignore[attr-defined]
        except Exception as exc:
            return DoctorCheck(
                name="LLM provider",
                status="FAIL",
                detail=f"claude-cli using model {model}; {exc}",
                fix="install Claude Code, then run `autocedar auth login claude-cli`",
            )
        if status.logged_in:
            return DoctorCheck(
                name="LLM provider",
                status="OK",
                detail=f"claude-cli using model {model}; {status.auth_method or 'CLI login'}",
            )
        return DoctorCheck(
            name="LLM provider",
            status="FAIL",
            detail=f"claude-cli using model {model}; {status.error or 'not logged in'}",
            fix="run `autocedar auth login claude-cli`, then retry `autocedar doctor`",
        )

    if provider == "local":
        try:
            credential = resolve_api_key("local")
            local_key = credential.api_key
        except ProviderConfigurationError:
            local_key = None
        endpoint = config.base_url or "http://127.0.0.1:8000/v1"
        try:
            models = list_openai_models(
                base_url=endpoint,
                api_key=local_key,
                timeout=3.0,
            )
        except Exception as exc:
            return DoctorCheck(
                name="LLM provider",
                status="FAIL",
                detail=f"local using model {model}; server is not reachable at {endpoint}: {exc}",
                fix=(
                    "start the local server, confirm `/v1/models` responds, and run "
                    "`autocedar config --provider local --endpoint http://HOST:PORT/v1`"
                ),
            )
        if model not in models:
            return DoctorCheck(
                name="LLM provider",
                status="FAIL",
                detail=(
                    f"local server is reachable at {endpoint}, but model {model!r} "
                    f"is not advertised; available: {', '.join(models)}"
                ),
                fix=(
                    "confirm that the intended server owns this endpoint (a shared "
                    "machine may already have another server on that port), then run "
                    "`autocedar config --provider local --model MODEL` with an "
                    "advertised model or restart the intended server"
                ),
            )
        return DoctorCheck(
            name="LLM provider",
            status="OK",
            detail=f"local using model {model} at {endpoint}; available models: {', '.join(models)}",
        )

    try:
        credential = resolve_api_key(provider)
    except ProviderConfigurationError:
        credential = None
    definition = get_provider_definition(provider)
    if credential is not None and credential.api_key:
        return DoctorCheck(
            name="LLM provider",
            status="OK",
            detail=f"{provider} using model {model}; API key set from {credential.source}",
        )
    return DoctorCheck(
        name="LLM provider",
        status="WARN",
        detail=f"{provider} using model {model}; API key is not set",
        fix=f"run `autocedar auth login {provider}` for {definition.display_name}",
    )


def _cedar_checks() -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    cedar = Path(CEDAR_PATH).expanduser()
    if not cedar.exists():
        checks.append(DoctorCheck(
            name="Cedar CLI",
            status="FAIL",
            detail=f"not found at {cedar}",
            fix="run `autocedar setup`, or install with `cargo install cedar-policy-cli --locked --version 4.10.0 --features analyze --force`, or set `CEDAR=/path/to/cedar`",
        ))
        return checks
    if not os.access(cedar, os.X_OK):
        checks.append(DoctorCheck(
            name="Cedar CLI",
            status="FAIL",
            detail=f"not executable at {cedar}",
            fix=f"run `chmod +x {cedar}` or set `CEDAR=/path/to/cedar`",
        ))
        return checks

    version = _run_text([str(cedar), "--version"])
    if version.returncode == 0:
        checks.append(DoctorCheck(
            name="Cedar CLI",
            status="OK",
            detail=f"{cedar} ({_first_line(version.output)})",
        ))
    else:
        checks.append(DoctorCheck(
            name="Cedar CLI",
            status="FAIL",
            detail=f"{cedar} failed to run: {_compact(version.output)}",
            fix="set `CEDAR=/path/to/cedar` to a working Cedar CLI binary",
        ))
        return checks

    help_result = _run_text([str(cedar), "symcc", "--help"])
    required_flags = ("--principal-type", "--action", "--resource-type", "--schema")
    missing = [flag for flag in required_flags if flag not in help_result.output]
    if help_result.returncode == 0 and not missing:
        checks.append(DoctorCheck(
            name="Cedar SymCC interface",
            status="OK",
            detail="analysis flags are present",
        ))
    else:
        detail = _compact(help_result.output) or "symcc help produced no output"
        checks.append(DoctorCheck(
            name="Cedar SymCC interface",
            status="FAIL",
            detail=f"missing required analysis flags: {', '.join(missing) or detail}",
            fix="run `autocedar setup --yes` or `cargo install cedar-policy-cli --locked --version 4.10.0 --features analyze --force`, then confirm `cedar symcc --help | grep principal-type`",
        ))
    return checks


def _cvc5_check() -> DoctorCheck:
    cvc5 = Path(CVC5_PATH).expanduser()
    if not cvc5.exists():
        return DoctorCheck(
            name="CVC5",
            status="FAIL",
            detail=f"not found at {cvc5}",
            fix="run `autocedar setup`, or install CVC5 manually, confirm `cvc5 --version`, then set `CVC5=$(command -v cvc5)` in `.env` if needed",
        )
    if not os.access(cvc5, os.X_OK):
        return DoctorCheck(
            name="CVC5",
            status="FAIL",
            detail=f"not executable at {cvc5}",
            fix=f"run `chmod +x {cvc5}` or set `CVC5=/path/to/cvc5`",
        )
    version = _run_text([str(cvc5), "--version"])
    if version.returncode == 0:
        return DoctorCheck(
            name="CVC5",
            status="OK",
            detail=f"{cvc5} ({_first_line(version.output)})",
        )
    return DoctorCheck(
        name="CVC5",
        status="FAIL",
        detail=f"{cvc5} failed to run: {_compact(version.output)}",
        fix="install CVC5, confirm `cvc5 --version`, then set `CVC5=/path/to/cvc5`",
    )


def _symcc_smoke_check() -> DoctorCheck:
    """Verify AutoCedar's actual SymCC path on a tiny implication query."""
    with tempfile.TemporaryDirectory(prefix="autocedar-doctor-") as td:
        root = Path(td)
        schema = root / "schema.cedarschema"
        policy_a = root / "a.cedar"
        policy_b = root / "b.cedar"
        schema.write_text(
            "entity User;\n"
            "entity Document { owner: User };\n"
            "action viewDocument appliesTo { principal: [User], resource: [Document] };\n",
            encoding="utf-8",
        )
        policy = (
            'permit (principal, action == Action::"viewDocument", resource) '
            "when { principal == resource.owner };\n"
        )
        policy_a.write_text(policy, encoding="utf-8")
        policy_b.write_text(policy, encoding="utf-8")
        passed, output = _run_symcc(
            str(schema),
            "User",
            "viewDocument",
            "Document",
            "implies",
            ["--policies1", str(policy_a), "--policies2", str(policy_b)],
        )
    if passed:
        return DoctorCheck(
            name="Live SymCC smoke test",
            status="OK",
            detail="identical owner-view policy implies itself",
        )
    return DoctorCheck(
        name="Live SymCC smoke test",
        status="FAIL",
        detail=_compact(output),
        fix="fix the Cedar/CVC5 checks above; if they pass, rerun with `CEDAR_DEBUG=1` and report the raw output",
    )


@dataclass
class _RunResult:
    returncode: int
    output: str


def _run_text(cmd: list[str], timeout: int = 10) -> _RunResult:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return _RunResult(127, str(exc))
    except subprocess.TimeoutExpired:
        return _RunResult(124, "timed out")
    output = (result.stdout.strip() + "\n" + result.stderr.strip()).strip()
    return _RunResult(result.returncode, output)


def _first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _compact(text: str, limit: int = 420) -> str:
    compacted = " ".join(text.split())
    if len(compacted) <= limit:
        return compacted
    return compacted[: limit - 3].rstrip() + "..."
