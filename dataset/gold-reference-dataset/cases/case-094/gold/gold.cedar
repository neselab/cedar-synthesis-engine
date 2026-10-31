permit (principal is User, action == Action::"enterGrade", resource is GradeEntry)
when { (true && ((principal.roles.contains(Role::"InstructorOfRecord") || principal.roles.contains(Role::"TeachingAssistant"))) && (!(true) || (resource.status == GradeEntryStatusValue::"draft")) && ((context.currentTime < context.gradingDeadline)) && (resource.module.roster.contains(resource.learner))) };

permit (principal is User, action == Action::"releaseGrade", resource is GradeEntry)
when { (true && ((principal.roles.contains(Role::"InstructorOfRecord"))) && (!(true) || (principal == resource.postedBy)) && (!(true) || (resource.status == GradeEntryStatusValue::"posted")) && (((context.releaseGradeScheduledStart <= context.currentTime) && (context.currentTime < context.releaseGradeScheduledEnd)))) };
