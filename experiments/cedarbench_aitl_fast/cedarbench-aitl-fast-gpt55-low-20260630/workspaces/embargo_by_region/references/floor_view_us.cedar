// Floor: a US-region user MUST be permitted to view an asset once
// the current time is at or after the asset's US release datetime.
permit (
    principal is User,
    action == Action::"view",
    resource is Asset
)
when {
    principal.region == "us"
    && context.now >= resource.releaseUS
};
