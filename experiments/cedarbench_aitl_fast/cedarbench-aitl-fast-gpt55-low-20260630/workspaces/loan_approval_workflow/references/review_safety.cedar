// Ceiling: review is permitted only when the application is submitted.
permit (
    principal is Officer,
    action == Action::"review",
    resource is LoanApplication
)
when {
    resource.isSubmitted
};
