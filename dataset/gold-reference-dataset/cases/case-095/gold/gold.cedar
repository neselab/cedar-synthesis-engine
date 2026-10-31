permit (principal is User, action == Action::"mergePullRequest", resource is PullRequest)
when { (((resource.approvalCount >= 0)) && ((principal.roles.contains(Role::"Maintainer"))) && (!(true) || (resource.status == PullRequestStatusValue::"approved")) && (!((resource.requiresSecurityReview == true)) || context.securityReviewCompleted) && ((resource.targetBranch like "hotfix/*"))) };

permit (principal is User, action == Action::"reviewPullRequest", resource is PullRequest)
when { (((resource.linesChanged >= 0)) && ((principal.roles.contains(Role::"Reviewer") || principal.roles.contains(Role::"Maintainer"))) && (!(true) || (resource.status == PullRequestStatusValue::"open")) && (resource.repo.team.contains(principal)) && (!((resource.linesChanged > 500)) || context.extendedReviewCompleted)) };
