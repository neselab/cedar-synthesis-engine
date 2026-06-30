// Ceiling: reject is permitted only when the application is submitted.
permit (
    principal is Officer,
    action == Action::"reject",
    resource is LoanApplication
)
when {
    resource.isSubmitted
};
