// Floor: an APAC-region user MUST be permitted to view an asset once
// the current time is at or after the asset's APAC release datetime.
permit (
    principal is User,
    action == Action::"view",
    resource is Asset
)
when {
    principal.region == "apac"
    && context.now >= resource.releaseAPAC
};
