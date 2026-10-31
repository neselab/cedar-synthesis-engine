Lab Result Release Access

A user may acknowledge a critical lab result only if they hold the ordering provider role, are the result’s recorded ordering provider, and make the request on the hospital network while the result has criticalHold status.

A user may release a lab result only if they hold the pathologist or ordering provider role, the result’s sensitivity is 0, 1, or 2, they are not the result’s recorded verifier, and they have used multi-factor authentication. When sensitivity is 2, the user must hold the pathologist role.

A user may release a lab result to the patient portal only if they hold the pathologist or lab director role, their credential level and the result’s sensitivity are each 0, 1, or 2, and their credential level is at least the result’s sensitivity. If the result is flagged as critical, the request must also indicate that the critical result has been acknowledged; this acknowledgment requirement applies only when that flag is true.

These are the only permissions, and each is sufficient only when all of its stated conditions are met. They are assessed using current recorded facts and neither change records nor require an order of execution.
