// Access permitted when individual is in the resource's parent Org.
permit (principal is Individual, action == Action::"access", resource is Resource)
when { principal in resource.parentOrg };
