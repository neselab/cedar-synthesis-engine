"""Unit tests for ``autocedar.cedar_text``: cutting Cedar text into policies
and clauses without Cedar's JSON form."""

from __future__ import annotations

import pytest

from autocedar.cedar_text import is_template, policy_conditions, split_policies


def test_policies_end_only_at_semicolons_outside_strings_and_comments() -> None:
    text = (
        "// permit (principal, action, resource); is not a policy\n"
        '@id("a;b") permit (principal, action, resource) when { "x;\\"y" != "" };\n'
        "forbid (principal, action, resource); // trailing ; comment\n"
    )

    assert split_policies(text) == [
        '@id("a;b") permit (principal, action, resource) when { "x;\\"y" != "" };',
        "forbid (principal, action, resource);",
    ]


def test_conditions_are_the_clauses_after_the_scope() -> None:
    policy = (
        '@reason("permit (x)") permit (principal == User::"a)b", action, resource)\n'
        'when { "(" != ")" } unless { false };'
    )

    assert policy_conditions(policy) == 'when { "(" != ")" } unless { false }'
    assert policy_conditions("permit (principal, action, resource);") == ""


def test_slots_mark_templates_but_question_marks_in_strings_do_not() -> None:
    assert is_template("permit (principal == ?principal, action, resource);")
    assert not is_template('permit (principal, action, resource) when { "?" == "?" };')


def test_policy_without_a_scope_is_an_error() -> None:
    with pytest.raises(ValueError):
        policy_conditions('when { true };')
