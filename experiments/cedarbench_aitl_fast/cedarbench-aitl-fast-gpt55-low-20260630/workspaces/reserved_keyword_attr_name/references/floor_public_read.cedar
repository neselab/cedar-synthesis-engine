// Floor: a hasAccess member viewing a public channel MUST be permitted to read.
permit (principal is Member, action == Action::"read", resource is Channel)
when { resource.isPublic && principal.hasAccess };
