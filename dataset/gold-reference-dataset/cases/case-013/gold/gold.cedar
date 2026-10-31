permit (principal is User, action == Action::"approveAward", resource is Award)
when { ((((principal.approvalAuthority == 0) || (principal.approvalAuthority == 1) || (principal.approvalAuthority == 2)) && (resource.amount >= 0) && ((resource.application.fundingTier == 0) || (resource.application.fundingTier == 1) || (resource.application.fundingTier == 2))) && ((principal.roles.contains(Role::"ProgramOfficer") || principal.roles.contains(Role::"GrantsOfficer"))) && (!(true) || (resource.status == AwardStatusValue::"pending")) && (!((principal == resource.application.applicant))) && ((principal.roles.contains(Role::"ProgramOfficer")))) };

permit (principal is User, action == Action::"obligateFunds", resource is Award)
when { (((resource.amount >= 0)) && ((principal.roles.contains(Role::"GrantsOfficer"))) && (!(true) || (principal != resource.approvedBy)) && (!((resource.highRiskFlag == true)) || context.highRiskReviewCompleted) && (context.onGovNetwork)) };
