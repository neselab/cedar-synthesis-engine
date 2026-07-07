permit (principal is LabTechnician, action == Action::"recordLabProcedureResults", resource is LabProcedure) when {
    (context.session.isActive && context.session has labTechnician && context.session.labTechnician == principal)
    && !(resource.patient.isDeactivated)
};