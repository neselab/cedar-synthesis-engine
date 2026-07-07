forbid (
    principal is HealthCareProfessional,
    action == Action::"editDemographicInformation",
    resource is DemographicInformation
)
when {
    context.includesSecurityQuestionOrPassword
};

forbid (
    principal is User,
    action == Action::"login",
    resource is Session
)
when {
    principal is Patient &&
    principal.isDeactivated
};

forbid (
    principal is User,
    action == Action::"requestPasswordChange",
    resource is User
)
when {
    resource is Patient &&
    resource.isDeactivated
};

forbid (
    principal,
    action == Action::"editDemographicInformation",
    resource is DemographicInformation
)
when {
    resource.patient.isDeactivated
};

forbid (
    principal,
    action == Action::"editPersonalHealthInformation",
    resource is MedicalRecord
)
when {
    resource.patient.isDeactivated
};

forbid (
    principal,
    action == Action::"editDiagnosticInformation",
    resource is DiagnosticInformation
)
when {
    resource.patient.isDeactivated
};

forbid (
    principal,
    action == Action::"modifyOfficeVisit",
    resource is OfficeVisit
)
when {
    resource.patient.isDeactivated
};

forbid (
    principal,
    action == Action::"deleteOfficeVisitFields",
    resource is OfficeVisit
)
when {
    resource.patient.isDeactivated
};

forbid (
    principal,
    action == Action::"toggleDesignatedLHCP",
    resource is LicensedHealthCareProfessional
)
when {
    context.patient.isDeactivated
};

forbid (
    principal,
    action == Action::"managePersonalRepresentative",
    resource is Patient
)
when {
    resource.isDeactivated
};

forbid (
    principal,
    action == Action::"recordLabProcedureResults",
    resource is LabProcedure
)
when {
    resource.patient.isDeactivated
};

permit (
    principal is User,
    action == Action::"login",
    resource is Session
)
when {
    resource.user == principal &&
    context.mid == principal.mid &&
    context.password == principal.password
};

permit (
    principal is User,
    action == Action::"requestPasswordChange",
    resource is User
)
when {
    context.session.isActive &&
    context.session.user == principal &&
    resource == principal
};

permit (
    principal is Administrator,
    action == Action::"assignCredentials",
    resource is LicensedHealthCareProfessional
)
when {
    context.session.isActive &&
    context.session has administrator &&
    context.session.administrator == principal
};

permit (
    principal is Administrator,
    action == Action::"reactivatePatient",
    resource is Patient
)
when {
    context.session.isActive &&
    context.session has administrator &&
    context.session.administrator == principal &&
    resource.isDeactivated
};

permit (
    principal is LicensedHealthCareProfessional,
    action == Action::"viewDiagnosticInformation",
    resource is DiagnosticInformation
)
when {
    context.session.isActive &&
    context.session has licensedHealthCareProfessional &&
    context.session.licensedHealthCareProfessional == principal &&
    principal in resource.allowedLHCPs
};

permit (
    principal is Patient,
    action == Action::"toggleDesignatedLHCP",
    resource is LicensedHealthCareProfessional
)
when {
    context.session.isActive &&
    context.session has patient &&
    context.session.patient == principal &&
    context.patient == principal
};

permit (
    principal is Patient,
    action == Action::"viewAccessLog",
    resource is AccessLog
)
when {
    context.session.isActive &&
    context.session has patient &&
    context.session.patient == principal &&
    resource.patient == principal
};

permit (
    principal is User,
    action == Action::"viewAccessLog",
    resource is AccessLog
)
when {
    context.session.isActive &&
    context.session.user == principal &&
    resource.patient.personalRepresentatives.contains(principal)
};

permit (
    principal is LicensedHealthCareProfessional,
    action == Action::"viewMedicalRecord",
    resource is MedicalRecord
)
when {
    context.session.isActive &&
    context.session has licensedHealthCareProfessional &&
    context.session.licensedHealthCareProfessional == principal &&
    principal in resource.patient.designatedLHCPs
};

permit (
    principal is UnlicensedPersonnel,
    action == Action::"viewMedicalRecord",
    resource is MedicalRecord
)
when {
    context.session.isActive &&
    context.session has unlicensedPersonnel &&
    context.session.unlicensedPersonnel == principal
};

