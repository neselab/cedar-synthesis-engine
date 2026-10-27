"""Untyped atoms fail admission instead of crashing a run, and synthesis
rejects candidates that can raise a Cedar evaluation error."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from autocedar.atoms import PropertyAtom, VerificationPlanDraft
from autocedar.grounding import CEDAR_PATH, CVC5_PATH, symbolic_verify_atom
from autocedar.harness import eval_harness as harness
from autocedar.harness.orchestrator import load_checks, run_verification
from autocedar.property_elicitor import compile_plan

requires_solvers = pytest.mark.skipif(
    not (os.access(CEDAR_PATH, os.X_OK) and os.access(CVC5_PATH, os.X_OK)),
    reason="Cedar/CVC5 not available",
)

SCHEMA = textwrap.dedent("""\
    entity User;
    entity Release { releaseDate: datetime };
    action view appliesTo { principal: [User], resource: [Release], context: { now: datetime } };
""")


def test_untyped_atom_fails_admission_without_raising(tmp_path: Path) -> None:
    schema = tmp_path / "schema.cedarschema"
    schema.write_text(SCHEMA)
    atom = PropertyAtom(
        name="deny_unlisted_actions",
        rationale="default deny",
        plain_english_summary="No other actions are allowed.",
        source_excerpt="Only the listed actions are permitted.",
        constraint_type="ceiling",
        action="",
        reference_cedar='permit (principal, action == Action::"view", resource);',
    )

    result = symbolic_verify_atom(atom, str(schema))

    assert not atom.symbolic_verified
    assert [c.name for c in result.checks] == ["typed-scope"]
    detail = result.checks[0].detail
    assert "an action or principal types or resource types" in detail
    assert "already denies" in detail


def _workspace(tmp_path: Path, candidate: str) -> Path:
    ceiling = PropertyAtom(
        name="released_or_day_before",
        rationale="window",
        plain_english_summary="Viewing opens 24 hours before release.",
        source_excerpt="Users can view a release from 24 hours before its release date.",
        constraint_type="ceiling",
        action="view",
        principal_types=["User"],
        resource_types=["Release"],
        reference_cedar='permit (principal, action == Action::"view", resource is Release);',
    )
    out = compile_plan(VerificationPlanDraft(properties=[ceiling]))
    (tmp_path / "references").mkdir()
    for name, text in out.references.items():
        (tmp_path / "references" / f"{name}.cedar").write_text(text)
    (tmp_path / "verification_plan.py").write_text(out.verification_plan_py)
    (tmp_path / "schema.cedarschema").write_text(SCHEMA)
    (tmp_path / "candidate.cedar").write_text(candidate)
    return tmp_path


@requires_solvers
def test_synthesis_rejects_candidate_that_can_overflow(tmp_path: Path) -> None:
    ws = _workspace(
        tmp_path,
        'permit (principal, action == Action::"view", resource) '
        'when { context.now >= resource.releaseDate.offset(duration("-24h")) };',
    )

    vr = run_verification(str(ws))

    failed = [r for r in vr.results if not r.passed]
    assert [r.check_name for r in failed] == ["no_runtime_errors__view__User__Release"]
    feedback = harness._format_feedback(vr, load_checks(str(ws)))
    assert "can raise an evaluation error" in feedback
    assert "short-circuits" in feedback


@requires_solvers
def test_guarded_datetime_arithmetic_passes(tmp_path: Path) -> None:
    ws = _workspace(
        tmp_path,
        'permit (principal, action == Action::"view", resource) when { '
        'resource.releaseDate > datetime("1970-01-02T00:00:00Z") && '
        'context.now >= resource.releaseDate.offset(duration("-24h")) };',
    )

    assert run_verification(str(ws)).loss == 0


@requires_solvers
def test_each_rule_is_checked_and_the_risky_one_is_named(tmp_path: Path) -> None:
    ws = _workspace(
        tmp_path,
        '// a comment with ; and { braces }\n'
        'permit (principal, action == Action::"view", resource) '
        'when { context.now >= resource.releaseDate };\n'
        'permit (principal, action == Action::"view", resource) '
        'when { "a;b{" != "" && context.now >= resource.releaseDate.offset(duration("-24h")) };\n',
    )

    vr = run_verification(str(ws))

    failed = [r for r in vr.results if not r.passed]
    assert [r.check_name for r in failed] == ["no_runtime_errors__view__User__Release"]
    assert not failed[0].tool_error
    assert failed[0].counterexample.startswith("Rule 2 of 2:")
    assert 'duration("-24h")' in failed[0].counterexample


@requires_solvers
def test_several_safe_rules_pass(tmp_path: Path) -> None:
    ws = _workspace(
        tmp_path,
        'permit (principal, action == Action::"view", resource) '
        'when { context.now >= resource.releaseDate };\n'
        'forbid (principal, action == Action::"view", resource) when { false };\n',
    )

    assert run_verification(str(ws)).loss == 0


@requires_solvers
def test_atom_with_several_policies_gets_a_real_never_errors_verdict(tmp_path: Path) -> None:
    schema = tmp_path / "schema.cedarschema"
    schema.write_text(SCHEMA)
    atom = PropertyAtom(
        name="view_window",
        rationale="window",
        plain_english_summary="View after release, or by guarded early access.",
        source_excerpt="Users can view a release after its release date.",
        constraint_type="ceiling",
        action="view",
        principal_types=["User"],
        resource_types=["Release"],
        reference_cedar=(
            'permit (principal, action == Action::"view", resource is Release) '
            "when { context.now >= resource.releaseDate };\n"
            'permit (principal, action == Action::"view", resource is Release) when { '
            'resource.releaseDate > datetime("1970-01-02T00:00:00Z") && '
            'context.now >= resource.releaseDate.offset(duration("-24h")) };'
        ),
    )

    symbolic_verify_atom(atom, str(schema))

    assert "never-errors: ok" in "\n".join(atom.symbolic_verification_log)
