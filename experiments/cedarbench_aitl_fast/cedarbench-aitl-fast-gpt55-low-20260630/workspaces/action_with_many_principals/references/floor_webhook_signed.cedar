// Floor: a Webhook with a valid signature MUST be permitted to invoke.
permit (principal is Webhook, action == Action::"invoke", resource is Resource)
when { principal.signatureValid };
