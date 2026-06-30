// Policy store — verified policies appended here

// --- Verified (eval iteration 2) ---
forbid (
  principal,
  action in [
    Action::"ViewDocument",
    Action::"ModifyDocument",
    Action::"DeleteDocument",
    Action::"EditIsPrivate",
    Action::"EditPublicAccess",
    Action::"AddToShareACL",
    Action::"CreateDocument",
    Action::"CreateGroup",
    Action::"DeleteGroup",
    Action::"ModifyGroup"
  ],
  resource
)
when {
  principal is User &&
  context.is_authenticated == false
};

permit (
  principal,
  action in [
    Action::"ViewDocument",
    Action::"ModifyDocument",
    Action::"DeleteDocument",
    Action::"EditIsPrivate",
    Action::"EditPublicAccess",
    Action::"AddToShareACL"
  ],
  resource
)
when {
  principal is User &&
  resource is Document &&
  resource.owner == principal
};

permit (
  principal,
  action == Action::"ViewDocument",
  resource
)
when {
  principal is User &&
  resource is Document &&
  principal in resource.viewACL
};

permit (
  principal,
  action == Action::"ModifyDocument",
  resource
)
when {
  principal is User &&
  resource is Document &&
  principal in resource.modifyACL
};

permit (
  principal,
  action in [
    Action::"AddToShareACL",
    Action::"DeleteDocument",
    Action::"EditIsPrivate",
    Action::"EditPublicAccess"
  ],
  resource
)
when {
  principal is User &&
  resource is Document &&
  principal in resource.manageACL
};

permit (
  principal,
  action == Action::"ViewDocument",
  resource
)
when {
  principal is Public &&
  resource is Document &&
  (resource.publicAccess == "view" || resource.publicAccess == "edit")
};

permit (
  principal,
  action == Action::"ViewDocument",
  resource
)
when {
  principal is User &&
  resource is Document &&
  (resource.publicAccess == "view" || resource.publicAccess == "edit")
};

permit (
  principal,
  action == Action::"ModifyDocument",
  resource
)
when {
  principal is User &&
  resource is Document &&
  resource.publicAccess == "edit"
};

permit (
  principal,
  action in [
    Action::"DeleteGroup",
    Action::"ModifyGroup"
  ],
  resource
)
when {
  principal is User &&
  resource is Group &&
  resource.owner == principal
};

permit (
  principal,
  action == Action::"CreateDocument",
  resource
)
when {
  principal is User &&
  resource is Drive
};

permit (
  principal,
  action == Action::"CreateGroup",
  resource
)
when {
  principal is User &&
  resource is Drive
};
