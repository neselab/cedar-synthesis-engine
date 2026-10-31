Lab Result Release Permissions

A user with the ordering provider role may acknowledge a lab result only when its status is criticalHold and the user is its ordering provider. Authorized coverage waives only the requirement to be that result’s ordering provider; the ordering provider role and criticalHold status remain required.

A user may release a lab result only if they have the pathologist or ordering provider role, the result’s sensitivity is 0, 1, or 2, and they are not the result’s verifier. When sensitivity is 1 or 2, the user must have the pathologist role.

A user may release a lab result to the patient portal only if they have the pathologist or lab director role and have used multi-factor authentication. Both the user’s credential level and the result’s sensitivity must be 0, 1, or 2, and the credential level must be at least the sensitivity.

These are the only permissions: each activity is permitted exactly when all its stated requirements are met. Permissions are determined from current recorded facts and neither change record states nor establish an order between activities.
