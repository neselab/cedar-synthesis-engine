"""Unit tests for ``autocedar.property_elicitor``.

See ``docs/HITL_STEP_B_PLAN.md`` §9 acceptance criterion 4: sugar
compile-down produces byte-identical output for five golden inputs.
The five inputs are one per atom type (ceiling, floor, liveness,
rate_limit, disjointness).
"""

from __future__ import annotations

import textwrap

from autocedar.atoms import PropertyAtom, VerificationPlanDraft
from autocedar.property_elicitor import (
    compile_plan,
    compile_plan_for_consistency,
    insert_when_with_conjuncts,
    wrap_when_with_conjuncts,
)


# ---------------------------------------------------------------------------
# Cedar text manipulation primitives.
# ---------------------------------------------------------------------------

def test_wrap_when_simple_inline() -> None:
    p = 'permit (principal, action, resource) when { a == b };'
    out = wrap_when_with_conjuncts(p, ["c == d"])
    # Body wrapped in parens and patches appended on new lines.
    assert "(a == b)" in out
    assert "&& c == d" in out
    # Closing brace + semicolon preserved.
    assert out.endswith("};")


def test_wrap_when_multiline_body_preserved() -> None:
    p = textwrap.dedent("""\
        permit (
            principal is User,
            action == Action::"read",
            resource is Record
        )
        when {
            principal == resource.owner
            && resource.status == "active"
        };
    """)
    out = wrap_when_with_conjuncts(p, ['!(resource.legalHold && principal.role != "legal")'])
    # The inner body's && structure is preserved inside the wrapping parens.
    assert 'principal == resource.owner' in out
    assert 'resource.status == "active"' in out
    assert '&& !(resource.legalHold && principal.role != "legal")' in out


def test_wrap_with_no_conjuncts_is_identity() -> None:
    p = 'permit (principal, action, resource) when { a == b };'
    assert wrap_when_with_conjuncts(p, []) == p


def test_insert_when_into_unconditional_permit() -> None:
    p = 'permit (principal, action, resource);'
    out = insert_when_with_conjuncts(p, ["x == y"])
    assert "when {" in out
    assert "x == y" in out
    assert out.rstrip().endswith(";")


# ---------------------------------------------------------------------------
# Sugar compile-down — golden tests, one per atom type.
# ---------------------------------------------------------------------------

def _ceiling_atom() -> PropertyAtom:
    return PropertyAtom(
        name="careTeam_only_read",
        rationale="bound on read",
        plain_english_summary="Care-team-only read",
        source_excerpt="Doctors and nurses on the patient's care team can read records.",
        constraint_type="ceiling",
        action="read",
        principal_types=["User"],
        resource_types=["Record"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Record) '
            'when { resource.careTeamMembers.contains(principal) };'
        ),
    )


def _floor_atom() -> PropertyAtom:
    return PropertyAtom(
        name="admin_must_edit",
        rationale="admins must be permitted to edit",
        plain_english_summary="Admins must be permitted to edit",
        source_excerpt="Admins can edit any record.",
        constraint_type="floor",
        action="edit",
        principal_types=["User"],
        resource_types=["Record"],
        reference_cedar=(
            'permit (principal is User, action == Action::"edit", resource is Record) '
            'when { principal.role == "admin" };'
        ),
    )


def _liveness_atom() -> PropertyAtom:
    return PropertyAtom(
        name="liveness_read",
        rationale="at least one read permitted",
        plain_english_summary="At least one read request must be permitted",
        source_excerpt="(implicit liveness)",
        constraint_type="liveness",
        action="read",
        principal_types=["User"],
        resource_types=["Record"],
    )


def _rate_limit_atom() -> PropertyAtom:
    return PropertyAtom(
        name="bulkExport_rl_minute",
        rationale="100 bulkExports per minute per user",
        plain_english_summary="Bulk export limited to 100/min per user",
        source_excerpt="Bulk export is rate-limited to 100 requests per minute per user.",
        constraint_type="rate_limit",
        action="bulkExport",
        principal_types=["User"],
        resource_types=["Record"],
        reference_cedar=(
            'permit (principal is User, action == Action::"bulkExport", resource is Record) '
            'when { context.requestsPerMinute < 100 };'
        ),
        rate_limit_window="1m",
        rate_limit_threshold=100,
        rate_limit_counter_attr="requestsPerMinute",
    )


