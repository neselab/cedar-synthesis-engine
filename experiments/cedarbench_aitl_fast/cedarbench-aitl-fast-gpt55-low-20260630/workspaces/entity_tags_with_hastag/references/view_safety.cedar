// Ceiling: view permitted only when the user holds a clearance tag that
// covers the document's required_clearance, AND if the document declares
// compartments_required the user holds a matching compartment tag.
//
// Notes:
//  - Every getTag MUST be preceded by a hasTag guard in the same clause.
//  - The negated-hasTag trap (§5.4/§8.3) applies: the compartment branch
//    is written positively as
//      (!resource.hasTag("compartments_required")
//       || (resource.hasTag("compartments_required") && ...))
permit (
    principal is User,
    action == Action::"view",
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
};
