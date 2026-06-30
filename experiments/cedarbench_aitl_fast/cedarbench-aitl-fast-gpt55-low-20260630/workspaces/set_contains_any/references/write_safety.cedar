// Ceiling: write permitted only when user's interest tags contain ALL
// document topic tags AND user has all required clearance tags.
permit (
    principal is User,
    action == Action::"write",
    resource is Document
)
when {
    principal.interestTags.containsAll(resource.topicTags)
    && principal.clearanceTags.containsAll(resource.requiredClearanceTags)
};
