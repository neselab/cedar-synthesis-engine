// Policy store — verified policies appended here

// --- Verified (eval iteration 2) ---
forbid (
    principal,
    action in [
        Action::"createPatient",
        Action::"editPatientData",
        Action::"enterCredential",
        Action::"editCredential",
        Action::"viewCredential",
        Action::"createLhcp",
        Action::"createEmergencyResponder",
        Action::"createPublicHealthAgent",
        Action::"createUap",
        Action::"assignLhcpToHospital",
        Action::"requestPasswordChange",
        Action::"setInactivityPeriodLength",
        Action::"viewPriorAndDesignatedLhcps",
        Action::"addProviderToList",
        Action::"designateDlhcp",
        Action::"undesignateDlhcp",
        Action::"viewAccessLog",
        Action::"viewMedicalRecord",
        Action::"viewFamilyHistory",
        Action::"viewPersonalHealthInformation",
        Action::"viewImmunizations",
        Action::"viewOfficeVisitInformation"
    ],
    resource
)
when {
    context.session.isActive == false
};

forbid (principal, action == Action::"editPatientData", resource)
when {
    principal is Hcp &&
    resource is Patient &&
    context.fieldName == "mid"
};

forbid (
    principal,
    action in [
        Action::"enterCredential",
        Action::"editCredential",
        Action::"viewCredential"
    ],
    resource
)
when {
    principal is Hcp &&
    resource is Credential &&
    (
        context.credentialField == "password" ||
        context.credentialField == "securityQuestion" ||
        context.credentialField == "security question"
    )
};

permit (principal, action == Action::"createPatient", resource)
when {
    principal is Hcp &&
    resource is Patient
};

permit (principal, action == Action::"editPatientData", resource)
when {
    principal is Hcp &&
    resource is Patient
};

permit (principal, action == Action::"createLhcp", resource)
when {
    principal is Administrator &&
    resource is Lhcp
};

permit (principal, action == Action::"createEmergencyResponder", resource)
when {
    principal is Administrator &&
    resource is EmergencyResponder
};

permit (principal, action == Action::"createPublicHealthAgent", resource)
when {
    principal is Administrator &&
    resource is PublicHealthAgent
};

permit (principal, action == Action::"createUap", resource)
when {
    principal is Lhcp &&
    resource is Uap
};

permit (principal, action == Action::"assignLhcpToHospital", resource)
when {
    principal is Administrator &&
    resource is Lhcp
};

permit (principal, action == Action::"login", resource)
when {
    principal is User &&
    resource is Session &&
    resource.user == principal &&
    context.credential.user == principal &&
    context.enteredMid == principal.mid &&
    context.passwordVerified == true
};

permit (principal, action == Action::"requestPasswordChange", resource)
when {
    principal is User &&
    resource is Credential &&
    resource.user == principal
};

permit (principal, action == Action::"logout", resource)
when {
    principal is User &&
    resource is Session &&
    resource.user == principal &&
    resource.isActive == true
};

permit (principal, action == Action::"closeApplication", resource)
when {
    principal is User &&
    resource is Session &&
    resource.user == principal &&
    resource.isActive == true
};

permit (principal, action == Action::"setInactivityPeriodLength", resource)
when {
    principal is Administrator &&
    resource is Session
};

permit (principal, action == Action::"viewPriorAndDesignatedLhcps", resource)
when {
    principal is Patient &&
    resource is ProviderList &&
    resource.patient == principal
};

permit (principal, action == Action::"addProviderToList", resource)
when {
    principal is Patient &&
    resource is ProviderList &&
    resource.patient == principal &&
    context.provider.name == context.searchName &&
    (context has searchSpecialty) &&
    (context.provider has specialty) &&
    context.provider.specialty == context.searchSpecialty &&
    !(context has searchZipCode)
};

permit (principal, action == Action::"addProviderToList", resource)
when {
    principal is Patient &&
    resource is ProviderList &&
    resource.patient == principal &&
    context.provider.name == context.searchName &&
    (context has searchSpecialty) &&
    (context.provider has specialty) &&
    context.provider.specialty == context.searchSpecialty &&
    (context has searchZipCode) &&
    (context.provider has zipCode) &&
    context.provider.zipCode == context.searchZipCode
};

permit (principal, action == Action::"designateDlhcp", resource)
when {
    principal is Patient &&
    resource is ProviderDesignation &&
    resource.patient == principal
};

permit (principal, action == Action::"undesignateDlhcp", resource)
when {
    principal is Patient &&
    resource is ProviderDesignation &&
    resource.patient == principal &&
    resource.isDesignated == true
};

permit (principal, action == Action::"viewAccessLog", resource)
when {
    principal is Patient &&
    resource is AccessLog &&
    resource.patient == principal &&
    resource.accessTimestamp >= context.beginDate &&
    resource.accessTimestamp <= context.endDate
};

permit (principal, action == Action::"viewMedicalRecord", resource)
when {
    principal is Patient &&
    resource is MedicalRecord &&
    resource.patient == principal
};

permit (principal, action == Action::"viewMedicalRecord", resource)
when {
    principal is PersonalRepresentative &&
    resource is MedicalRecord &&
    resource.patient in principal.representedPatients
};

permit (principal, action == Action::"viewFamilyHistory", resource)
when {
    principal is Patient &&
    resource is MedicalRecord &&
    resource.patient == principal &&
    resource.hasFamilyHistory == true
};

permit (principal, action == Action::"viewFamilyHistory", resource)
when {
    principal is PersonalRepresentative &&
    resource is MedicalRecord &&
    resource.patient in principal.representedPatients &&
    resource.hasFamilyHistory == true
};

permit (principal, action == Action::"viewPersonalHealthInformation", resource)
when {
    principal is Patient &&
    resource is MedicalRecord &&
    resource.patient == principal &&
    resource.hasPersonalHealthInformation == true
};

permit (principal, action == Action::"viewPersonalHealthInformation", resource)
when {
    principal is PersonalRepresentative &&
    resource is MedicalRecord &&
    resource.patient in principal.representedPatients &&
    resource.hasPersonalHealthInformation == true
};

permit (principal, action == Action::"viewImmunizations", resource)
when {
    principal is Patient &&
    resource is MedicalRecord &&
    resource.patient == principal &&
    resource.hasImmunizations == true
};

permit (principal, action == Action::"viewImmunizations", resource)
when {
    principal is PersonalRepresentative &&
    resource is MedicalRecord &&
    resource.patient in principal.representedPatients &&
    resource.hasImmunizations == true
};

permit (principal, action == Action::"viewOfficeVisitInformation", resource)
when {
    principal is Patient &&
    resource is MedicalRecord &&
    resource.patient == principal &&
    resource.hasOfficeVisitInformation == true
};

permit (principal, action == Action::"viewOfficeVisitInformation", resource)
when {
    principal is PersonalRepresentative &&
    resource is MedicalRecord &&
    resource.patient in principal.representedPatients &&
    resource.hasOfficeVisitInformation == true
};
