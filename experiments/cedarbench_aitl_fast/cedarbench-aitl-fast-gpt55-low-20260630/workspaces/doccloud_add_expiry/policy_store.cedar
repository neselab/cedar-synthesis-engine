// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
forbid (
    principal is User,
    action,
    resource
) when {
    context.is_authenticated == false
};

forbid (
    principal is User,
    action in [Action::"ViewDocument", Action::"ModifyDocument"],
    resource is Document
) when {
    principal in resource.owner.blocked || resource.owner in principal.blocked
};

forbid (
    principal,
    action in [
        Action::"ViewDocument",
        Action::"ModifyDocument",
        Action::"DeleteDocument",
        Action::"EditIsPrivate",
        Action::"EditPublicAccess",
        Action::"AddToShareACL"
    ],
    resource is Document
) when {
    context.currentTime > resource.expiryDate
} unless {
    principal is User &&
    principal == resource.owner &&
    action == Action::"DeleteDocument"
};

permit (
    principal is User,
    action in [
        Action::"ViewDocument",
        Action::"ModifyDocument",
        Action::"DeleteDocument",
        Action::"EditIsPrivate",
        Action::"EditPublicAccess",
        Action::"AddToShareACL"
    ],
    resource is Document
) when {
    principal == resource.owner
};

permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
) when {
    principal in resource.viewACL
};

permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
) when {
    principal in resource.modifyACL
};

permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
) when {
    principal in resource.manageACL
};

permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
) when {
    principal in resource.modifyACL
};

permit (
    principal is User,
    action in [
        Action::"AddToShareACL",
        Action::"DeleteDocument",
        Action::"EditIsPrivate",
        Action::"EditPublicAccess"
    ],
    resource is Document
) when {
    principal in resource.manageACL
};

permit (
    principal is Public,
    action == Action::"ViewDocument",
    resource is Document
) when {
    resource.publicAccess == "view" || resource.publicAccess == "edit"
};

permit (
    principal is User,
    action == Action::"ViewDocument",
    resource is Document
) when {
    resource.publicAccess == "view" || resource.publicAccess == "edit"
};

permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
) when {
    resource.publicAccess == "edit"
};

permit (
    principal is User,
    action == Action::"DeleteGroup",
    resource is Group
) when {
    principal == resource.owner
};

permit (
    principal is User,
    action == Action::"ModifyGroup",
    resource is Group
) when {
    principal == resource.owner
};

permit (
    principal is User,
    action == Action::"CreateDocument",
    resource is Drive
);

permit (
    principal is User,
    action == Action::"CreateGroup",
    resource is Drive
);
