permit (principal is User, action == Action::"acknowledgeCritical", resource is LabResult)
when { (true && ((principal.roles.contains(Role::"OrderingProvider"))) && (!(true) || (principal == resource.orderingProvider) || (context.coverageAuthorized && (principal.roles.contains(Role::"OrderingProvider")))) && (!(true) || (resource.status == LabResultStatusValue::"criticalHold"))) };

permit (principal is User, action == Action::"releaseResult", resource is LabResult)
when { ((((resource.sensitivity == 0) || (resource.sensitivity == 1) || (resource.sensitivity == 2))) && ((principal.roles.contains(Role::"Pathologist") || principal.roles.contains(Role::"OrderingProvider"))) && (!(true) || (principal != resource.verifiedBy)) && (((context.releaseResultScheduledStart <= context.currentTime) && (context.currentTime < context.releaseResultScheduledEnd))) && (context.mfaUsed)) };

permit (principal is User, action == Action::"releaseToPortal", resource is LabResult)
when { ((((principal.credentialLevel == 0) || (principal.credentialLevel == 1) || (principal.credentialLevel == 2)) && ((resource.sensitivity == 0) || (resource.sensitivity == 1) || (resource.sensitivity == 2))) && ((principal.roles.contains(Role::"Pathologist") || principal.roles.contains(Role::"LabDirector"))) && (!(true) || (principal.credentialLevel >= resource.sensitivity))) };
