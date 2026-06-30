// Floor: any User MUST be permitted to `viewBalance` on any Account.
// The candidate may not gate balance viewing behind any additional
// condition.
permit (
    principal is User,
    action == Action::"viewBalance",
    resource is Account
);
