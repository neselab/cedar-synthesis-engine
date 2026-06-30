// Floor: a viewByTag request whose requestedTag is the literal
// "draft" on a Document whose tags contains "draft" MUST be
// permitted. Pins a second documented happy path.
permit (
    principal is User,
    action == Action::"viewByTag",
    resource is Document
)
when {
    context.requestedTag == "draft"
    && resource.tags.contains("draft")
};
