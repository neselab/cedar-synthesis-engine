"""Tests for ``autocedar.critic``.

Covers acceptance criterion 7 of ``docs/HITL_STEP_B_PLAN.md`` §9 —
the critic prompt boundary.
"""

from __future__ import annotations

import inspect
import json

import pytest

from autocedar.critic import (
    CRITIC_DIMENSIONS,
    CRITIC_STYLE_GUIDE,
    CriticScore,
    build_critic_prompt,
    parse_critic_response,
    score_candidate,
    stub_llm_scorer,
)


# ---------------------------------------------------------------------------
# Acceptance criterion 7 — boundary test.
# ---------------------------------------------------------------------------

def test_build_critic_prompt_signature_only_takes_candidate_text() -> None:
    """The boundary that enforces §7.5.1 lives in the function signature.

    The critic prompt builder must accept exactly one parameter — the
    candidate Cedar text — so it cannot accidentally include the
    verification plan, the spec, or verifier feedback.
    """
    sig = inspect.signature(build_critic_prompt)
    parameter_names = list(sig.parameters)
    assert parameter_names == ["candidate_cedar"], (
        f"build_critic_prompt must take only candidate_cedar; "
        f"got parameters {parameter_names}"
    )


def test_build_critic_prompt_includes_candidate_and_style_guide() -> None:
    candidate = (
        'permit (principal is User, action == Action::"read", resource is Resource)\n'
        "when { principal == resource.owner };\n"
    )
    prompt = build_critic_prompt(candidate)
    assert candidate in prompt
    # The constant style guide appears verbatim (or at least the title line).
    assert "Cedar style guide" in prompt
    assert CRITIC_STYLE_GUIDE.splitlines()[0] in prompt


def test_build_critic_prompt_does_not_leak_unrelated_strings() -> None:
    """Defensive: the prompt the candidate gets is JUST the candidate +
    style guide. Strings that look like verification feedback or spec
    excerpts must not appear unless the candidate itself contains them.

    This guards against future refactors where someone might thread
    an extra parameter into the prompt builder via a global or default.
    """
    candidate = (
        'permit (principal is User, action == Action::"read", resource is Resource);\n'
    )
    prompt = build_critic_prompt(candidate)
    # Nothing the test passes outside the candidate should appear.
    assert "verification plan" not in prompt.lower() or (
        "the verification" in CRITIC_STYLE_GUIDE.lower()
    )
    # In particular, no spec-shaped sentences leak in.
    assert "Doctors and nurses" not in prompt
    assert "HR can view" not in prompt
    assert "ceiling implies" not in prompt
    assert "iteration 1" not in prompt
    assert "verifier feedback" not in prompt


# ---------------------------------------------------------------------------
# CriticScore dataclass behavior.
# ---------------------------------------------------------------------------

def test_critic_score_validates_range() -> None:
    with pytest.raises(ValueError):
        CriticScore(idiomatic=6, minimal=4, attribute_prefer=4, maintainable=4)
    with pytest.raises(ValueError):
        CriticScore(idiomatic=4, minimal=0, attribute_prefer=4, maintainable=4)


def test_critic_score_passes_threshold_default() -> None:
    s = CriticScore(idiomatic=5, minimal=4, attribute_prefer=4, maintainable=4)
    assert s.passes_threshold()


def test_critic_score_fails_threshold_when_one_dim_too_low() -> None:
    """Default threshold per §7.5.2: no single dim < 3."""
    s = CriticScore(idiomatic=5, minimal=5, attribute_prefer=2, maintainable=5)
    # Mean is 4.25 (≥ 4) BUT attribute_prefer=2 falls below the min=3 floor.
    assert not s.passes_threshold()


def test_critic_score_fails_threshold_when_mean_too_low() -> None:
    s = CriticScore(idiomatic=3, minimal=3, attribute_prefer=3, maintainable=3)
    assert not s.passes_threshold()


# ---------------------------------------------------------------------------
# Response parser.
# ---------------------------------------------------------------------------

def test_parse_critic_response_with_code_fence() -> None:
    response = (
        "Here are the scores:\n"
        "```json\n"
        + json.dumps(
            {
                "idiomatic": {"score": 5, "rationale": "..."},
                "minimal": {"score": 4, "rationale": "..."},
                "attribute_prefer": {"score": 4, "rationale": "..."},
                "maintainable": {"score": 4, "rationale": "..."},
            },
        )
        + "\n```"
    )
    s = parse_critic_response(response)
    assert s.idiomatic == 5
    assert s.composite_mean > 4.0


def test_parse_critic_response_with_bare_json() -> None:
    response = json.dumps(
        {
            "idiomatic": 5,
            "minimal": 4,
            "attribute_prefer": 4,
            "maintainable": 4,
        },
    )
    s = parse_critic_response(response)
    assert s.idiomatic == 5
    assert s.minimal == 4


def test_parse_critic_response_rejects_out_of_range() -> None:
    response = json.dumps(
        {
            "idiomatic": 9,  # invalid
            "minimal": 4,
            "attribute_prefer": 4,
            "maintainable": 4,
        },
    )
    with pytest.raises(ValueError):
        parse_critic_response(response)


def test_parse_critic_response_rejects_missing_dimension() -> None:
    response = json.dumps(
        {
            "idiomatic": 4,
            "minimal": 4,
            "attribute_prefer": 4,
            # missing: maintainable
        },
    )
    with pytest.raises(ValueError):
        parse_critic_response(response)


# ---------------------------------------------------------------------------
# End-to-end: score_candidate with stub.
# ---------------------------------------------------------------------------

def test_score_candidate_with_stub_returns_valid_score() -> None:
    candidate = (
        'permit (principal is User, action == Action::"read", resource is Resource);\n'
    )
    s = score_candidate(candidate, llm=stub_llm_scorer)
    assert all(getattr(s, d) in range(1, 6) for d in CRITIC_DIMENSIONS)


def test_score_candidate_with_custom_llm() -> None:
    """The pluggable LLMScorer interface accepts a real model-backed scorer."""
    high_quality_response = json.dumps(
        {
            "idiomatic": 5,
            "minimal": 5,
            "attribute_prefer": 5,
            "maintainable": 5,
        },
    )
    s = score_candidate("permit (...);", llm=lambda prompt: high_quality_response)
    assert s.composite_mean == 5.0
    assert s.passes_threshold()
