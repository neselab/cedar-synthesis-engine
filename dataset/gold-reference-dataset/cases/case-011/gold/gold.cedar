permit (principal is User, action == Action::"mergePullRequest", resource is PullRequest)
when { (((resource.approvalCount >= 0)) && ((principal.roles.contains(Role::"Maintainer"))) && (!(true) || (principal != resource.author)) && ((resource.targetBranch like "hotfix/*")) && ((resource.approvalCount >= 1)) && (context.onVpn)) };
