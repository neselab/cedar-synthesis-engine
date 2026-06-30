permit (
    principal is User,
    action == Action::"grantViewAccessToPresentation",
    resource is Presentation
)
when {
    (resource.owner == principal ||
     principal in resource.editors ||
     principal in resource.editorTeams) &&
    (context.target.job != Job::"customer" ||
     (principal.job == Job::"distributor" &&
      principal.customerId == context.target.customerId))
};