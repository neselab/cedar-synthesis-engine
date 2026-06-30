// Floor: a viewByTag request whose requestedTag is the literal
// "public" on a Document whose tags contains "public" MUST be
// permitted. This pins the documented happy path and is jointly
// satisfiable with the safety ceiling (non-empty set, non-empty
// requested tag).
permit (
    principal is User,
    action == Action::"viewByTag",
    resource is Document
)
when {
    context.requestedTag == "public"
    && resource.tags.contains("public")
};
