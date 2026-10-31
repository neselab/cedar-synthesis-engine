Lab Result Release Permissions

These are the only permissions for users to acknowledge critical lab results, release lab results, or release lab results to the patient portal; each permission requires all conditions stated for that activity. They do not change records or require an order of activities.

A user may acknowledge a critical lab result only if the user holds the ordering provider role and the result is in criticalHold status. The user must also be the result’s ordering provider unless coverage is authorized. Authorized coverage waives only the ordering-provider relationship requirement; the role and status requirements still apply.

A user may release a lab result only if the user holds the pathologist or ordering provider role, the result’s sensitivity is 0, 1, or 2, and the user is not the result’s verifier. The user must have used multi-factor authentication. The request’s current time must be at or after its scheduled release start and strictly before its scheduled release end, with all times measured in UTC.

A user may release a lab result to the patient portal only if the user holds the pathologist or lab director role. Both the user’s credential level and the result’s sensitivity must be 0, 1, or 2, and the credential level must be at least the sensitivity.
