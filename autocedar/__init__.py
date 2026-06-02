"""HITL production agent for Cedar policy authoring.

See ``docs/HITL_STEP_B_PLAN.md`` for the implementation contract.
The package is organized as:

- ``atoms``: dataclasses for schema and property atoms (Stage 1 / Stage 2).
- ``property_elicitor``: Stage 2 (sugar compile-down).
- ``grounding``: symbolic verification + adversarial-example pipeline.
- ``schema_atomizer``: Stage 1 (LLM-driven; integrated in Step C).
- ``critic``: Stage 3 quality scorer with strict prompt boundary.
- ``corpus``: session log writer.
- ``pipeline``: orchestrates Stages 1, 1.5, 2, 1.75, 3, 2.5.
- ``ui``: terminal review UI and persistence.
- ``tui``: Textual-based interactive agent shell.
- ``harness``: packaged namespace for the v1 CEGIS harness.

Root-level ``eval_harness.py``, ``orchestrator.py``, and
``solver_wrapper.py`` remain as backwards-compatible scripts. New package
imports should use ``autocedar.harness``.
"""

__version__ = "0.1.0"
