forbid (
  principal is User,
  action,
  resource
)
when {
  !context.is_authenticated
};

forbid (
  principal is User,
  action in [Action::"ViewDocument", Action::"ModifyDocument"],
  resource is Document
)
when {
  principal in resource.owner.blocked
};

forbid (
  principal is User,
  action in [Action::"ViewDocument", Action::"ModifyDocument"],
  resource is Document
)
when {
  resource.owner in principal.blocked
};

permit (
  principal is User,
  action in [
    Action::"ViewDocument",
    Action::"ModifyDocument",
    Action::"DeleteDocument",
    Action::"EditIsPrivate",
    Action::"EditPublicAccess",
    Action::"AddToShareACL",
    Action::"ViewMetadata"
  ],
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
  principal in resource.viewACL
};

permit (
  principal is User,
  action == Action::"ViewDocument",
  resource is Document
)
when {
  principal in resource.modifyACL
};

permit (
  principal is User,
  action == Action::"ViewDocument",
  resource is Document
)
when {
  principal in resource.manageACL
};

permit (
  principal is User,
  action == Action::"ViewDocument",
  resource is Document
)
when {
  resource.publicAccess == "view" || resource.publicAccess == "edit"
};

permit (
  principal is Public,
  action == Action::"ViewDocument",
  resource is Document
)
when {
  resource.publicAccess == "view" || resource.publicAccess == "edit"
};

permit (
  principal is User,
  action == Action::"ModifyDocument",
  resource is Document
)
when {
  principal in resource.modifyACL
};

permit (
  principal is User,
  action == Action::"ModifyDocument",
  resource is Document
)
when {
  resource.publicAccess == "edit"
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
)
when {
  principal in resource.manageACL
};

permit (
  principal is User,
  action == Action::"ViewMetadata",
  resource is Document
)
when {
  principal in resource.viewACL ||
  principal in resource.modifyACL ||
  principal in resource.manageACL ||
  resource.publicAccess == "preview" ||
  resource.publicAccess == "view" ||
  resource.publicAccess == "edit"
};

permit (
  principal is Public,
  action == Action::"ViewMetadata",
  resource is Document
)
when {
  resource.publicAccess == "preview" ||
  resource.publicAccess == "view" ||
  resource.publicAccess == "edit"
};

permit (
  principal is User,
  action in [Action::"DeleteGroup", Action::"ModifyGroup"],
  resource is Group
)
when {
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