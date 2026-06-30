// Floor: any officer MUST be permitted to escalate a submitted
// loan application.
permit (
    principal is Officer,
    action == Action::"escalate",
    resource is LoanApplication
)
when {
    resource.isSubmitted
};
