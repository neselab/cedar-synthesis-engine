// Floor: a User principal with mfaVerified MUST be permitted to invoke.
permit (principal is User, action == Action::"invoke", resource is Resource)
when { principal.mfaVerified };
