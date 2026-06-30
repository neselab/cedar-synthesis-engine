// Floor: an analyst MUST be permitted to submit a loan application
// that has not yet been submitted.
permit (
    principal is Officer,
    action == Action::"submit",
    resource is LoanApplication
)
when {
    principal.role == "analyst"
    && !resource.isSubmitted
};
