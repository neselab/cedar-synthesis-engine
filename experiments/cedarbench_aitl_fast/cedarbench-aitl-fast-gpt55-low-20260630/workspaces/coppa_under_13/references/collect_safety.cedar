// Ceiling: collect permitted only when one of the following holds:
//   (a) the data category is "anonymous" (no PII), OR
//   (b) the user is 13 or older (>= 4748 days old, conservative
//       leap-year-safe threshold), OR
//   (c) the user is under 13 AND verifiable parental consent has been
//       collected (parentalConsentToken present in context).
//
// The has-guard on parentalConsentToken is required because the
// attribute is optional in the schema. Cedar's type-checker does NOT
// propagate negation through `has`, so the guard MUST take the form
// `(!(context has X) || (context has X && ...))` rather than the
// shorter-but-rejected `!(context has X) || ...`.
permit (
    principal is User,
    action == Action::"collect",
    resource is DataPoint
)
when {
    resource.category == "anonymous"
    || context.now.durationSince(principal.dateOfBirth) >= duration("4748d")
    || (context has parentalConsentToken)
};
