// Floor: user with overlapping interest tags AND full clearance MUST read.
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal.interestTags.containsAny(resource.topicTags)
    && principal.clearanceTags.containsAll(resource.requiredClearanceTags)
};
