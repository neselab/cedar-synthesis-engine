from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import autocedar.setup_tools as setup_tools


def test_setup_plan_blocks_cedar_when_cargo_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(setup_tools, "CEDAR_PATH", str(tmp_path / "missing-cedar"))
    monkeypatch.setattr(setup_tools, "CVC5_PATH", str(tmp_path / "missing-cvc5"))
    monkeypatch.setattr(setup_tools.shutil, "which", lambda name: None)

    plan = setup_tools.build_setup_plan(install_cvc5=False)

    assert plan.blocked is True
    assert plan.steps[0].name == "Cedar CLI"
    assert plan.steps[0].status == "BLOCKED"
    assert "Cargo" in plan.steps[0].detail


def test_setup_plan_installs_cedar_with_analyze_feature(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(setup_tools, "CEDAR_PATH", str(tmp_path / "missing-cedar"))
    monkeypatch.setattr(setup_tools.shutil, "which", lambda name: "/usr/bin/cargo" if name == "cargo" else None)

    plan = setup_tools.build_setup_plan(install_cvc5=False)

    assert plan.needs_install is True
    assert plan.steps[0].command is not None
    assert "--features" in plan.steps[0].command
    assert "analyze" in plan.steps[0].command


def test_setup_plan_uses_brew_for_cvc5_on_macos(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(setup_tools, "CVC5_PATH", str(tmp_path / "missing-cvc5"))
    monkeypatch.setattr(setup_tools.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(setup_tools.shutil, "which", lambda name: "/opt/homebrew/bin/brew" if name == "brew" else None)

    plan = setup_tools.build_setup_plan(install_cedar=False)

    assert plan.steps[0].status == "INSTALL"
    assert plan.steps[0].command == ["brew", "install", "cvc5"]


def test_run_setup_plan_only_runs_install_steps() -> None:
    plan = setup_tools.SetupPlan([
        setup_tools.SetupStep("already", "OK", "present"),
        setup_tools.SetupStep("install", "INSTALL", "missing", ["tool", "install"]),
    ])
    seen: list[list[str]] = []

    def fake_runner(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        seen.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "ok", "")

    results = setup_tools.run_setup_plan(plan, runner=fake_runner)

    assert seen == [["tool", "install"]]
    assert [step.status for step in results] == ["OK", "OK"]
