permit (principal is User, action == Action::"mergePullRequest", resource is PullRequest)
when { (((resource.approvalCount >= 0)) && ((principal.roles.contains(Role::"Maintainer"))) && (!(true) || (principal != resource.author)) && ((resource.targetBranch like "main")) && ((resource.approvalCount >= 1))) };

permit (principal is User, action == Action::"reviewPullRequest", resource is PullRequest)
when { (((resource.linesChanged >= 0)) && ((principal.roles.contains(Role::"Reviewer") || principal.roles.contains(Role::"Maintainer"))) && (!(true) || (principal != resource.author)) && (((context.reviewPullRequestScheduledStart <= context.currentTime) && (context.currentTime < context.reviewPullRequestScheduledEnd))) && ((principal.roles.contains(Role::"Maintainer")))) };
