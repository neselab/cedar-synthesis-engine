// Ceiling: invoke permitted only when BOTH:
//  - context has a nonce attribute (request carries proof of recency),
//  - the resource's validNonces set contains that nonce.
//
// This ceiling rules out the two deny states:
//   1. nonce missing            -> first conjunct false      -> not permitted
//   2. nonce present but unknown -> second conjunct false    -> not permitted
permit (
    principal is User,
    action == Action::"invoke",
    resource is CriticalEndpoint
)
when {
    context has nonce && resource.validNonces.contains(context.nonce)
};
