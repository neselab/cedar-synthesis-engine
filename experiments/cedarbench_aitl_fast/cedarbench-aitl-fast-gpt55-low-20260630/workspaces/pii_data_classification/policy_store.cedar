// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
forbid (
    principal is User,
    action in [Action::"readDocument", Action::"downloadDocument"],
    resource is Document
)
when {
    resource.containsPII == true &&
    principal.hasPIITraining == false
};

forbid (
    principal is User,
    action in [Action::"readDocument", Action::"downloadDocument"],
    resource is Document
)
when {
    resource.classification == "Restricted" &&
    !(principal in resource.needToKnow)
};

permit (
    principal is User,
    action == Action::"readDocument",
    resource is Document
)
when {
    resource.classification == "Public" &&
    (
        principal.clearance == "L1" ||
        principal.clearance == "L2" ||
        principal.clearance == "L3" ||
        principal.clearance == "L4"
    )
};

permit (
    principal is User,
    action == Action::"readDocument",
    resource is Document
)
when {
    resource.classification == "Internal" &&
    (
        principal.clearance == "L2" ||
        principal.clearance == "L3" ||
        principal.clearance == "L4"
    )
};

permit (
    principal is User,
    action == Action::"readDocument",
    resource is Document
)
when {
    resource.classification == "Confidential" &&
    (
        principal.clearance == "L3" ||
        principal.clearance == "L4"
    )
};

permit (
    principal is User,
    action == Action::"readDocument",
    resource is Document
)
when {
    resource.classification == "Restricted" &&
    principal.clearance == "L4"
};

permit (
    principal is User,
    action == Action::"downloadDocument",
    resource is Document
)
when {
    resource.classification == "Public" &&
    (
        principal.clearance == "L2" ||
        principal.clearance == "L3" ||
        principal.clearance == "L4"
    )
};

permit (
    principal is User,
    action == Action::"downloadDocument",
    resource is Document
)
when {
    resource.classification == "Internal" &&
    (
        principal.clearance == "L3" ||
        principal.clearance == "L4"
    )
};

permit (
    principal is User,
    action == Action::"downloadDocument",
    resource is Document
)
when {
    resource.classification == "Confidential" &&
    principal.clearance == "L4"
};
