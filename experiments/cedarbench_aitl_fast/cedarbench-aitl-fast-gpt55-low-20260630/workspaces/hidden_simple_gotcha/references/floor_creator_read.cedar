// Floor: the original creator MUST retain read access permanently,
// even after ownership transfers away. THIS is the hidden invariant
// that catches the surface-reading synthesizer.
permit (
    principal is User,
    action == Action::"read",
    resource is File
)
when {
    principal == resource.creator
};
