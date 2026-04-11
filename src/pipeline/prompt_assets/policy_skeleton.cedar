// Example Cedar skeleton
permit (
    principal is User,
    action == Action::"some_action",
    resource is SomeResource
) when {
    true
};

