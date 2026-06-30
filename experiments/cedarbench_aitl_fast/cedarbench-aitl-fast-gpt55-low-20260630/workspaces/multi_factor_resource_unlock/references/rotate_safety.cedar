// Ceiling: rotate permitted only when ALL of:
//   - role is security_officer or admin,
//   - hasMfa is true,
//   - for level 3: hasSecurityReview is additionally required.
permit (
    principal is User,
    action == Action::"rotate",
    resource is Secret
)
when {
    (principal.role == "security_officer" || principal.role == "admin")
    && context.hasMfa
    && (resource.sensitivityLevel != 3 || context.hasSecurityReview)
};
