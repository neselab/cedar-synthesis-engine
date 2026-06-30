// Ceiling for executeEmergency: the candidate may permit ONLY when the
// principal is one of the five eligible approvers AND context.attesters
// is a superset of at least one 3-element subset of {s1, s2, s3, s4, s5}.
//
// Cedar has no .size() operator, so the threshold is encoded as a
// disjunction over the C(5,3) = 10 possible 3-of-5 subsets, each tested
// with .containsAll().
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
    && (
        context.attesters.containsAll([Approver::"s1", Approver::"s2", Approver::"s3"])
     || context.attesters.containsAll([Approver::"s1", Approver::"s2", Approver::"s4"])
     || context.attesters.containsAll([Approver::"s1", Approver::"s2", Approver::"s5"])
     || context.attesters.containsAll([Approver::"s1", Approver::"s3", Approver::"s4"])
     || context.attesters.containsAll([Approver::"s1", Approver::"s3", Approver::"s5"])
     || context.attesters.containsAll([Approver::"s1", Approver::"s4", Approver::"s5"])
     || context.attesters.containsAll([Approver::"s2", Approver::"s3", Approver::"s4"])
     || context.attesters.containsAll([Approver::"s2", Approver::"s3", Approver::"s5"])
     || context.attesters.containsAll([Approver::"s2", Approver::"s4", Approver::"s5"])
     || context.attesters.containsAll([Approver::"s3", Approver::"s4", Approver::"s5"])
    )
};