def _disjointness_atom() -> PropertyAtom:
    return PropertyAtom(
        name="legal_hold_disj",
        rationale="legal hold off-limits except legal team",
        plain_english_summary="Legal-hold records off-limits except for legal team",
        source_excerpt=(
            "Records under legal hold are completely off-limits — no one can "
            "read or edit them, including admins, unless they're specifically "
            "the legal team."
        ),
        constraint_type="disjointness",
        action="edit",  # same action as the floor, so §8.8 patch applies
        principal_types=["User"],
        resource_types=["Record"],
        reference_cedar=(
            'permit (principal is User, action == Action::"edit", resource is Record) '
            'when { !(resource.legalHold && principal.role != "legal") };'
        ),
        disjoint_with="non_legal_legal_hold_path",
        disjoint_target_body=(
            'resource.legalHold && principal.role != "legal"'
        ),
    )


def _scenario2_properties() -> list[PropertyAtom]:
    """Expected Scenario 2 shape from the project-tracker Cedar exercise."""
    return [
        PropertyAtom(
            name="view_requires_team_membership",
            rationale="view is limited to ticket team members",
            plain_english_summary="Only ticket team members can view a ticket.",
            source_excerpt=(
                "A user can view ... a ticket if they are a member of the "
                "ticket's team."
            ),
            constraint_type="ceiling",
            action="view",
            principal_types=["User"],
            resource_types=["Ticket"],
            reference_cedar=(
                'permit (principal is User, action == Action::"view", resource is Ticket) '
                "when { principal in resource.team };"
            ),
        ),
        PropertyAtom(
            name="view_allowed_for_team_member",
            rationale="team members must be able to view their tickets",
            plain_english_summary="Ticket team members can view a ticket.",
            source_excerpt=(
                "A user can view ... a ticket if they are a member of the "
                "ticket's team."
            ),
            constraint_type="floor",
            action="view",
            principal_types=["User"],
            resource_types=["Ticket"],
            reference_cedar=(
                'permit (principal is User, action == Action::"view", resource is Ticket) '
                "when { principal in resource.team };"
            ),
        ),
        PropertyAtom(
            name="comment_requires_team_membership",
            rationale="comment is limited to ticket team members",
            plain_english_summary="Only ticket team members can comment on a ticket.",
            source_excerpt=(
                "A user can ... comment on a ticket if they are a member of "
                "the ticket's team."
            ),
            constraint_type="ceiling",
            action="comment",
            principal_types=["User"],
            resource_types=["Ticket"],
            reference_cedar=(
                'permit (principal is User, action == Action::"comment", resource is Ticket) '
                "when { principal in resource.team };"
            ),
        ),
        PropertyAtom(
            name="comment_allowed_for_team_member",
            rationale="team members can comment subject to closed-ticket override",
            plain_english_summary="Ticket team members can comment on a ticket.",
            source_excerpt=(
                "A user can ... comment on a ticket if they are a member of "
                "the ticket's team."
            ),
            constraint_type="floor",
            action="comment",
            principal_types=["User"],
            resource_types=["Ticket"],
            reference_cedar=(
                'permit (principal is User, action == Action::"comment", resource is Ticket) '
                "when { principal in resource.team };"
            ),
        ),
        PropertyAtom(
            name="closed_ticket_comment_disjointness",
            rationale="closed tickets cannot be commented on by anyone",
            plain_english_summary="Closed tickets cannot be commented on.",
            source_excerpt="Closed tickets cannot be commented on by anyone.",
            constraint_type="disjointness",
            action="comment",
            principal_types=["User"],
            resource_types=["Ticket"],
            reference_cedar=(
                'permit (principal is User, action == Action::"comment", resource is Ticket) '
                'when { !(resource.status == "closed") };'
            ),
            disjoint_with="comment_closed_ticket_path",
            disjoint_target_body='resource.status == "closed"',
        ),
        PropertyAtom(
            name="close_exact_team_member_open",
            rationale="closing requires team membership and open status",
            plain_english_summary="Team members can close open tickets only.",
            source_excerpt=(
                "A user can close a ticket only if they are a member of the "
                "team and the ticket is currently open."
            ),
            constraint_type="ceiling",
            action="close",
            principal_types=["User"],
            resource_types=["Ticket"],
            reference_cedar=(
                'permit (principal is User, action == Action::"close", resource is Ticket) '
                'when { principal in resource.team && resource.status == "open" };'
            ),
        ),
        PropertyAtom(
            name="close_allowed_for_team_member_open",
            rationale="team members must be able to close open tickets",
            plain_english_summary="Team members can close open tickets.",
            source_excerpt=(
                "Carol asks to close an open Alpha ticket. Allowed — member, "
                "and the ticket is open."
            ),
            constraint_type="floor",
            action="close",
            principal_types=["User"],
            resource_types=["Ticket"],
            reference_cedar=(
                'permit (principal is User, action == Action::"close", resource is Ticket) '
                'when { principal in resource.team && resource.status == "open" };'
            ),
        ),
        PropertyAtom(
            name="comment_liveness_for_team_member_open",
            rationale="there should be at least one permitted team-member comment",
            plain_english_summary=(
                "At least one comment request by a team member on an open "
                "ticket should be permitted."
            ),
            source_excerpt="Carol comments on that same open Alpha ticket. Allowed.",
            constraint_type="liveness",
            action="comment",
            principal_types=["User"],
            resource_types=["Ticket"],
        ),
    ]


