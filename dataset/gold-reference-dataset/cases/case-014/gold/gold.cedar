permit (principal is User, action == Action::"approveBudget", resource is Campaign)
when { (((resource.budget >= 0) && ((resource.budgetTier == 0) || (resource.budgetTier == 1) || (resource.budgetTier == 2)) && (resource.contingency >= 0)) && ((principal.roles.contains(Role::"CampaignDirector") || principal.roles.contains(Role::"AccountManager"))) && (!((((resource.budget > 1500000) || (resource.contingency > (1500000 - resource.budget))))) || (principal != resource.preparedBy) || (context.emergencyLaunch && (principal.roles.contains(Role::"CampaignDirector"))))) };

permit (principal is User, action == Action::"launchCampaign", resource is Campaign)
when { (true && ((principal.roles.contains(Role::"AccountManager") || principal.roles.contains(Role::"CampaignDirector"))) && (!(true) || (resource.status == CampaignStatusValue::"approved")) && ((principal == resource.advertiser)) && (resource.riskLabels.contains("restricted"))) };
