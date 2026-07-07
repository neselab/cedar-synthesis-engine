permit (principal is User, action == Action::"monitorReviewProcess", resource is ReviewOverview)
when {
    principal.role == "chair" || principal.role == "pcc"
};

