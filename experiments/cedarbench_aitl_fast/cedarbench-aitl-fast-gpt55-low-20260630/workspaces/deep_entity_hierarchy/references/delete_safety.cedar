// Ceiling: delete permitted only when same team AND public.
permit (
    principal is Employee,
    action == Action::"delete",
    resource is Document
)
when {
    principal in resource.ownerTeam
    && resource.classification == "public"
};
