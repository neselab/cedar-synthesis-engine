permit (principal is HealthCareProfessional, action == Action::"modifyOfficeVisit", resource is OfficeVisit) when {
    (context.session.isActive && context.session has healthCareProfessional && context.session.healthCareProfessional == principal)
    && !(resource.patient.isDeactivated)
    && !(resource.patient.isDeactivated)
};