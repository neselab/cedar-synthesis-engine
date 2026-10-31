permit (principal is User, action == Action::"approveDeployment", resource is Deployment)
when { ((((resource.changeRisk >= 0) && (resource.changeRisk <= 100))) && ((principal.roles.contains(Role::"Approver") || principal.roles.contains(Role::"ReleaseManager"))) && (!(true) || (principal != resource.committer) || (context.emergencyChange && (principal.roles.contains(Role::"ReleaseManager")))) && (context.sourceIp.isInRange(ip("192.168.0.0/16")))) };

permit (principal is User, action == Action::"promoteDeployment", resource is Deployment)
when { ((((principal.deployTier == 0) || (principal.deployTier == 1) || (principal.deployTier == 2)) && ((resource.targetEnv == 0) || (resource.targetEnv == 1) || (resource.targetEnv == 2))) && ((principal.roles.contains(Role::"ReleaseManager"))) && (!(true) || (resource.status == DeploymentStatusValue::"approved")) && ((principal == resource.approver)) && (context.sourceIp.isInRange(ip("172.16.0.0/12")))) };
