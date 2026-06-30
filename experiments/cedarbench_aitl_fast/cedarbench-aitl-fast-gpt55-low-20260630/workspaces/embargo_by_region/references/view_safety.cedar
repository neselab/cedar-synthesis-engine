// Ceiling: view permitted only when the current time is at or after
// the release datetime for the user's region. Cedar has no dynamic
// record key access -- the policy must branch explicitly on each
// region value.
permit (
    principal is User,
    action == Action::"view",
    resource is Asset
)
when {
    (principal.region == "us"   && context.now >= resource.releaseUS)
    || (principal.region == "eu"   && context.now >= resource.releaseEU)
    || (principal.region == "apac" && context.now >= resource.releaseAPAC)
};
