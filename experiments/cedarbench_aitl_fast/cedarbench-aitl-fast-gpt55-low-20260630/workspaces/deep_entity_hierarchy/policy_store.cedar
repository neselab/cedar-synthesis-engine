// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal,
  action == Action::"view",
  resource
)
when {
  principal is Employee &&
  resource is Document &&
  (
    resource.classification == "public" ||
    resource.classification == "internal" ||
    (
      resource.classification == "confidential" &&
      principal in resource.ownerTeam
    )
  )
};

permit (
  principal,
  action == Action::"edit",
  resource
)
when {
  principal is Employee &&
  resource is Document &&
  principal in resource.ownerTeam &&
  resource.classification != "confidential"
};

permit (
  principal,
  action == Action::"delete",
  resource
)
when {
  principal is Employee &&
  resource is Document &&
  principal in resource.ownerTeam &&
  resource.classification == "public"
};
