// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is HCP,
    action == Action::"createPatient",
    resource is Patient
);

permit (
    principal is HCP,
    action == Action::"editPatientData",
    resource is Patient
)
when {
    context.editedField != "mid"
};

permit (
    principal is Administrator,
    action == Action::"createLHCP",
    resource is LHCP
)
when {
    resource.specialty != ""
};

permit (
    principal is Administrator,
    action == Action::"createEmergencyResponder",
    resource is EmergencyResponder
);

permit (
    principal is Administrator,
    action == Action::"createPublicHealthAgent",
    resource is PublicHealthAgent
);

permit (
    principal is Administrator,
    action == Action::"assignLHCPToHospitals",
    resource is LHCP
)
when {
    context.assignsMultipleHospitals == true
};

permit (
    principal is LHCP,
    action == Action::"createUAP",
    resource is UAP
);

permit (
    principal,
    action == Action::"login",
    resource is Session
)
when {
    resource.user == principal &&
    context.mid == principal.mid &&
    context.password == principal.password
};

permit (
    principal,
    action == Action::"requestPasswordChange",
    resource
)
when {
    principal == resource
};

permit (
    principal,
    action == Action::"logout",
    resource is Session
)
when {
    resource.user == principal &&
    resource.isAuthenticated == true
};

permit (
    principal,
    action == Action::"closeApplication",
    resource is Session
)
when {
    resource.user == principal &&
    resource.isAuthenticated == true
};

permit (
    principal is Administrator,
    action == Action::"setInactivityPeriodLength",
    resource is SystemConfiguration
);

permit (
    principal is Patient,
    action == Action::"viewPastAndDesignatedLHCPs",
    resource is Patient
)
when {
    principal == resource
};

permit (
    principal is Patient,
    action == Action::"searchProviders",
    resource is ProviderSearch
)
when {
    resource.name != "" &&
    resource.specialty != "" &&
    (if resource has zipCode then resource.zipCode != "" else true)
};

permit (
    principal is Patient,
    action == Action::"addProviderToList",
    resource is Patient
)
when {
    principal == resource
};

permit (
    principal is Patient,
    action == Action::"designateDLHCP",
    resource is Patient
)
when {
    principal == resource
};

permit (
    principal is Patient,
    action == Action::"undesignateDLHCP",
    resource is Patient
)
when {
    principal == resource
};

permit (
    principal is Patient,
    action == Action::"viewAccessLog",
    resource is AccessLog
)
when {
    resource.patient == principal &&
    context.beginDate <= context.endDate
};

permit (
    principal is Patient,
    action == Action::"viewMedicalRecord",
    resource is MedicalRecord
)
when {
    resource.patient == principal
};

permit (
    principal is PersonalRepresentative,
    action == Action::"viewMedicalRecord",
    resource is MedicalRecord
)
when {
    principal in resource.patient.personalRepresentatives
};

permit (
    principal is Patient,
    action == Action::"seeRecordHealthInformation",
    resource is MedicalRecord
)
when {
    resource.patient == principal &&
    (
        (context.informationCategory == "personalHealthInformation" && resource.hasPersonalHealthInformation == true) ||
        (context.informationCategory == "immunizations" && resource.hasImmunizations == true) ||
        (context.informationCategory == "officeVisitInformation" && resource.hasOfficeVisitInformation == true)
    )
};

permit (
    principal is PersonalRepresentative,
    action == Action::"seeRecordHealthInformation",
    resource is MedicalRecord
)
when {
    principal in resource.patient.personalRepresentatives &&
    (
        (context.informationCategory == "personalHealthInformation" && resource.hasPersonalHealthInformation == true) ||
        (context.informationCategory == "immunizations" && resource.hasImmunizations == true) ||
        (context.informationCategory == "officeVisitInformation" && resource.hasOfficeVisitInformation == true)
    )
};
