permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    principal.org == resource.owner.org ||
    principal in resource.manageACL
};