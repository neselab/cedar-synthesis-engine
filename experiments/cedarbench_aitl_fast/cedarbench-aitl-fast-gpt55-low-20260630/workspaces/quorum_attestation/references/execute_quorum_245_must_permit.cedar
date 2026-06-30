// Floor for executeEmergency with quorum {s2,s4,s5}.
// A "non-adjacent" subset to catch candidates that only emit
// contiguous/sorted disjuncts. When attesters contains at least
// {s2,s4,s5} and the principal is one of the five eligible approvers,
// the candidate MUST permit.
permit (
    principal is Approver,
    action == Action::"executeEmergency",
    resource is EmergencyAction
)
when {
    (principal == Approver::"s1"
     || principal == Approver::"s2"
     || principal == Approver::"s3"
     || principal == Approver::"s4"
     || principal == Approver::"s5")
    && context.attesters.containsAll([Approver::"s2", Approver::"s4", Approver::"s5"])
};
