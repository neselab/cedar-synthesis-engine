// Floor: an Individual in the chain must be permitted.
permit (principal is Individual, action == Action::"access", resource is Resource)
when { principal in resource.parentOrg };
