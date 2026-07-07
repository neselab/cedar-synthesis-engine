permit (principal is User, action == Action::"changeStudentInfo", resource is StudentInfo)
when {
    principal.role == "registrar"
};