permit (
    principal is User,
    action == Action::"viewMedicalRecord",
    resource is MedicalRecord
)
when {
    context.session.isActive &&
    context.session.user == principal &&
    (
        principal == resource.patient ||
        resource.patient.personalRepresentatives.contains(principal)
    )
};

permit (
    principal is User,
    action == Action::"editDemographicInformation",
    resource is DemographicInformation
)
when {
    context.session.isActive &&
    context.session.user == principal &&
    (
        principal == resource.patient ||
        resource.patient.personalRepresentatives.contains(principal)
    )
};

permit (
    principal is UnlicensedPersonnel,
    action == Action::"editDemographicInformation",
    resource is DemographicInformation
)
when {
    context.session.isActive &&
    context.session has unlicensedPersonnel &&
    context.session.unlicensedPersonnel == principal
};

permit (
    principal is HealthCareProfessional,
    action == Action::"editDemographicInformation",
    resource is DemographicInformation
)
when {
    context.session.isActive &&
    context.session has healthCareProfessional &&
    context.session.healthCareProfessional == principal &&
    !context.includesSecurityQuestionOrPassword
};

permit (
    principal is UnlicensedPersonnel,
    action == Action::"editDiagnosticInformation",
    resource is DiagnosticInformation
)
when {
    context.session.isActive &&
    context.session has unlicensedPersonnel &&
    context.session.unlicensedPersonnel == principal
};

permit (
    principal is HealthCareProfessional,
    action == Action::"editPersonalHealthInformation",
    resource is MedicalRecord
)
when {
    context.session.isActive &&
    context.session has healthCareProfessional &&
    context.session.healthCareProfessional == principal
};

permit (
    principal is UnlicensedPersonnel,
    action == Action::"editPersonalHealthInformation",
    resource is MedicalRecord
)
when {
    context.session.isActive &&
    context.session has unlicensedPersonnel &&
    context.session.unlicensedPersonnel == principal
};

permit (
    principal is HealthCareProfessional,
    action == Action::"modifyOfficeVisit",
    resource is OfficeVisit
)
when {
    context.session.isActive &&
    context.session has healthCareProfessional &&
    context.session.healthCareProfessional == principal
};

permit (
    principal is UnlicensedPersonnel,
    action == Action::"modifyOfficeVisit",
    resource is OfficeVisit
)
when {
    context.session.isActive &&
    context.session has unlicensedPersonnel &&
    context.session.unlicensedPersonnel == principal
};

permit (
    principal is HealthCareProfessional,
    action == Action::"deleteOfficeVisitFields",
    resource is OfficeVisit
)
when {
    context.session.isActive &&
    context.session has healthCareProfessional &&
    context.session.healthCareProfessional == principal
};

permit (
    principal is HealthCareProfessional,
    action == Action::"managePersonalRepresentative",
    resource is Patient
)
when {
    context.session.isActive &&
    context.session has healthCareProfessional &&
    context.session.healthCareProfessional == principal
};

permit (
    principal is LicensedHealthCareProfessional,
    action == Action::"viewEmergencyReport",
    resource is EmergencyReport
)
when {
    context.session.isActive &&
    context.session has licensedHealthCareProfessional &&
    context.session.licensedHealthCareProfessional == principal &&
    context.mid == resource.patient.mid
};

permit (
    principal is EmergencyResponder,
    action == Action::"viewEmergencyReport",
    resource is EmergencyReport
)
when {
    context.session.isActive &&
    context.session has emergencyResponder &&
    context.session.emergencyResponder == principal &&
    context.mid == resource.patient.mid
};

permit (
    principal is LicensedHealthCareProfessional,
    action == Action::"requestComprehensivePatientReport",
    resource is ComprehensivePatientReport
)
when {
    context.session.isActive &&
    context.session has licensedHealthCareProfessional &&
    context.session.licensedHealthCareProfessional == principal
};

permit (
    principal is Patient,
    action == Action::"viewLabProcedureResults",
    resource is LabProcedure
)
when {
    context.session.isActive &&
    context.session has patient &&
    context.session.patient == principal &&
    resource.patient == principal
};

