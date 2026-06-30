// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"read",
    resource is Article
)
when {
    principal.role == "viewer" &&
    resource.isPublished == true
};

@id("editor-read")
@description("Allows editors to read any article.")
permit (
    principal is User,
    action == Action::"read",
    resource is Article
)
when {
    principal.role == "editor"
};

@id("editor-write")
@description("Allows editors to write any article.")
permit (
    principal is User,
    action == Action::"write",
    resource is Article
)
when {
    principal.role == "editor"
};

@id("admin-read")
@description("Allows admins to read any article.")
permit (
    principal is User,
    action == Action::"read",
    resource is Article
)
when {
    principal.role == "admin"
};

@id("admin-write")
@description("Allows admins to write any article.")
permit (
    principal is User,
    action == Action::"write",
    resource is Article
)
when {
    principal.role == "admin"
};

@id("admin-delete")
@description("Allows admins to delete any article.")
permit (
    principal is User,
    action == Action::"delete",
    resource is Article
)
when {
    principal.role == "admin"
};
