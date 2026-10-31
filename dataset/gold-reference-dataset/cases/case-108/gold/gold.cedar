permit (principal is User, action == Action::"approveClaim", resource is Claim)
when { (((resource.claimAmount >= 0) && (resource.deductible >= 0) && (resource.lineItemCount >= 0)) && ((principal.roles.contains(Role::"Reviewer") || principal.roles.contains(Role::"ClaimsManager"))) && (!(((resource.lineItemCount > 20) || (resource.claimAmount > 1000000))) || (principal != resource.handler))) };

permit (principal is User, action == Action::"issuePayout", resource is Payout)
when { (((resource.amount >= 0) && (resource.claim.claimAmount >= 0) && (resource.claim.deductible >= 0) && (resource.claim.lineItemCount >= 0)) && ((principal.roles.contains(Role::"PayoutOfficer") || principal.roles.contains(Role::"ClaimsManager"))) && (!(((resource.claim.lineItemCount > 20))) || (principal != resource.claim.approver)) && (((context.issuePayoutScheduledStart <= context.currentTime) && (context.currentTime < context.issuePayoutScheduledEnd)))) };
