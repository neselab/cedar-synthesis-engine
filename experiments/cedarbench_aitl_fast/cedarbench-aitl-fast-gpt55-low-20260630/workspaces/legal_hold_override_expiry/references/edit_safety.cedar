// Ceiling: editDocument permitted only when either:
//  (a) the principal is the owner AND the document has not expired, OR
//  (b) the principal is a legal team member AND the document is under
//      a legal hold (expiry is ignored in this case).
permit (
    principal is User,
    action == Action::"editDocument",
    resource is Document
)
when {
    (principal == resource.owner && context.now.datetime < resource.expiryDate)
    || (principal.isLegalTeam && resource.legalHold)
};