def test_ceiling_compiles_to_implies_with_reference_path() -> None:
    plan = VerificationPlanDraft(properties=[_ceiling_atom()])
    out = compile_plan(plan)
    assert "careTeam_only_read" in out.references
    assert '"type": "implies"' in out.verification_plan_py
    assert '"reference_path": os.path.join(REFS, "careTeam_only_read.cedar")' in out.verification_plan_py


def test_floor_compiles_to_floor_with_floor_path() -> None:
    plan = VerificationPlanDraft(properties=[_floor_atom()])
    out = compile_plan(plan)
    assert "admin_must_edit" in out.references
    assert '"type": "floor"' in out.verification_plan_py
    assert '"floor_path": os.path.join(REFS, "admin_must_edit.cedar")' in out.verification_plan_py


def test_liveness_compiles_with_no_reference_file() -> None:
    plan = VerificationPlanDraft(properties=[_liveness_atom()])
    out = compile_plan(plan)
    # No reference file emitted for liveness atoms.
    assert "liveness_read" not in out.references
    assert '"type": "always-denies-liveness"' in out.verification_plan_py
    # Liveness entries do NOT carry a reference_path or floor_path.
    assert '"reference_path"' not in out.verification_plan_py
    assert '"floor_path"' not in out.verification_plan_py


def test_liveness_probe_compiles_to_overlap_check_with_reference() -> None:
    atom = _liveness_atom()
    atom.reference_cedar = (
        'permit (principal is User, action == Action::"read", resource is Record) '
        'when { resource.careTeamMembers.contains(principal) };'
    )
    plan = VerificationPlanDraft(properties=[atom])
    out = compile_plan(plan)
    assert "liveness_read" in out.references
    assert '"type": "liveness-overlap"' in out.verification_plan_py
    assert '"reference_path": os.path.join(REFS, "liveness_read.cedar")' in out.verification_plan_py
    assert '"floor_path"' not in out.verification_plan_py


def test_rate_limit_compiles_to_implies() -> None:
    plan = VerificationPlanDraft(properties=[_rate_limit_atom()])
    out = compile_plan(plan)
    # Rate-limit atom resolves to a primitive ceiling (implies).
    assert '"type": "implies"' in out.verification_plan_py
    assert "bulkExport_rl_minute" in out.references
    # The reference body uses the context.<counter> < threshold form.
    assert "context.requestsPerMinute < 100" in out.references["bulkExport_rl_minute"]


