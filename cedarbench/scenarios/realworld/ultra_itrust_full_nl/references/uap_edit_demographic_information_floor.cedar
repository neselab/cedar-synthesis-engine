permit (principal is UnlicensedPersonnel, action == Action::"editDemographicInformation", resource is DemographicInformation) when {
    (context.session.isActive && context.session has unlicensedPersonnel && context.session.unlicensedPersonnel == principal)
    && !(principal is HealthCareProfessional && context.includesSecurityQuestionOrPassword)
    && !(resource.patient.isDeactivated)
};