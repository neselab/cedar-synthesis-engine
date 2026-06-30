permit (
    principal is User,
    action == Action::"AddToShareACL",
    resource is Document
)
when {
    principal.org == resource.owner.org ||
    principal in resource.manageACL
};