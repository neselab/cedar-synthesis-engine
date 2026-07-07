permit (principal is UnlicensedPersonnel, action == Action::"modifyOfficeVisit", resource is OfficeVisit) when {
    (context.session.isActive && context.session has unlicensedPersonnel && context.session.unlicensedPersonnel == principal)
    && !(resource.patient.isDeactivated)
    && !(resource.patient.isDeactivated)
};