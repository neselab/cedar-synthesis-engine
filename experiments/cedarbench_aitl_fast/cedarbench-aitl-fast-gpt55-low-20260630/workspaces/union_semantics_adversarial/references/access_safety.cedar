// Ceiling: candidate access permits MUST be no more permissive than
// the coupled (group, category) condition. The naive cross-product
// `(groupA || groupB) && (alpha || beta)` fails this check because it
// permits a groupA-only user to access beta resources.
permit (principal is User, action == Action::"access", resource is Resource)
when {
    (principal.groupA && resource.category == "alpha")
    || (principal.groupB && resource.category == "beta")
};
