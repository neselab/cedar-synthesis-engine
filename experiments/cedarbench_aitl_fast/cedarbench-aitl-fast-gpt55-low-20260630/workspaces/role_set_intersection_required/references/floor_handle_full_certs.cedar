// Floor: a worker holding EVERY required cert MUST be allowed to handle.
// (Trivially redundant with the ceiling — but pins the lower bound so
// containsAny / per-cert OR encodings are caught: containsAny would
// permit MORE workers than this floor demands and still pass the floor,
// but would also exceed the ceiling.)
permit (
    principal is Worker,
    action == Action::"handle",
    resource is Material
)
when {
    principal.certifications.containsAll(resource.requiredCerts)
};
