permit (principal is Hcp, action == Action::"createPatient", resource is Patient)
when { !(!context.session.isActive) };