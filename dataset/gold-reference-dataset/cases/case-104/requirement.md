Lab Result Release Access

These are the only permissions for users to acknowledge critical lab results, release lab results, or release lab results to the patient portal; each permission requires all conditions stated for that activity. Decisions use current recorded facts and trusted application context, without changing records or imposing an order between activities. Users may hold multiple roles.

Acknowledging a critical lab result

The user must hold the ordering provider role and be the result’s recorded ordering provider. Authorized coverage waives only the requirement to be the recorded ordering provider, not the role requirement or the timing requirement. The recorded critical notification time must be no later than the request’s current time and no more than 15 minutes earlier, including both endpoints. Times are measured in UTC.

Releasing a lab result

The user must hold the pathologist or ordering provider role, or must hold the medical technologist role, be the result’s recorded verifier, and have emergency release enabled for the request. The result’s sensitivity must be 0, 1, or 2. The user must differ from the recorded verifier unless the user holds the medical technologist role, is the recorded verifier, and has emergency release enabled; this exception waives only the requirement to differ from the verifier. If the result is flagged as critical, the critical release review must be completed. That review duty applies only when the critical flag is true, and the emergency exception does not waive it or any other requirement.

Releasing a lab result to the patient portal

The user must hold the pathologist or lab director role. The user’s credential level and the result’s sensitivity must each be 0, 1, or 2, and the result’s recorded status must be released.