permit (
    principal is User,
    action == Action::"viewLabProcedureResults",
    resource is LabProcedure
)
when {
    context.session.isActive &&
    context.session.user == principal &&
    resource.patient.personalRepresentatives.contains(principal)
};

permit (
    principal is LabTechnician,
    action == Action::"viewLabProcedureQueue",
    resource is LabProcedure
)
when {
    context.session.isActive &&
    context.session has labTechnician &&
    context.session.labTechnician == principal &&
    resource has assignedTechnician &&
    resource.assignedTechnician == principal
};

permit (
    principal is LabTechnician,
    action == Action::"recordLabProcedureResults",
    resource is LabProcedure
)
when {
    context.session.isActive &&
    context.session has labTechnician &&
    context.session.labTechnician == principal
};

permit (
    principal is PublicHealthAgent,
    action == Action::"viewAdverseEventReport",
    resource is AdverseEventReport
)
when {
    context.session.isActive &&
    context.session has publicHealthAgent &&
    context.session.publicHealthAgent == principal
};

permit (
    principal is PublicHealthAgent,
    action == Action::"respondToAdverseEventReport",
    resource is AdverseEventReport
)
when {
    context.session.isActive &&
    context.session has publicHealthAgent &&
    context.session.publicHealthAgent == principal
};

permit (
    principal is Patient,
    action == Action::"viewOfficeVisitInformation",
    resource is OfficeVisit
)
when {
    context.session.isActive &&
    context.session has patient &&
    context.session.patient == principal &&
    resource.patient == principal &&
    !context.includesNotes
};

permit (
    principal is User,
    action == Action::"viewOfficeVisitInformation",
    resource is OfficeVisit
)
when {
    context.session.isActive &&
    context.session.user == principal &&
    resource.patient.personalRepresentatives.contains(principal) &&
    !context.includesNotes
};

permit (
    principal is Patient,
    action == Action::"viewImmunizationInformation",
    resource is Immunization
)
when {
    context.session.isActive &&
    context.session has patient &&
    context.session.patient == principal &&
    resource.patient == principal
};

permit (
    principal is User,
    action == Action::"viewImmunizationInformation",
    resource is Immunization
)
when {
    context.session.isActive &&
    context.session.user == principal &&
    resource.patient.personalRepresentatives.contains(principal)
};

permit (
    principal is LicensedHealthCareProfessional,
    action == Action::"sendMessage",
    resource is Message
)
when {
    context.session.isActive &&
    context.session has licensedHealthCareProfessional &&
    context.session.licensedHealthCareProfessional == principal &&
    resource.sender == principal &&
    resource has patient &&
    resource.patient == context.patient &&
    principal in context.patient.designatedLHCPs &&
    resource has patientRecipient &&
    resource.patientRecipient == context.patient &&
    !(resource has personalRepresentativeRecipient) &&
    !(resource has lhcpRecipient)
};

permit (
    principal is LicensedHealthCareProfessional,
    action == Action::"sendMessage",
    resource is Message
)
when {
    context.session.isActive &&
    context.session has licensedHealthCareProfessional &&
    context.session.licensedHealthCareProfessional == principal &&
    resource.sender == principal &&
    resource has patient &&
    resource.patient == context.patient &&
    principal in context.patient.designatedLHCPs &&
    resource has personalRepresentativeRecipient &&
    resource.personalRepresentativeRecipient in context.patient.personalRepresentatives &&
    !(resource has patientRecipient) &&
    !(resource has lhcpRecipient)
};

permit (
    principal is User,
    action == Action::"sendMessage",
    resource is Message
)
when {
    context.session.isActive &&
    context.session.user == principal &&
    resource.sender == principal &&
    resource has patient &&
    resource.patient == context.patient &&
    resource has lhcpRecipient &&
    context.patient.designatedLHCPs.contains(resource.lhcpRecipient) &&
    (
        principal == context.patient ||
        context.patient.personalRepresentatives.contains(principal)
    ) &&
    !(resource has patientRecipient) &&
    !(resource has personalRepresentativeRecipient)
};
