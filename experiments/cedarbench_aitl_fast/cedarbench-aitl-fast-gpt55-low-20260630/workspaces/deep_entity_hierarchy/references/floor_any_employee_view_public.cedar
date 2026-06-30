// Floor: any employee MUST be able to view a public document.
permit (
    principal is Employee,
    action == Action::"view",
    resource is Document
)
when {
    resource.classification == "public"
};