def test_disjointness_compiles_to_implies_and_patches_floors_on_same_action() -> None:
    """The §8.8 patch test: a disjointness atom on action ``edit`` must
    inject ``&& !(disjoint_target_body)`` into every floor on ``edit``."""
    plan = VerificationPlanDraft(
        properties=[
            _floor_atom(),  # floor on `edit`
            _disjointness_atom(),  # disjointness on `edit`
        ],
    )
    out = compile_plan(plan)

    # The disjointness atom itself compiles to a ceiling (implies).
    assert "legal_hold_disj" in out.references
    assert '"name": "legal_hold_disj"' in out.verification_plan_py
    # The floor on the same action gets the negated patch appended.
    floor_text = out.references["admin_must_edit"]
    assert 'principal.role == "admin"' in floor_text
    assert '!(resource.legalHold && principal.role != "legal")' in floor_text


def test_consistency_plan_uses_patched_floors_and_skips_raw_disjointness() -> None:
    plan = VerificationPlanDraft(
        properties=[
            _floor_atom(),
            _disjointness_atom(),
        ],
    )

    consistency_plan = compile_plan_for_consistency(plan)

    assert [atom.name for atom in consistency_plan.properties] == ["admin_must_edit"]
    floor = consistency_plan.properties[0]
    assert floor.constraint_type == "floor"
    assert 'principal.role == "admin"' in floor.reference_cedar
    assert '!(resource.legalHold && principal.role != "legal")' in floor.reference_cedar


def test_disjointness_does_not_patch_floors_on_other_actions() -> None:
    """A disjointness atom on action ``edit`` must NOT touch floors on ``read``."""
    read_floor = PropertyAtom(
        name="read_must_permit_owner",
        rationale="...",
        plain_english_summary="...",
        source_excerpt="...",
        constraint_type="floor",
        action="read",
        principal_types=["User"],
        resource_types=["Record"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Record) '
            "when { principal == resource.owner };"
        ),
    )
    plan = VerificationPlanDraft(
        properties=[read_floor, _disjointness_atom()],
    )
    out = compile_plan(plan)
    # The read floor should be unchanged — no disjointness patch.
    read_floor_text = out.references["read_must_permit_owner"]
    assert "legalHold" not in read_floor_text


def test_scenario2_uses_disjointness_for_closed_ticket_override() -> None:
    """Scenario 2 should preserve the deny-override intent.

    The source exercise teaches that "closed tickets cannot be commented on"
    overrides the member-comment permission. AutoCedar should represent that as
    a disjointness property, which compiles to a ceiling and patches same-action
    comment floors.
    """
    properties = _scenario2_properties()
    plan = VerificationPlanDraft(properties=properties)
    out = compile_plan(plan)

    assert "closed_ticket_comment_disjointness" in out.references
    assert '"name": "closed_ticket_comment_disjointness"' in out.verification_plan_py
    assert '"type": "implies"' in out.verification_plan_py

    comment_floor = out.references["comment_allowed_for_team_member"]
    assert "principal in resource.team" in comment_floor
    assert '!(resource.status == "closed")' in comment_floor

    liveness_shapes = [
        (atom.action, tuple(atom.principal_types), tuple(atom.resource_types))
        for atom in properties
        if atom.constraint_type == "liveness"
    ]
    assert len(liveness_shapes) == len(set(liveness_shapes))


def test_full_five_atom_plan_compiles_deterministically() -> None:
    """Combined run with one of every atom type. Output must be deterministic."""
    plan = VerificationPlanDraft(
        properties=[
            _ceiling_atom(),
            _floor_atom(),
            _liveness_atom(),
            _rate_limit_atom(),
            _disjointness_atom(),
        ],
    )
    out_a = compile_plan(plan)
    out_b = compile_plan(plan)
    assert out_a.verification_plan_py == out_b.verification_plan_py
    assert out_a.references == out_b.references

    # All non-liveness atoms have a reference file.
    assert set(out_a.references) == {
        "careTeam_only_read",
        "admin_must_edit",
        "bulkExport_rl_minute",
        "legal_hold_disj",
    }
    # The plan file references each non-liveness atom and lists the liveness one.
    for name in (
        "careTeam_only_read",
        "admin_must_edit",
        "liveness_read",
        "bulkExport_rl_minute",
        "legal_hold_disj",
    ):
        assert f'"name": "{name}"' in out_a.verification_plan_py
