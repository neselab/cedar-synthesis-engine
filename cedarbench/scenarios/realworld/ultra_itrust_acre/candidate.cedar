permit (principal, action == Action::"viewAccessLog", resource) when { context.session.isActive && context.session has patientUser && context.session.patientUser == principal && context.patient == principal && resource.patient == principal };

permit (principal, action == Action::"viewAccessLog", resource) when { context.session.isActive && context.session has personalRepresentativeUser && context.session.personalRepresentativeUser == principal && context.patient == resource.patient && principal.representedPatients.contains(resource.patient) };

permit (principal, action == Action::"viewMedicalRecord", resource) when { context.session.isActive && context.session has patientUser && context.session.patientUser == principal && context.patient == principal && resource.patient == principal };

permit (principal, action == Action::"viewMedicalRecord", resource) when { context.session.isActive && context.session has personalRepresentativeUser && context.session.personalRepresentativeUser == principal && context.patient == resource.patient && principal.representedPatients.contains(resource.patient) };

permit (principal, action == Action::"viewFamilyHistory", resource) when { context.session.isActive && context.session has patientUser && context.session.patientUser == principal && context.patient == principal && resource.patient == principal };

permit (principal, action == Action::"viewFamilyHistory", resource) when { context.session.isActive && context.session has personalRepresentativeUser && context.session.personalRepresentativeUser == principal && context.patient == resource.patient && principal.representedPatients.contains(resource.patient) };

permit (principal, action == Action::"viewPersonalHealthInformation", resource) when { context.session.isActive && context.session has patientUser && context.session.patientUser == principal && context.patient == principal && resource.patient == principal };

permit (principal, action == Action::"viewPersonalHealthInformation", resource) when { context.session.isActive && context.session has personalRepresentativeUser && context.session.personalRepresentativeUser == principal && context.patient == resource.patient && principal.representedPatients.contains(resource.patient) };

permit (principal, action == Action::"viewImmunization", resource) when { context.session.isActive && context.session has patientUser && context.session.patientUser == principal && context.patient == principal && resource.patient == principal };

permit (principal, action == Action::"viewImmunization", resource) when { context.session.isActive && context.session has personalRepresentativeUser && context.session.personalRepresentativeUser == principal && context.patient == resource.patient && principal.representedPatients.contains(resource.patient) };

permit (principal, action == Action::"viewOfficeVisit", resource) when { context.session.isActive && context.session has patientUser && context.session.patientUser == principal && context.patient == principal && resource.patient == principal };

permit (principal, action == Action::"viewOfficeVisit", resource) when { context.session.isActive && context.session has personalRepresentativeUser && context.session.personalRepresentativeUser == principal && context.patient == resource.patient && principal.representedPatients.contains(resource.patient) };

permit (principal, action == Action::"takeOfficeVisitSurvey", resource) when { context.session.isActive && context.session has patientUser && context.session.patientUser == principal && context.patient == principal && resource.patient == principal && !resource.surveyTaken };

permit (principal, action == Action::"takeOfficeVisitSurvey", resource) when { context.session.isActive && context.session has personalRepresentativeUser && context.session.personalRepresentativeUser == principal && context.patient == resource.patient && principal.representedPatients.contains(resource.patient) && !resource.surveyTaken };

permit (principal, action == Action::"viewDiagnosticInformation", resource) when { context.session.isActive && context.session has lhcpUser && context.session.lhcpUser == principal && context.patient == resource.patient && resource.allowedViewers.contains(principal) };

permit (principal, action == Action::"restrictDiagnosticInformation", resource) when { context.session.isActive && context.session has patientUser && context.session.patientUser == principal && resource.patient == principal && resource.restrictionAllowed };

permit (principal, action == Action::"determineDiagnosisRestrictionAllowed", resource) when { context.session.isActive && context.session has lhcpUser && context.session.lhcpUser == principal };

permit (principal, action == Action::"createPatient", resource) when { context.session.isActive && context.session has hcpUser && context.session.hcpUser == principal };

permit (principal, action == Action::"disablePatient", resource) when { context.session.isActive && context.session has hcpUser && context.session.hcpUser == principal };

