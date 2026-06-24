// Policy store — verified policies appended here

// --- Verified (eval iteration 2) ---
permit (
    principal,
    action == Action::"viewAccessLog",
    resource
)
when {
    principal is Patient &&
    resource is AccessLog &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient == principal &&
    resource.patient == principal
};

permit (
    principal,
    action == Action::"viewAccessLog",
    resource
)
when {
    principal is PersonalRepresentative &&
    resource is AccessLog &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient in principal.representedPatients &&
    resource.patient == context.patient
};

permit (
    principal,
    action == Action::"viewMedicalRecord",
    resource
)
when {
    principal is Patient &&
    resource is MedicalRecord &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient == principal &&
    resource.patient == principal
};

permit (
    principal,
    action == Action::"viewMedicalRecord",
    resource
)
when {
    principal is PersonalRepresentative &&
    resource is MedicalRecord &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient in principal.representedPatients &&
    resource.patient == context.patient
};

permit (
    principal,
    action == Action::"viewDiagnosticInformation",
    resource
)
when {
    principal is LHCP &&
    resource is DiagnosticInformation &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient == resource.patient &&
    principal in resource.allowedViewers
};

permit (
    principal,
    action == Action::"viewPersonalHealthInformation",
    resource
)
when {
    principal is Patient &&
    resource is PersonalHealthInformation &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient == principal &&
    resource.patient == principal
};

permit (
    principal,
    action == Action::"viewPersonalHealthInformation",
    resource
)
when {
    principal is PersonalRepresentative &&
    resource is PersonalHealthInformation &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient in principal.representedPatients &&
    resource.patient == context.patient
};

permit (
    principal,
    action == Action::"viewFamilyHistory",
    resource
)
when {
    principal is Patient &&
    resource is FamilyHistory &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient == principal &&
    resource.patient == principal
};

permit (
    principal,
    action == Action::"viewFamilyHistory",
    resource
)
when {
    principal is PersonalRepresentative &&
    resource is FamilyHistory &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient in principal.representedPatients &&
    resource.patient == context.patient
};

permit (
    principal,
    action == Action::"viewImmunization",
    resource
)
when {
    principal is Patient &&
    resource is Immunization &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient == principal &&
    resource.patient == principal
};

permit (
    principal,
    action == Action::"viewImmunization",
    resource
)
when {
    principal is PersonalRepresentative &&
    resource is Immunization &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient in principal.representedPatients &&
    resource.patient == context.patient
};

permit (
    principal,
    action == Action::"viewOfficeVisit",
    resource
)
when {
    principal is Patient &&
    resource is OfficeVisit &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient == principal &&
    resource.patient == principal
};

permit (
    principal,
    action == Action::"viewOfficeVisit",
    resource
)
when {
    principal is PersonalRepresentative &&
    resource is OfficeVisit &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient in principal.representedPatients &&
    resource.patient == context.patient
};

permit (
    principal,
    action == Action::"takeOfficeVisitSurvey",
    resource
)
when {
    principal is Patient &&
    resource is OfficeVisit &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient == principal &&
    resource.patient == principal &&
    resource.surveyTaken == false
};

permit (
    principal,
    action == Action::"takeOfficeVisitSurvey",
    resource
)
when {
    principal is PersonalRepresentative &&
    resource is OfficeVisit &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.patient in principal.representedPatients &&
    resource.patient == context.patient &&
    resource.surveyTaken == false
};

permit (
    principal,
    action == Action::"createPatient",
    resource
)
when {
    principal is HCP &&
    resource is Patient &&
    context.session.isActive == true &&
    context.session.user == principal
};

permit (
    principal,
    action == Action::"disablePatient",
    resource
)
when {
    principal is HCP &&
    resource is Patient &&
    context.session.isActive == true &&
    context.session.user == principal
};

permit (
    principal,
    action == Action::"reactivatePatient",
    resource
)
when {
    principal is Administrator &&
    resource is Patient &&
    context.session.isActive == true &&
    context.session.user == principal &&
    resource.isActive == false
};

permit (
    principal,
    action == Action::"createLHCP",
    resource
)
when {
    principal is Administrator &&
    resource is LHCP &&
    context.session.isActive == true &&
    context.session.user == principal
};

permit (
    principal,
    action == Action::"createEmergencyResponder",
    resource
)
when {
    principal is Administrator &&
    resource is EmergencyResponder &&
    context.session.isActive == true &&
    context.session.user == principal
};

permit (
    principal,
    action == Action::"createLabTechnician",
    resource
)
when {
    principal is Administrator &&
    resource is LabTechnician &&
    context.session.isActive == true &&
    context.session.user == principal
};

permit (
    principal,
    action == Action::"createPublicHealthAgent",
    resource
)
when {
    principal is Administrator &&
    resource is PublicHealthAgent &&
    context.session.isActive == true &&
    context.session.user == principal
};

permit (
    principal,
    action == Action::"createUAP",
    resource
)
when {
    principal is LHCP &&
    resource is UAP &&
    context.session.isActive == true &&
    context.session.user == principal
};

permit (
    principal,
    action == Action::"assignCredentials",
    resource
)
when {
    principal is Administrator &&
    resource is LHCP &&
    context.session.isActive == true &&
    context.session.user == principal
};

permit (
    principal,
    action == Action::"assignHospital",
    resource
)
when {
    principal is Administrator &&
    resource is LHCP &&
    context.session.isActive == true &&
    context.session.user == principal &&
    context.hospital in context.hospitalList.hospitals
};

permit (
    principal,
    action == Action::"viewLhcps",
    resource
)
when {
    principal is Patient &&
    resource is Patient &&
    context.session.isActive == true &&
    context.session.user == principal &&
    resource == principal
};

permit (
    principal,
    action == Action::"addProvider",
    resource
)
when {
    principal is Patient &&
    resource is Patient &&
    context.session.isActive == true &&
    context.session.user == principal &&
    resource == principal
};

permit (
    principal,
    action == Action::"designateLHCP",
    resource
)
when {
    principal is Patient &&
    resource is ProviderDesignation &&
    context.session.isActive == true &&
    context.session.user == principal &&
    resource.patient == principal
};

permit (
    principal,
    action == Action::"undesignateLHCP",
    resource
)
when {
    principal is Patient &&
    resource is ProviderDesignation &&
    context.session.isActive == true &&
    context.session.user == principal &&
    resource.patient == principal
};

permit (
    principal,
    action == Action::"editPersonalHealthInformation",
    resource
)
when {
    principal is HCP &&
    resource is PersonalHealthInformation &&
    context.session.isActive == true &&
    context.session.user == principal &&
    resource.patient == context.patient &&
    context.patient.isActive == true
};
