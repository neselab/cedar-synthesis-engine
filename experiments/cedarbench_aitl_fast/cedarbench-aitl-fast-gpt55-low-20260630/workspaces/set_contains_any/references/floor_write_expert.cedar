// Floor: user with all topic tags AND full clearance MUST write.
permit (
    principal is User,
    action == Action::"write",
    resource is Document
)
when {
    principal.interestTags.containsAll(resource.topicTags)
    && principal.clearanceTags.containsAll(resource.requiredClearanceTags)
};