permit (principal, action == Action::"reactivatePatient", resource) when { context.session.isActive && context.session has administratorUser && context.session.administratorUser == principal && !resource.isActive };

permit (principal, action == Action::"editPatient", resource) when { context.session.isActive && context.session has hcpUser && context.session.hcpUser == principal && resource.isActive };

permit (principal, action == Action::"createLHCP", resource) when { context.session.isActive && context.session has administratorUser && context.session.administratorUser == principal };

permit (principal, action == Action::"createEmergencyResponder", resource) when { context.session.isActive && context.session has administratorUser && context.session.administratorUser == principal };

permit (principal, action == Action::"createLabTechnician", resource) when { context.session.isActive && context.session has administratorUser && context.session.administratorUser == principal };

permit (principal, action == Action::"createPublicHealthAgent", resource) when { context.session.isActive && context.session has administratorUser && context.session.administratorUser == principal };

permit (principal, action == Action::"createUAP", resource) when { context.session.isActive && context.session has lhcpUser && context.session.lhcpUser == principal };

permit (principal, action == Action::"assignCredentials", resource) when { context.session.isActive && context.session has administratorUser && context.session.administratorUser == principal };

permit (principal, action == Action::"setInactivityPeriod", resource) when { context.session.isActive && context.session has administratorUser && context.session.administratorUser == principal };

permit (principal, action == Action::"assignHospital", resource) when { context.session.isActive && context.session has administratorUser && context.session.administratorUser == principal && context.hospitalList.hospitals.contains(context.hospital) };

permit (principal, action == Action::"viewLhcps", resource) when { context.session.isActive && context.session has patientUser && context.session.patientUser == principal && resource == principal };

permit (principal, action == Action::"addProvider", resource) when { context.session.isActive && context.session has patientUser && context.session.patientUser == principal && resource == principal };

permit (principal, action == Action::"designateLHCP", resource) when { context.session.isActive && context.session has patientUser && context.session.patientUser == principal && resource.patient == principal };

permit (principal, action == Action::"undesignateLHCP", resource) when { context.session.isActive && context.session has patientUser && context.session.patientUser == principal && resource.patient == principal };

permit (principal, action == Action::"editPersonalHealthInformation", resource) when { context.session.isActive && context.session has hcpUser && context.session.hcpUser == principal && context.patient == resource.patient && resource.patient.isActive };

permit (principal, action == Action::"editImmunization", resource) when { context.session.isActive && context.session has hcpUser && context.session.hcpUser == principal && context.patient == resource.patient && resource.patient.isActive };

permit (principal, action == Action::"editFamilyHistory", resource) when { context.session.isActive && context.session has hcpUser && context.session.hcpUser == principal && context.patient == resource.patient && resource.patient.isActive };

permit (principal, action == Action::"documentOfficeVisit", resource) when { context.session.isActive && context.session has hcpUser && context.session.hcpUser == principal && context.patient == resource.patient && resource.patient.isActive };

permit (principal, action == Action::"editOfficeVisit", resource) when { context.session.isActive && context.session has hcpUser && context.session.hcpUser == principal && context.patient == resource.patient && resource.patient.isActive };

permit (principal, action == Action::"addPersonalRepresentative", resource) when { context.session.isActive && context.session has hcpUser && context.session.hcpUser == principal && context.patient == resource.patient && resource.patient.isActive };

permit (principal, action == Action::"removePersonalRepresentative", resource) when { context.session.isActive && context.session has hcpUser && context.session.hcpUser == principal && context.patient == resource.patient && resource.patient.isActive };

permit (principal, action == Action::"enterDemographicInformation", resource) when { context.session.isActive && context.session has uapUser && context.session.uapUser == principal && context.patient == resource.patient && resource.patient.isActive };

permit (principal, action == Action::"editDemographicInformation", resource) when { context.session.isActive && context.session has uapUser && context.session.uapUser == principal && context.patient == resource.patient && resource.patient.isActive };

permit (principal, action == Action::"viewMedicalRecord", resource) when { context.session.isActive && context.session has uapUser && context.session.uapUser == principal && context.patient == resource.patient };
