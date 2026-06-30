// Floor: an EU-region user MUST be permitted to view an asset once
// the current time is at or after the asset's EU release datetime.
permit (
    principal is User,
    action == Action::"view",
    resource is Asset
)
when {
    principal.region == "eu"
    && context.now >= resource.releaseEU
};
