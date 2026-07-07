permit (principal is HealthCareProfessional, action == Action::"editDemographicInformation", resource is DemographicInformation) when {
    (context.session.isActive && context.session has healthCareProfessional && context.session.healthCareProfessional == principal && context.mid == resource.patient.mid && !context.includesSecurityQuestionOrPassword)
    && !(principal is HealthCareProfessional && context.includesSecurityQuestionOrPassword)
    && !(resource.patient.isDeactivated)
};