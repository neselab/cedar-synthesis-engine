// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
forbid (
    principal is User,
    action in [
        Action::"submit",
        Action::"approve",
        Action::"finalize",
        Action::"reject"
    ],
    resource is Document
)
when {
    resource.status == "approved" || resource.status == "rejected"
};

permit (
    principal is User,
    action == Action::"submit",
    resource is Document
)
when {
    principal == resource.owner &&
    resource.status == "draft"
};

permit (
    principal is User,
    action == Action::"approve",
    resource is Document
)
when {
    principal in resource.requiredApprovers &&
    resource.status == "in_review"
};

permit (
    principal is User,
    action == Action::"finalize",
    resource is Document
)
when {
    principal in resource.requiredApprovers &&
    resource.status == "in_review" &&
    resource.currentApprovals.containsAll(resource.requiredApprovers)
};

permit (
    principal is User,
    action == Action::"reject",
    resource is Document
)
when {
    principal in resource.requiredApprovers &&
    resource.status == "in_review"
};

permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal == resource.owner ||
    principal in resource.requiredApprovers
};
