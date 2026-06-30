// Ceiling for viewClientProfile: intentionally loose.
//
// The spec requires "there exists an orgInfo in principal.assigned_orgs
// with orgInfo.organization == resource.organization". Cedar's set
// containment does not support existential quantification with partial
// record matching — `.contains()` requires a fully-specified record,
// and there is no `.any()` operator.
//
// The strictest ceiling expressible in base Cedar is "permit any
// Professional viewClientProfile of any Client" — i.e., no constraint.
// A candidate that over-permits will still satisfy this ceiling. The
// semantic gap (org match cannot be verified) is an acknowledged spec
// expressibility limitation, not a harness bug.
permit (
    principal is Taxpreparer::Professional,
    action == Taxpreparer::Action::"viewClientProfile",
    resource is Taxpreparer::Client
);
