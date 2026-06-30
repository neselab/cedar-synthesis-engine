permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
)
when {
    context.is_authenticated == true &&
    principal in resource.modifyACL &&
    principal in resource.manageACL
};