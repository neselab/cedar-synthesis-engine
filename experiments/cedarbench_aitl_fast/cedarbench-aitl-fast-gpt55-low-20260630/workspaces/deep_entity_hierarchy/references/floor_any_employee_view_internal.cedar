// Floor: any employee MUST be able to view an internal document.
permit (
    principal is Employee,
    action == Action::"view",
    resource is Document
)
when {
    resource.classification == "internal"
};
