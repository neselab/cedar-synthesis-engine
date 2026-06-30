forbid (
  principal is User,
  action,
  resource
)
when {
  context.is_authenticated == false
};

forbid (
  principal is User,
  action == Action::"ViewDocument",
  resource is Document
)
when {
  principal in resource.owner.blocked
};

forbid (
  principal is User,
  action == Action::"ViewDocument",
  resource is Document
)
when {
  resource.owner in principal.blocked
};

forbid (
  principal is User,
  action == Action::"ModifyDocument",
  resource is Document
)
when {
  principal in resource.owner.blocked
};

forbid (
  principal is User,
  action == Action::"ModifyDocument",
  resource is Document
)
when {
  resource.owner in principal.blocked
};

forbid (
  principal is User,
  action == Action::"ModifyDocument",
  resource is Document
)
when {
  resource.isLocked == true
};

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
  action == Action::"ModifyDocument",
  resource is Document
)
when {
  principal == resource.owner
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
  action == Action::"EditPublicAccess",
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
  action == Action::"ModifyDocument",
  resource is Document
)
when {
  principal in resource.modifyACL
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
  action == Action::"DeleteDocument",
  resource is Document
)
when {
  principal in resource.manageACL
};

permit (
  principal is User,
  action == Action::"EditIsPrivate",
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
  principal in resource.manageACL
};

permit (
  principal is Public,
  action == Action::"ViewDocument",
  resource is Document
)
when {
  resource.publicAccess == "view"
};

permit (
  principal is Public,
  action == Action::"ViewDocument",
  resource is Document
)
when {
  resource.publicAccess == "edit"
};

permit (
  principal is User,
  action == Action::"ViewDocument",
  resource is Document
)
when {
  resource.publicAccess == "view"
};

permit (
  principal is User,
  action == Action::"ViewDocument",
  resource is Document
)
when {
  resource.publicAccess == "edit"
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
  action == Action::"DeleteGroup",
  resource is Group
)
when {
  principal == resource.owner
};

permit (
  principal is User,
  action == Action::"ModifyGroup",
  resource is Group
)
when {
  principal == resource.owner
};