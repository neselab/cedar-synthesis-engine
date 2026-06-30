// Floor: when the material has NO required certs, ANY worker must be
// allowed to handle it. This pins the empty-set semantics of containsAll
// (every set is a superset of the empty set) and rejects encodings
// that special-case empty by denying.
permit (
    principal is Worker,
    action == Action::"handle",
    resource is Material
)
when {
    resource.requiredCerts.isEmpty()
};
