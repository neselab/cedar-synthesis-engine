// Floor (Requirement C — restated post-resolution): for any document
// that is NOT quarantined, the owner MUST be permitted to view it.
// This is the SAME property as owner_must_view_unquarantined.cedar
// stated from the document's perspective rather than the principal's:
// it gives a second independent verification angle on the resolved
// owner-permission guarantee.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    !resource.quarantined
    && resource.owner == principal
};
