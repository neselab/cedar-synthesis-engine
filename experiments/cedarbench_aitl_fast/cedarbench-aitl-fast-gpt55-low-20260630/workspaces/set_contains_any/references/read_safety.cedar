// Ceiling: read permitted only when interest tags overlap with topic tags
// AND user has all required clearance tags.
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal.interestTags.containsAny(resource.topicTags)
    && principal.clearanceTags.containsAll(resource.requiredClearanceTags)
};
