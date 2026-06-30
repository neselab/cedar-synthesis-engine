// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
forbid (principal is User, action, resource is Resource)
when {
    principal.isSuspended
};

forbid (principal is User, action == Action::"access", resource is Resource)
when {
    context.outsideBusinessHours
};

forbid (principal is User, action, resource is Resource)
when {
    resource.isClassified && !principal.mfaVerified
};

forbid (principal is User, action == Action::"access", resource is Resource)
when {
    resource.requiresApproval && !context.approvalGranted
};

permit (principal is User, action == Action::"access", resource is Resource);

permit (principal is User, action == Action::"view", resource is Resource);
