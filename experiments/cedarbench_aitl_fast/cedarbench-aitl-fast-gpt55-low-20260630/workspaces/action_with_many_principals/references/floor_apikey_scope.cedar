// Floor: an ApiKey whose scopes contain "invoke" MUST be permitted to invoke.
permit (principal is ApiKey, action == Action::"invoke", resource is Resource)
when { principal.scopes.contains("invoke") };
