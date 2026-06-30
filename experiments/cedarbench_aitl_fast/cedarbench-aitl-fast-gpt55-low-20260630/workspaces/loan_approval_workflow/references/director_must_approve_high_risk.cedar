// Floor: a director with sufficient approvalLimit MUST be permitted to
// approve a high-risk submitted loan application.
permit (
    principal is Officer,
    action == Action::"approve",
    resource is LoanApplication
)
when {
    resource.isSubmitted
    && principal.approvalLimit >= resource.amount
    && resource.riskRating == "high"
    && principal.role == "director"
};
