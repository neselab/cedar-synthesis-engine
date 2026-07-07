permit (principal, action == Action::"requestCatalogue", resource)
when {
    principal.role == "student"
    && context.onCampusLan
    && resource.semesterIsBeginning
};

permit (principal, action == Action::"registerCourse", resource)
when {
    principal.role == "student"
    && context.onCampusLan
    && resource.student == principal
    && resource.offering.isCurrentSemester
    && resource.offering.registrationOpen
};

permit (principal, action in [Action::"addCourseSelection", Action::"updateCourseSelection", Action::"deleteCourseSelection"], resource)
when {
    principal.role == "student"
    && context.onCampusLan
    && resource.student == principal
    && resource.isCurrentSelection
    && resource.offering.isCurrentSemester
    && resource.offering.registrationOpen
    && resource.offering.addDropOpen
};

permit (principal, action == Action::"viewReportCard", resource)
when {
    principal.role == "student"
    && context.onCampusLan
    && resource.student == principal
    && resource.previousSemesterCompleted
};

permit (principal, action == Action::"selectTeachingOffering", resource)
when {
    principal.role == "professor"
    && resource.isUpcomingSemester
    && resource.registrationOpen
    && !resource.hasTeachingConflict
    && resource.eligibleProfessors.contains(principal)
};

permit (principal, action == Action::"modifyAssignedOffering", resource)
when {
    principal.role == "professor"
    && resource.registrationOpen
    && resource has instructor
    && resource.instructor == principal
};

permit (principal, action == Action::"viewRoster", resource)
when {
    principal.role == "professor"
    && resource has instructor
    && resource.instructor == principal
};

permit (principal, action == Action::"enterGrade", resource)
when {
    principal.role == "professor"
    && resource.previousSemesterCompleted
    && resource.professor == principal
    && resource.offering has instructor
    && resource.offering.instructor == principal
};

permit (principal, action == Action::"changeStudentInfo", resource)
when {
    principal.role == "registrar"
};

permit (principal, action == Action::"closeRegistration", resource)
when {
    principal.role == "registrar"
    && resource.isCurrentSemester
    && resource.isOpen
};

