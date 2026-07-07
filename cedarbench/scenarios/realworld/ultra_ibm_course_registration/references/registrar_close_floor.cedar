permit (principal is User, action == Action::"closeRegistration", resource is RegistrationProcess)
when {
    principal.role == "registrar"
    && resource.isCurrentSemester
    && resource.isOpen
};

