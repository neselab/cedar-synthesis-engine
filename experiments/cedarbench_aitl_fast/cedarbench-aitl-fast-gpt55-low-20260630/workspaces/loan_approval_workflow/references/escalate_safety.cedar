// Ceiling: escalate is permitted only when the application is submitted.
permit (
    principal is Officer,
    action == Action::"escalate",
    resource is LoanApplication
)
when {
    resource.isSubmitted
};
