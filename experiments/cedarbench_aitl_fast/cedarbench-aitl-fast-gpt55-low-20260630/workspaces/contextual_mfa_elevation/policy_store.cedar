// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal.workspace == resource.workspace
};

permit (
    principal is User,
    action == Action::"comment",
    resource is Document
)
when {
    principal.workspace == resource.workspace
};

permit (
    principal is User,
    action == Action::"write",
    resource is Document
)
when {
    principal.workspace == resource.workspace
};

permit (
    principal is User,
    action == Action::"deleteDocument",
    resource is Document
)
when {
    principal.workspace == resource.workspace &&
    context.now.datetime.durationSince(principal.mfaVerifiedAt) < duration("15m")
};

permit (
    principal is User,
    action == Action::"adminOperation",
    resource is Workspace
)
when {
    principal.workspace == resource &&
    principal.isAdmin == true &&
    context.now.datetime.durationSince(principal.mfaVerifiedAt) < duration("15m")
};
