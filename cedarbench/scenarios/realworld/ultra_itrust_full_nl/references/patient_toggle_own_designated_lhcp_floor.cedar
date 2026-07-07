permit (principal is Patient, action == Action::"toggleDesignatedLHCP", resource is LicensedHealthCareProfessional) when {
    (context.session.isActive && context.session has patient && context.session.patient == principal && context.patient == principal)
    && !(context.patient.isDeactivated)
};