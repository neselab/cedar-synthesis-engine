// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal.interestTags.containsAny(resource.topicTags) &&
    principal.clearanceTags.containsAll(resource.requiredClearanceTags)
};

permit (
    principal is User,
    action == Action::"write",
    resource is Document
)
when {
    principal.interestTags.containsAll(resource.topicTags) &&
    principal.clearanceTags.containsAll(resource.requiredClearanceTags)
};

permit (
    principal is User,
    action == Action::"manageTags",
    resource is Document
)
when {
    principal == resource.owner
};
