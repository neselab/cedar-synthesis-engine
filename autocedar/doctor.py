"""Environment preflight checks for AutoCedar.

The doctor command makes verifier setup failures explicit before a user
enters an authoring session. It checks the actual paths AutoCedar will use,
not just whatever happens to be first on the shell PATH.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from autocedar.codex_auth import codex_runtime_info, is_codex_provider
from autocedar.env import ANTHROPIC_API_KEY, find_dotenv, is_real_anthropic_api_key
from autocedar.grounding import CEDAR_PATH, CVC5_PATH, _run_symcc
from autocedar.llm import default_model_for_provider, default_provider


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


def run_doctor(*, live_symcc: bool = True, cwd: Path | None = None) -> DoctorReport:
    """Run local setup checks and return a structured report."""
    cwd = cwd or Path.cwd()
    report = DoctorReport()

    report.checks.append(DoctorCheck(
        name="Python",
        status="OK",
        detail=sys.version.split()[0],
    ))
    report.checks.append(_dotenv_check(cwd))
    report.checks.append(_llm_check())
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
            status="WARN",
            detail="not found; shell environment will be used",
            fix="copy `.env.example` to `.env` or export the needed variables in your shell",
        )
    return DoctorCheck(name=".env", status="OK", detail=str(env_path))


def _llm_check() -> DoctorCheck:
    provider = default_provider()
    model = default_model_for_provider(provider)
    if is_codex_provider(provider):
        info = codex_runtime_info()
        if info.auth_available:
            visible = ", ".join(info.models[:6])
            if len(info.models) > 6:
                visible += ", ..."
            return DoctorCheck(
                name="LLM provider",
                status="OK",
                detail=(
                    f"{provider} using model {model}; Codex OAuth found at "
                    f"{info.auth_source}; visible models: {visible}"
                ),
            )
        return DoctorCheck(
            name="LLM provider",
            status="FAIL",
            detail=f"{provider} using model {model}; Codex OAuth is not available at {info.auth_source}",
            fix="run `codex login`, then retry `autocedar doctor` or use `/provider anthropic` with `/apikey`",
        )

    if is_real_anthropic_api_key(os.environ.get(ANTHROPIC_API_KEY)):
        return DoctorCheck(
            name="LLM provider",
            status="OK",
            detail=f"{provider} using model {model}; {ANTHROPIC_API_KEY} is set",
        )
    return DoctorCheck(
        name="LLM provider",
        status="WARN",
        detail=f"{provider} using model {model}; {ANTHROPIC_API_KEY} is not set",
        fix="run `autocedar apikey`, export `ANTHROPIC_API_KEY`, or use `/apikey` inside the TUI",
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
