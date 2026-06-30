// Floor: any officer MUST be permitted to reject a submitted
// loan application.
permit (
    principal is Officer,
    action == Action::"reject",
    resource is LoanApplication
)
when {
    resource.isSubmitted
};
