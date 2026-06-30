// Floor: the profile owner MUST be permitted to view their own profile.
permit (
    principal is User,
    action == Action::"viewProfile",
    resource is Profile
)
when {
    principal == resource.owner
};
