permit (principal is User, action == Action::"postGrade", resource is Grade)
when { (true && ((principal.roles.contains(Role::"Instructor"))) && (!(true) || (principal != resource.student)) && (!(true) || (resource.status == GradeStatusValue::"draft")) && ((context.currentDate < context.gradingDeadline)) && (resource.courseRecord.roster.contains(resource.student)) && (context.onCampusNetwork)) };
