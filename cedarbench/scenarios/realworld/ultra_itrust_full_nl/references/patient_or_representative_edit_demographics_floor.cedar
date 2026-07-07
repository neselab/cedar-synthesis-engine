permit (principal, action == Action::"editDemographicInformation", resource is DemographicInformation) when {
    (context.session.isActive && ((principal is Patient && context.session has patient && context.session.patient == principal && resource.patient == principal) || (principal is User && context.session has patient && context.session.patient == principal && resource.patient.personalRepresentatives.contains(principal))))
    && !(principal is HealthCareProfessional && context.includesSecurityQuestionOrPassword)
    && !(resource.patient.isDeactivated)
};