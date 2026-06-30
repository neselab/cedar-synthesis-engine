permit (
    principal is User,
    action == Action::"login",
    resource is Session
);

permit (
    principal is User,
    action == Action::"logout",
    resource is Session
)
when {
    principal.sessionActive == true
};

permit (
    principal is User,
    action == Action::"refreshToken",
    resource is Session
)
when {
    principal.sessionActive == true &&
    principal.role != "guest"
};

permit (
    principal is User,
    action == Action::"viewProfile",
    resource is Profile
)
when {
    principal == resource.owner
};