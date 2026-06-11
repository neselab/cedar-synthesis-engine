from __future__ import annotations

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
