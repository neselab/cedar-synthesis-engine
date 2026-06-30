// Floor for executeEmergency with quorum {s1,s2,s3}.
// When attesters contains at least {s1,s2,s3} and the principal is one
// of the five eligible approvers, the candidate MUST permit.
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
    && context.attesters.containsAll([Approver::"s1", Approver::"s2", Approver::"s3"])
};
