// Ceiling: handle permitted only when worker holds EVERY required cert.
// Intersection requirement — containsAll, not containsAny.
permit (
    principal is Worker,
    action == Action::"handle",
    resource is Material
)
when {
    principal.certifications.containsAll(resource.requiredCerts)
};
