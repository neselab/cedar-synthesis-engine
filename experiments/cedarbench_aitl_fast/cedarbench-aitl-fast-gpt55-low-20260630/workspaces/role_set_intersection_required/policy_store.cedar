// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is Worker,
    action == Action::"view",
    resource is Material
);

permit (
    principal is Worker,
    action == Action::"handle",
    resource is Material
) when {
    principal.certifications.containsAll(resource.requiredCerts)
};
