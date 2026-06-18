"""Guided installation for AutoCedar's external verifier tools."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from autocedar.grounding import CEDAR_PATH, CVC5_PATH

CEDAR_INSTALL_CMD = [
    "cargo",
    "install",
    "cedar-policy-cli",
    "--locked",
    "--version",
    "4.10.0",
    "--features",
    "analyze",
    "--force",
]


@dataclass
class SetupStep:
    name: str
    status: str
    detail: str
    command: list[str] | None = None


@dataclass
class SetupPlan:
    steps: list[SetupStep] = field(default_factory=list)

    @property
    def needs_install(self) -> bool:
        return any(step.status == "INSTALL" for step in self.steps)

    @property
    def blocked(self) -> bool:
        return any(step.status == "BLOCKED" for step in self.steps)


Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def build_setup_plan(
    *,
    install_cedar: bool = True,
    install_cvc5: bool = True,
) -> SetupPlan:
    """Detect missing verifier tools and return the install steps AutoCedar can run."""
    plan = SetupPlan()
    if install_cedar:
        plan.steps.append(_cedar_step())
    if install_cvc5:
        plan.steps.append(_cvc5_step())
    return plan


def run_setup_plan(plan: SetupPlan, *, runner: Runner | None = None) -> list[SetupStep]:
    """Run install steps from a plan and return per-step results."""
    runner = runner or _run_command
    results: list[SetupStep] = []
    for step in plan.steps:
        if step.status != "INSTALL" or step.command is None:
            results.append(step)
            continue
        completed = runner(step.command)
        if completed.returncode == 0:
            results.append(SetupStep(step.name, "OK", "installed", step.command))
        else:
            output = _compact((completed.stdout or "") + "\n" + (completed.stderr or ""))
            results.append(
                SetupStep(
                    step.name,
                    "FAIL",
                    output or f"command exited with {completed.returncode}",
                    step.command,
                )
            )
    return results


def format_setup_plan(plan: SetupPlan) -> str:
    lines = ["AutoCedar setup", ""]
    for step in plan.steps:
        lines.append(f"[{step.status}] {step.name}: {step.detail}")
        if step.command:
            lines.append(f"      run: {_quote(step.command)}")
    lines.append("")
    if plan.blocked:
        lines.append("Result: blocked. Install the blocked prerequisite, then rerun `autocedar setup`.")
    elif plan.needs_install:
        lines.append("Result: install steps are available. Run `autocedar setup --yes` to execute them.")
    else:
        lines.append("Result: verifier tools already appear to be installed. Run `autocedar doctor` to verify.")
    return "\n".join(lines)


def format_setup_results(results: list[SetupStep]) -> str:
    lines = ["AutoCedar setup results", ""]
    failed = False
    for step in results:
        lines.append(f"[{step.status}] {step.name}: {step.detail}")
        if step.status == "FAIL":
            failed = True
        if step.command:
            lines.append(f"      command: {_quote(step.command)}")
    lines.append("")
    if failed:
        lines.append("Result: setup failed. Fix the failed command, then rerun `autocedar doctor`.")
    else:
        lines.append("Result: setup commands finished. Run `autocedar doctor` to confirm the live toolchain.")
    return "\n".join(lines)


def _cedar_step() -> SetupStep:
    cedar = Path(CEDAR_PATH).expanduser()
    if cedar.exists() and os.access(cedar, os.X_OK):
        return SetupStep("Cedar CLI", "OK", f"found at {cedar}")
    if shutil.which("cargo") is None:
        return SetupStep(
            "Cedar CLI",
            "BLOCKED",
            "Cargo is not installed. Install Rust first: https://rustup.rs/",
        )
    return SetupStep(
        "Cedar CLI",
        "INSTALL",
        f"not found at {cedar}; install Cedar CLI 4.10.0 with SymCC analyze support",
        CEDAR_INSTALL_CMD,
    )


def _cvc5_step() -> SetupStep:
    cvc5 = Path(CVC5_PATH).expanduser()
    if cvc5.exists() and os.access(cvc5, os.X_OK):
        return SetupStep("CVC5", "OK", f"found at {cvc5}")

    system = platform.system().lower()
    if system == "darwin" and shutil.which("brew"):
        return SetupStep("CVC5", "INSTALL", f"not found at {cvc5}", ["brew", "install", "cvc5"])

    if system == "linux" and shutil.which("apt-get"):
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            command = ["apt-get", "install", "-y", "cvc5"]
        elif shutil.which("sudo"):
            command = ["sudo", "apt-get", "install", "-y", "cvc5"]
        else:
            command = None
        if command is not None:
            return SetupStep("CVC5", "INSTALL", f"not found at {cvc5}", command)

    return SetupStep(
        "CVC5",
        "BLOCKED",
        "CVC5 was not found and AutoCedar does not know a safe installer for this system. Install CVC5 manually, then set CVC5=/path/to/cvc5 if needed.",
    )


def _run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True)


def _quote(cmd: list[str]) -> str:
    return " ".join(cmd)


def _compact(text: str, limit: int = 500) -> str:
    compacted = " ".join(text.split())
    if len(compacted) <= limit:
        return compacted
    return compacted[: limit - 3].rstrip() + "..."
