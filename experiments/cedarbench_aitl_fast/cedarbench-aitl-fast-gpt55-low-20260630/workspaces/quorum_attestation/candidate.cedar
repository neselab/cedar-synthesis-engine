permit (
    principal is Approver,
    action == Action::"executeEmergency",
    resource is EmergencyAction
)
when {
    (
        principal == Approver::"s1" ||
        principal == Approver::"s2" ||
        principal == Approver::"s3" ||
        principal == Approver::"s4" ||
        principal == Approver::"s5"
    ) &&
    (
        context.attesters.containsAll([Approver::"s1", Approver::"s2", Approver::"s3"]) ||
        context.attesters.containsAll([Approver::"s1", Approver::"s2", Approver::"s4"]) ||
        context.attesters.containsAll([Approver::"s1", Approver::"s2", Approver::"s5"]) ||
        context.attesters.containsAll([Approver::"s1", Approver::"s3", Approver::"s4"]) ||
        context.attesters.containsAll([Approver::"s1", Approver::"s3", Approver::"s5"]) ||
        context.attesters.containsAll([Approver::"s1", Approver::"s4", Approver::"s5"]) ||
        context.attesters.containsAll([Approver::"s2", Approver::"s3", Approver::"s4"]) ||
        context.attesters.containsAll([Approver::"s2", Approver::"s3", Approver::"s5"]) ||
        context.attesters.containsAll([Approver::"s2", Approver::"s4", Approver::"s5"]) ||
        context.attesters.containsAll([Approver::"s3", Approver::"s4", Approver::"s5"])
    )
};

permit (
    principal is Approver,
    action == Action::"viewEmergency",
    resource is EmergencyAction
);