// Ceiling: submit is permitted only when the principal is an analyst
// AND the application has not already been submitted.
permit (
    principal is Officer,
    action == Action::"submit",
    resource is LoanApplication
)
when {
    principal.role == "analyst"
    && !resource.isSubmitted
};
