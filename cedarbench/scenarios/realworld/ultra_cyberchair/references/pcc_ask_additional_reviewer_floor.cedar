permit (principal is User, action == Action::"askAdditionalReviewer", resource is ReviewOverview)
when {
    principal.role == "pcc"
    && resource.paper.onlyNonExpertReviews
};

