permit (principal is Patient, action == Action::"viewOfficeVisitInformation", resource is OfficeVisit) when {
    (context.session.isActive && context.session has patient && context.session.patient == principal && resource.patient == principal)
    && !(context.includesNotes)
};