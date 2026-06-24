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
    context.session has patientUser &&
    context.session.patientUser == principal &&
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
    context.session has personalRepresentativeUser &&
    context.session.personalRepresentativeUser == principal &&
    resource.patient == context.patient &&
    principal.representedPatients.contains(context.patient)
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
    context.session has patientUser &&
    context.session.patientUser == principal &&
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
    context.session has personalRepresentativeUser &&
    context.session.personalRepresentativeUser == principal &&
    resource.patient == context.patient &&
    principal.representedPatients.contains(context.patient)
};

permit (
    principal,
    action == Action::"viewMedicalRecord",
    resource
)
when {
    principal is UAP &&
    resource is MedicalRecord &&
    context.session.isActive == true &&
    context.session has uapUser &&
    context.session.uapUser == principal &&
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
    context.session has patientUser &&
    context.session.patientUser == principal &&
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
    context.session has personalRepresentativeUser &&
    context.session.personalRepresentativeUser == principal &&
    resource.patient == context.patient &&
    principal.representedPatients.contains(context.patient)
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
    context.session has patientUser &&
    context.session.patientUser == principal &&
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
    context.session has personalRepresentativeUser &&
    context.session.personalRepresentativeUser == principal &&
    resource.patient == context.patient &&
    principal.representedPatients.contains(context.patient)
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
    context.session has patientUser &&
    context.session.patientUser == principal &&
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
    context.session has personalRepresentativeUser &&
    context.session.personalRepresentativeUser == principal &&
    resource.patient == context.patient &&
    principal.representedPatients.contains(context.patient)
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
    context.session has patientUser &&
    context.session.patientUser == principal &&
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
    context.session has personalRepresentativeUser &&
    context.session.personalRepresentativeUser == principal &&
    resource.patient == context.patient &&
    principal.representedPatients.contains(context.patient)
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
    context.session has patientUser &&
    context.session.patientUser == principal &&
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
    context.session has personalRepresentativeUser &&
    context.session.personalRepresentativeUser == principal &&
    resource.patient == context.patient &&
    principal.representedPatients.contains(context.patient) &&
    resource.surveyTaken == false
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
    context.session has lhcpUser &&
    context.session.lhcpUser == principal &&
    resource.patient == context.patient &&
    resource.allowedViewers.contains(principal)
};

permit (
    principal,
    action == Action::"restrictDiagnosticInformation",
    resource
)
when {
    principal is Patient &&
    resource is DiagnosticInformation &&
    context.session.isActive == true &&
    context.session has patientUser &&
    context.session.patientUser == principal &&
    resource.patient == principal &&
    resource.restrictionAllowed == true
};

permit (
    principal,
    action == Action::"determineDiagnosisRestrictionAllowed",
    resource
)
when {
    principal is LHCP &&
    resource is DiagnosticInformation &&
    context.session.isActive == true &&
    context.session has lhcpUser &&
    context.session.lhcpUser == principal
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
    context.session has hcpUser &&
    context.session.hcpUser == principal
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
    context.session has hcpUser &&
    context.session.hcpUser == principal
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
    context.session has administratorUser &&
    context.session.administratorUser == principal &&
    resource.isActive == false
};

permit (
    principal,
    action == Action::"editPatient",
    resource
)
when {
    principal is HCP &&
    resource is Patient &&
    context.session.isActive == true &&
    context.session has hcpUser &&
    context.session.hcpUser == principal &&
    resource.isActive == true
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
    context.session has administratorUser &&
    context.session.administratorUser == principal
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
    context.session has administratorUser &&
    context.session.administratorUser == principal
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
    context.session has administratorUser &&
    context.session.administratorUser == principal
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
    context.session has administratorUser &&
    context.session.administratorUser == principal
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
    context.session has lhcpUser &&
    context.session.lhcpUser == principal
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
    context.session has administratorUser &&
    context.session.administratorUser == principal
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
    context.session has administratorUser &&
    context.session.administratorUser == principal &&
    context.hospitalList.hospitals.contains(context.hospital)
};

permit (
    principal,
    action == Action::"setInactivityPeriod",
    resource
)
when {
    principal is Administrator &&
    resource is SystemSettings &&
    context.session.isActive == true &&
    context.session has administratorUser &&
    context.session.administratorUser == principal
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
    context.session has patientUser &&
    context.session.patientUser == principal &&
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
    context.session has patientUser &&
    context.session.patientUser == principal &&
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
    context.session has patientUser &&
    context.session.patientUser == principal &&
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
    context.session has patientUser &&
    context.session.patientUser == principal &&
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
    context.session has hcpUser &&
    context.session.hcpUser == principal &&
    resource.patient == context.patient &&
    resource.patient.isActive == true
};

permit (
    principal,
    action == Action::"editImmunization",
    resource
)
when {
    principal is HCP &&
    resource is Immunization &&
    context.session.isActive == true &&
    context.session has hcpUser &&
    context.session.hcpUser == principal &&
    resource.patient == context.patient &&
    resource.patient.isActive == true
};

permit (
    principal,
    action == Action::"editFamilyHistory",
    resource
)
when {
    principal is HCP &&
    resource is FamilyHistory &&
    context.session.isActive == true &&
    context.session has hcpUser &&
    context.session.hcpUser == principal &&
    resource.patient == context.patient &&
    resource.patient.isActive == true
};

permit (
    principal,
    action == Action::"documentOfficeVisit",
    resource
)
when {
    principal is HCP &&
    resource is OfficeVisit &&
    context.session.isActive == true &&
    context.session has hcpUser &&
    context.session.hcpUser == principal &&
    resource.patient == context.patient &&
    resource.patient.isActive == true
};

permit (
    principal,
    action == Action::"editOfficeVisit",
    resource
)
when {
    principal is HCP &&
    resource is OfficeVisit &&
    context.session.isActive == true &&
    context.session has hcpUser &&
    context.session.hcpUser == principal &&
    resource.patient == context.patient &&
    resource.patient.isActive == true
};

permit (
    principal,
    action == Action::"addPersonalRepresentative",
    resource
)
when {
    principal is HCP &&
    resource is PersonalRepresentativeRelationship &&
    context.session.isActive == true &&
    context.session has hcpUser &&
    context.session.hcpUser == principal &&
    resource.patient == context.patient &&
    resource.patient.isActive == true
};

permit (
    principal,
    action == Action::"removePersonalRepresentative",
    resource
)
when {
    principal is HCP &&
    resource is PersonalRepresentativeRelationship &&
    context.session.isActive == true &&
    context.session has hcpUser &&
    context.session.hcpUser == principal &&
    resource.patient == context.patient &&
    resource.patient.isActive == true
};

permit (
    principal,
    action == Action::"enterDemographicInformation",
    resource
)
when {
    principal is UAP &&
    resource is DemographicInformation &&
    context.session.isActive == true &&
    context.session has uapUser &&
    context.session.uapUser == principal &&
    resource.patient == context.patient &&
    resource.patient.isActive == true
};

permit (
    principal,
    action == Action::"editDemographicInformation",
    resource
)
when {
    principal is UAP &&
    resource is DemographicInformation &&
    context.session.isActive == true &&
    context.session has uapUser &&
    context.session.uapUser == principal &&
    resource.patient == context.patient &&
    resource.patient.isActive == true
};
