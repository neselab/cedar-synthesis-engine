// Ceiling: deleteDocument permitted only when the principal is the
// owner AND the document has not expired AND the document is NOT under
// a legal hold. Legal team members have NO delete authority — legal
// hold blocks deletion entirely until the hold is lifted.
permit (
    principal is User,
    action == Action::"deleteDocument",
    resource is Document
)
when {
    principal == resource.owner
    && context.now.datetime < resource.expiryDate
    && !resource.legalHold
};
