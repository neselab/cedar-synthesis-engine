// Ceiling: query permitted only when clearance dominates classification.
//   public    -> any clearance
//   internal  -> clearance "internal" or "restricted"
//   restricted -> clearance "restricted" only
permit (
    principal is User,
    action == Action::"query",
    resource is Dataset
)
when {
    resource.classification == "public"
    || (resource.classification == "internal"
        && (principal.clearance == "internal" || principal.clearance == "restricted"))
    || (resource.classification == "restricted"
        && principal.clearance == "restricted")
};
