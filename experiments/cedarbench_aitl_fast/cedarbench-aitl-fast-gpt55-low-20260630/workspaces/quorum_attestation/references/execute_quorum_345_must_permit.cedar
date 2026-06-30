// Floor for executeEmergency with quorum {s3,s4,s5}.
// This is the "last" subset in canonical enumeration order — a common
// omission target. When attesters contains at least {s3,s4,s5} and the
// principal is one of the five eligible approvers, the candidate MUST
// permit.
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
    && context.attesters.containsAll([Approver::"s3", Approver::"s4", Approver::"s5"])
};
