// Ceiling: audit permitted for any approver role. There are no
// amount or tier restrictions on the audit action.
permit (
    principal is Approver,
    action == Action::"audit",
    resource is Transaction
)
when {
    principal.role == "teller"
    || principal.role == "manager"
    || principal.role == "vp"
};
