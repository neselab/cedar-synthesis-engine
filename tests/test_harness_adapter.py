from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from autocedar.harness_adapter import make_harness_synthesizer


def test_harness_synthesizer_returns_actual_candidate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    scenario = tmp_path / "scenario"
    scenario.mkdir()

    calls: dict[str, object] = {}

    def fake_run_scenario(**kwargs: object) -> SimpleNamespace:
        calls.update(kwargs)
        run_dir = Path(str(kwargs["run_dir"]))
        scenario_path = Path(str(kwargs["scenario_path"]))
        workspace = run_dir / scenario_path.name
        workspace.mkdir(parents=True)
        (workspace / "candidate.cedar").write_text("permit (principal, action, resource);\n")
        return SimpleNamespace(
            converged=True,
            error="",
            final_loss=0,
            iterations=1,
            max_iterations=3,
        )

    import autocedar.harness.eval_harness as eval_harness

    monkeypatch.setattr(eval_harness, "run_scenario", fake_run_scenario)

    synthesize = make_harness_synthesizer(
        phase1_model="phase-one",
        phase2_model="phase-two",
        max_iters=3,
        quiet=True,
    )
    candidate = synthesize(scenario)

    assert candidate == scenario.parent / "harness_runs" / "scenario" / "candidate.cedar"
    assert candidate.read_text() == "permit (principal, action, resource);\n"
    assert calls["phase1_model"] == "phase-one"
    assert calls["phase2_model"] == "phase-two"
    assert calls["max_iters"] == 3
    assert calls["gen_references"] is False
    assert calls["no_review"] is True


def test_harness_synthesizer_rejects_non_convergence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    scenario = tmp_path / "scenario"
    scenario.mkdir()

    def fake_run_scenario(**kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            converged=False,
            error="",
            final_loss=2,
            iterations=3,
            max_iterations=3,
        )

    import autocedar.harness.eval_harness as eval_harness

    monkeypatch.setattr(eval_harness, "run_scenario", fake_run_scenario)

    synthesize = make_harness_synthesizer(max_iters=3, quiet=True)
    with pytest.raises(RuntimeError, match="did not converge"):
        synthesize(scenario)


def test_harness_symcc_retries_without_cvc5_path_when_cedar_rejects_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import autocedar.harness.solver_wrapper as solver_wrapper

    calls: list[list[str]] = []

    def fake_run(
        cmd: list[str],
        *,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        _ = capture_output, text, timeout
        calls.append(cmd)
        if "--cvc5-path" in cmd:
            return subprocess.CompletedProcess(
                cmd,
                2,
                "",
                "error: unexpected argument '--cvc5-path' found\nUsage: cedar symcc",
            )
        return subprocess.CompletedProcess(cmd, 0, "VERIFIED", "")

    monkeypatch.setattr(solver_wrapper.subprocess, "run", fake_run)

    passed, output = solver_wrapper._run_symcc(
        "schema.cedarschema",
        "User",
        'Action::"read"',
        "Resource",
        "implies",
        ["--policies1", "a.cedar", "--policies2", "b.cedar"],
    )

    assert passed is True
    assert output == "VERIFIED"
    assert "--cvc5-path" in calls[0]
    assert "--cvc5-path" not in calls[1]


def test_harness_symcc_reports_cli_without_analyze_feature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import autocedar.harness.solver_wrapper as solver_wrapper

    calls: list[list[str]] = []

    def fake_run(
        cmd: list[str],
        *,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        _ = capture_output, text, timeout
        calls.append(cmd)
        if "--cvc5-path" in cmd:
            return subprocess.CompletedProcess(
                cmd,
                2,
                "",
                "error: unexpected argument '--cvc5-path' found\nUsage: cedar symcc",
            )
        return subprocess.CompletedProcess(
            cmd,
            2,
            "",
            "Cannot run `symcc`: this Cedar CLI was built without the `analyze` feature enabled",
        )

    monkeypatch.setattr(solver_wrapper.subprocess, "run", fake_run)

    passed, output = solver_wrapper._run_symcc(
        "schema.cedarschema",
        "User",
        'Action::"read"',
        "Resource",
        "implies",
        ["--policies1", "a.cedar", "--policies2", "b.cedar"],
    )

    assert passed is False
    assert "Cedar symcc setup error" in output
    assert "--features analyze" in output
    assert "built without the `analyze` feature" in output
    assert "--cvc5-path" in calls[0]
    assert "--cvc5-path" not in calls[1]


def test_harness_symcc_reports_missing_cvc5_as_setup_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import autocedar.harness.solver_wrapper as solver_wrapper

    def fake_run(
        cmd: list[str],
        *,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        _ = capture_output, text, timeout
        return subprocess.CompletedProcess(
            cmd,
            1,
            "",
            "Analysis failed: CVC5 solver not found or failed to start at "
            "'/home/twinm/.local/bin/cvc5': IO error during a solver operation",
        )

    monkeypatch.setattr(solver_wrapper.subprocess, "run", fake_run)

    passed, output = solver_wrapper._run_symcc(
        "schema.cedarschema",
        "User",
        'Action::"read"',
        "Resource",
        "implies",
        ["--policies1", "a.cedar", "--policies2", "b.cedar"],
    )

    assert passed is False
    assert "Cedar symcc setup error" in output
    assert "CVC5 solver was not found" in output
    assert "CVC5=/path/to/cvc5" in output


def test_harness_symcc_classifies_nonformal_nonzero_exit_as_setup_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import autocedar.harness.solver_wrapper as solver_wrapper

    def fake_run(
        cmd: list[str],
        *,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        _ = capture_output, text, timeout
        return subprocess.CompletedProcess(cmd, 1, "", "internal solver transport error")

    monkeypatch.setattr(solver_wrapper.subprocess, "run", fake_run)

    passed, output = solver_wrapper._run_symcc(
        "schema.cedarschema",
        "User",
        'Action::"read"',
        "Resource",
        "implies",
        ["--policies1", "a.cedar", "--policies2", "b.cedar"],
    )

    assert passed is False
    assert "exited before producing a formal verification result" in output
    assert "not a policy counterexample" in output
