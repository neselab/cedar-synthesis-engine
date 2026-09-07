"""Adapter from the HITL authoring pipeline to the packaged CEGIS harness."""

from __future__ import annotations

import contextlib
import io
import os
from collections.abc import Callable
from pathlib import Path


OutputCallback = Callable[[str], None]


class _ProgressStream(io.StringIO):
    """Forward complete lines while synthesis runs, including failure output."""

    def __init__(self, callback: OutputCallback | None) -> None:
        super().__init__()
        self.callback = callback
        self.pending = ""

    def write(self, text: str) -> int:
        if self.callback:
            self.pending += text
            while "\n" in self.pending:
                line, self.pending = self.pending.split("\n", 1)
                if line.strip():
                    self.callback(line)
        return len(text)

    def flush(self) -> None:
        if self.pending and self.callback:
            self.callback(self.pending)
            self.pending = ""


def make_harness_synthesizer(
    *,
    provider: str | None = None,
    phase1_model: str | None = None,
    phase2_model: str | None = None,
    max_iters: int | None = None,
    gen_references: bool = False,
    no_review: bool = True,
    quiet: bool = False,
    output_callback: OutputCallback | None = None,
) -> Callable[[Path], Path]:
    """Build a ``pipeline.author`` Stage 3 synthesizer.

    The HITL pipeline materializes a v1-harness-shaped scenario directory.
    This adapter runs the packaged CEGIS harness on that scenario and returns
    the actual ``candidate.cedar`` written by the harness. It raises if the
    harness errors or does not converge, so public authoring never silently
    accepts a placeholder candidate.
    """

    def synthesize(scenario_dir: Path) -> Path:
        from autocedar.harness.eval_harness import (
            DEFAULT_MODEL,
            DEFAULT_PHASE1_MODEL,
            MAX_ITERATIONS,
            run_scenario,
        )

        scenario_dir = Path(scenario_dir)
        run_dir = scenario_dir.parent / "harness_runs"
        run_dir.mkdir(parents=True, exist_ok=True)

        p1 = phase1_model or DEFAULT_PHASE1_MODEL
        p2 = phase2_model or DEFAULT_MODEL
        iters = max_iters or MAX_ITERATIONS

        if quiet or output_callback is not None:
            captured = _ProgressStream(output_callback)
            with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
                result = run_scenario(
                    scenario_path=os.path.abspath(scenario_dir),
                    run_dir=str(run_dir),
                    phase1_model=p1,
                    phase2_model=p2,
                    max_iters=iters,
                    gen_references=gen_references,
                    no_review=no_review,
                    provider=provider,
                    fixed_target=True,
                )
            captured.flush()
        else:
            result = run_scenario(
                scenario_path=os.path.abspath(scenario_dir),
                run_dir=str(run_dir),
                phase1_model=p1,
                phase2_model=p2,
                max_iters=iters,
                gen_references=gen_references,
                no_review=no_review,
                provider=provider,
                fixed_target=True,
            )

        candidate_path = run_dir / scenario_dir.name / "candidate.cedar"
        if result.error:
            raise RuntimeError(f"Stage 3 synthesis failed: {result.error}")
        if not result.converged:
            raise RuntimeError(
                "Stage 3 synthesis did not converge "
                f"(loss={result.final_loss}, "
                f"iters={result.iterations}/{result.max_iterations}). "
                f"Last candidate, if any: {candidate_path}",
            )
        if not candidate_path.exists():
            raise FileNotFoundError(
                f"Stage 3 reported convergence but did not write {candidate_path}",
            )
        return candidate_path

    return synthesize
