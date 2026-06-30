// Floor: a Scheduler whose cron trigger has been verified MUST be permitted.
permit (principal is Scheduler, action == Action::"invoke", resource is Resource)
when { principal.cronVerified };
