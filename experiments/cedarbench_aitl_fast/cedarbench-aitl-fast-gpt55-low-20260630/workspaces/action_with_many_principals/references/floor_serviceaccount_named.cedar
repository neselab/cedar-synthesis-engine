// Floor: a ServiceAccount with a non-empty serviceName MUST be permitted.
permit (principal is ServiceAccount, action == Action::"invoke", resource is Resource)
when { principal.serviceName != "" };
