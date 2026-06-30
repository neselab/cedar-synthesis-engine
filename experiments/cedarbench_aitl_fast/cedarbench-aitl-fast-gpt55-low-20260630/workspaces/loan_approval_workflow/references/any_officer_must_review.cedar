// Floor: any officer MUST be permitted to review a submitted
// loan application.
permit (
    principal is Officer,
    action == Action::"review",
    resource is LoanApplication
)
when {
    resource.isSubmitted
};
