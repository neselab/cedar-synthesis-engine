permit (principal is User, action == Action::"enterGrade", resource is GradeEntry)
when { (true && ((principal.roles.contains(Role::"InstructorOfRecord") || principal.roles.contains(Role::"TeachingAssistant"))) && (!(true) || (principal != resource.learner)) && ((principal.roles.contains(Role::"TeachingAssistant"))) && (context.onInstitutionNetwork)) };

permit (principal is User, action == Action::"releaseGrade", resource is GradeEntry)
when { (true && ((principal.roles.contains(Role::"InstructorOfRecord"))) && (!(true) || (principal == resource.postedBy)) && (context.onInstitutionNetwork)) };
