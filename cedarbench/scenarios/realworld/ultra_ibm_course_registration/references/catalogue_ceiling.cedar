permit (principal is User, action == Action::"requestCatalogue", resource is CourseCatalogue)
when {
    principal.role == "student"
    && context.onCampusLan
    && resource.semesterIsBeginning
};

