// Floor: a TA whose dept matches the exam subject MUST be permitted
// to addComment. Note the symmetry with `ta_view_own_subject` —
// addComment and viewGrade have the SAME subject-scoped TA rule, but
// editGrade has NO permit path for TAs (other than instructor-bypass).
// The synthesizer must not collapse these three actions into a single
// rule.
permit (
    principal is User,
    action == Action::"addComment",
    resource is Exam
)
when {
    principal.role == "ta"
    && principal.dept == resource.subject
};
