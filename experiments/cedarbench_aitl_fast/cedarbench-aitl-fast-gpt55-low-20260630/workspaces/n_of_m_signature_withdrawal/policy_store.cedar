// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is Signer,
    action == Action::"executeProposal",
    resource is Proposal
)
when {
    (
        principal == Signer::"s1" ||
        principal == Signer::"s2" ||
        principal == Signer::"s3" ||
        principal == Signer::"s4" ||
        principal == Signer::"s5"
    ) &&
    (
        context.activeSigners.containsAll([Signer::"s1", Signer::"s2", Signer::"s3"]) ||
        context.activeSigners.containsAll([Signer::"s1", Signer::"s2", Signer::"s4"]) ||
        context.activeSigners.containsAll([Signer::"s1", Signer::"s2", Signer::"s5"]) ||
        context.activeSigners.containsAll([Signer::"s1", Signer::"s3", Signer::"s4"]) ||
        context.activeSigners.containsAll([Signer::"s1", Signer::"s3", Signer::"s5"]) ||
        context.activeSigners.containsAll([Signer::"s1", Signer::"s4", Signer::"s5"]) ||
        context.activeSigners.containsAll([Signer::"s2", Signer::"s3", Signer::"s4"]) ||
        context.activeSigners.containsAll([Signer::"s2", Signer::"s3", Signer::"s5"]) ||
        context.activeSigners.containsAll([Signer::"s2", Signer::"s4", Signer::"s5"]) ||
        context.activeSigners.containsAll([Signer::"s3", Signer::"s4", Signer::"s5"])
    )
};

permit (
    principal is Signer,
    action == Action::"viewProposal",
    resource is Proposal
)
when {
    principal == Signer::"s1" ||
    principal == Signer::"s2" ||
    principal == Signer::"s3" ||
    principal == Signer::"s4" ||
    principal == Signer::"s5"
};

permit (
    principal is Signer,
    action == Action::"addSignature",
    resource is Proposal
)
when {
    principal == Signer::"s1" ||
    principal == Signer::"s2" ||
    principal == Signer::"s3" ||
    principal == Signer::"s4" ||
    principal == Signer::"s5"
};

permit (
    principal is Signer,
    action == Action::"withdrawSignature",
    resource is Proposal
)
when {
    principal == Signer::"s1" ||
    principal == Signer::"s2" ||
    principal == Signer::"s3" ||
    principal == Signer::"s4" ||
    principal == Signer::"s5"
};
