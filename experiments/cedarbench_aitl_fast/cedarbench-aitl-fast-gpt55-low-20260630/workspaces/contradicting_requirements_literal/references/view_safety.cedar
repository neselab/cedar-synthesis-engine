// Ceiling: view is permitted only when the document is NOT
// quarantined. This encodes the precedence rule's resolution of
// the contradiction: quarantine wins over ownership, so even owners
// cannot view a quarantined document.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    !resource.quarantined
};
