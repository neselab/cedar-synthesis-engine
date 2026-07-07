permit (principal is User, action == Action::"viewOfficeVisitInformation", resource is OfficeVisit) when {
    (context.session.isActive && context.session has user && context.session has user && context.session has user && context.session.user == principal && principal in resource.patient.personalRepresentatives)
    && !(context.includesNotes)
};