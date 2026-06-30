// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
forbid (principal, action, resource)
when {
  context.is_authenticated == false
};

forbid (
  principal is User,
  action in [
    Action::"ViewDocument",
    Action::"ModifyDocument",
    Action::"DeleteDocument",
    Action::"EditIsPrivate",
    Action::"AddToShareACL",
    Action::"EditPublicAccess"
  ],
  resource is Document
)
when {
  resource.owner.blocked.contains(principal) ||
  principal.blocked.contains(resource.owner)
};

forbid (
  principal,
  action in [
    Action::"ViewDocument",
    Action::"ModifyDocument",
    Action::"DeleteDocument",
    Action::"EditIsPrivate",
    Action::"AddToShareACL",
    Action::"EditPublicAccess"
  ],
  resource is Document
)
when {
  principal != resource.owner &&
  resource.isPrivate
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

permit (
  principal is User,
  action == Action::"ViewDocument",
  resource is Document
)
when {
  principal == resource.owner
};

permit (
  principal is User,
  action == Action::"ViewDocument",
  resource is Document
)
when {
  principal in resource.viewACL &&
  resource.isPrivate == false
};

permit (
  principal is Public,
  action == Action::"ViewDocument",
  resource is Document
)
when {
  (resource.publicAccess == "view" || resource.publicAccess == "edit") &&
  resource.isPrivate == false
};

permit (
  principal is User,
  action == Action::"ModifyDocument",
  resource is Document
)
when {
  principal == resource.owner
};

permit (
  principal is User,
  action == Action::"ModifyDocument",
  resource is Document
)
when {
  principal in resource.modifyACL &&
  resource.isPrivate == false
};

permit (
  principal is User,
  action == Action::"DeleteDocument",
  resource is Document
)
when {
  principal == resource.owner
};

permit (
  principal is User,
  action == Action::"EditIsPrivate",
  resource is Document
)
when {
  principal == resource.owner
};

permit (
  principal is User,
  action == Action::"AddToShareACL",
  resource is Document
)
when {
  principal == resource.owner
};

permit (
  principal is User,
  action == Action::"AddToShareACL",
  resource is Document
)
when {
  principal in resource.manageACL
};

permit (
  principal is User,
  action == Action::"EditPublicAccess",
  resource is Document
)
when {
  principal == resource.owner
};

permit (
  principal is User,
  action == Action::"EditPublicAccess",
  resource is Document
)
when {
  principal in resource.manageACL
};

permit (
  principal is User,
  action == Action::"ModifyGroup",
  resource is Group
)
when {
  principal == resource.owner
};

permit (
  principal is User,
  action == Action::"DeleteGroup",
  resource is Group
)
when {
  principal == resource.owner
};
