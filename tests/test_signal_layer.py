from autocedar.harness.eval_harness import _format_signal_diagnostics
from autocedar.harness.solver_wrapper import CheckResult


def test_signal_diagnostics_show_generic_session_binding_delta(tmp_path):
    ref = tmp_path / "viewer_floor.cedar"
    ref.write_text(
        'permit (principal is User, action == Action::"viewProject", '
        "resource is Project) when { context.session.isActive && "
        "context.session.actor == principal && "
        "resource.approvedViewers.contains(principal) };\n"
    )
    candidate = (
        'permit (principal is User, action == Action::"viewProject", '
        "resource is Project) when { context.session.isActive && "
        "context.session has account && context.session.account == principal && "
        "resource.approvedViewers.contains(principal) };\n"
    )
    result = CheckResult(
        check_name="approved_viewer_floor",
        check_type="floor",
        description="Approved viewers can view projects.",
        passed=False,
        counterexample="",
    )
    check_def = {
        "name": "approved_viewer_floor",
        "type": "floor",
        "description": "Approved viewers can view projects.",
        "floor_path": str(ref),
    }

    rendered = "\n".join(_format_signal_diagnostics(result, check_def, candidate))

    assert "session-binding mismatch" in rendered
    assert "context.session.actor == principal" in rendered
    assert "context.session.account == principal" in rendered
    assert "Candidate/reference diff" in rendered
