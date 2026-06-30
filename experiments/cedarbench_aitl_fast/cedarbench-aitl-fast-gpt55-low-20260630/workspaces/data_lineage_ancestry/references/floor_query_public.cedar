// Floor: any user MUST be permitted to query a public dataset.
permit (
    principal is User,
    action == Action::"query",
    resource is Dataset
)
when {
    resource.classification == "public"
};
