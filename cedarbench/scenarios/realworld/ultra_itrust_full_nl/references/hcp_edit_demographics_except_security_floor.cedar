permit (principal is HealthCareProfessional, action == Action::"editDemographicInformation", resource is DemographicInformation) when {
    (context.session.isActive && context.session has healthCareProfessional && context.session.healthCareProfessional == principal && !context.includesSecurityQuestionOrPassword)
    && !(principal is HealthCareProfessional && context.includesSecurityQuestionOrPassword)
    && !(resource.patient.isDeactivated)
};