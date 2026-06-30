permit (
  principal is User,
  action == Action::"view",
  resource is JointAsset
)
when {
  principal == resource.owner1 ||
  principal == resource.owner2
};

permit (
  principal is User,
  action == Action::"transfer",
  resource is JointAsset
)
when {
  context has consent1 &&
  context has consent2 &&
  (
    (
      context.consent1.signer == resource.owner1 &&
      context.consent2.signer == resource.owner2
    ) ||
    (
      context.consent1.signer == resource.owner2 &&
      context.consent2.signer == resource.owner1
    )
  ) &&
  context.now.durationSince(context.consent1.signedAt) >= duration("0h") &&
  context.now.durationSince(context.consent1.signedAt) <= duration("24h") &&
  context.now.durationSince(context.consent2.signedAt) >= duration("0h") &&
  context.now.durationSince(context.consent2.signedAt) <= duration("24h")
};