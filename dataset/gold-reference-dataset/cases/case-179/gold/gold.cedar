permit (principal is User, action == Action::"mergePullRequest", resource is PullRequest)
when { (((resource.approvalCount >= 0)) && ((principal.roles.contains(Role::"Maintainer"))) && (!(true) || (resource.status == PullRequestStatusValue::"approved")) && ((resource.targetBranch like "release/*")) && ((resource.approvalCount >= 2))) };

permit (principal is User, action == Action::"reviewPullRequest", resource is PullRequest)
when { (((resource.linesChanged >= 0)) && ((principal.roles.contains(Role::"Reviewer") || principal.roles.contains(Role::"Maintainer"))) && (!(true) || (principal != resource.author)) && (!((resource.requiresSecurityReview == true)) || context.securityReviewCompleted) && ((principal.roles.contains(Role::"Maintainer")))) };
