permit (
    principal is User,
    action == Action::"ModifyDocument",
    resource is Document
) when {
    context.is_authenticated == true &&
    (context.currentTime <= resource.expiryDate ||
     principal == resource.owner)
};