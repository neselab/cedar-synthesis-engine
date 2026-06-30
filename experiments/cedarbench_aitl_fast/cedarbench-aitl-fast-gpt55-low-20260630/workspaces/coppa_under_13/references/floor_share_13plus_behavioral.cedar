// Floor: sharing behavioral data for a user who is at least 13
// (>= 4748 days old, conservative leap-year-safe threshold) MUST be
// permitted. The age check is on the data subject (resource.owner),
// not the requesting principal.
permit (
    principal is User,
    action == Action::"share",
    resource is DataPoint
)
when {
    resource.category == "behavioral"
    && context.now.durationSince(resource.owner.dateOfBirth) >= duration("4748d")
};
