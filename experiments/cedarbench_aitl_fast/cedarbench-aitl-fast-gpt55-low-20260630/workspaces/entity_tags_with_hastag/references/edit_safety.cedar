// Ceiling: edit permitted only when the user satisfies view's clearance +
// compartment requirements AND additionally holds edit_authorized tag
// containing "true".
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    principal.hasTag("clearance")
    && resource.hasTag("required_clearance")
    && principal.getTag("clearance").containsAll(resource.getTag("required_clearance"))
    && (!resource.hasTag("compartments_required")
        || (resource.hasTag("compartments_required")
            && principal.hasTag("compartment")
            && principal.getTag("compartment").containsAll(resource.getTag("compartments_required"))))
    && principal.hasTag("edit_authorized")
    && principal.getTag("edit_authorized").contains("true")
};
