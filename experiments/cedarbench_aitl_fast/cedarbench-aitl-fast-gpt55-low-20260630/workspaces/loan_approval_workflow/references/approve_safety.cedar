// Ceiling: approve is permitted only when ALL of:
//  - application is submitted,
//  - officer's approvalLimit >= loan amount,
//  - if high-risk, the officer is a director or VP.
permit (
    principal is Officer,
    action == Action::"approve",
    resource is LoanApplication
)
when {
    resource.isSubmitted
    && principal.approvalLimit >= resource.amount
    && (resource.riskRating != "high" || principal.role == "director" || principal.role == "vp")
};
