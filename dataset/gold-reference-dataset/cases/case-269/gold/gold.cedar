permit (principal is User, action == Action::"executeContract", resource is Contract)
when { (((resource.contractValue >= 0)) && ((principal.roles.contains(Role::"ContractAdmin"))) && (!(true) || (resource.status == ContractStatusValue::"signed")) && (!((resource.contractValue > 100000000)) || context.executeContractV8ReviewCompleted) && (context.onCorpNetwork)) };

permit (principal is User, action == Action::"reviewContract", resource is Contract)
when { (((resource.contractValue >= 0)) && ((principal.roles.contains(Role::"Reviewer"))) && (!(true) || (principal != resource.drafter)) && (!(true) || (resource.status == ContractStatusValue::"draft"))) };

permit (principal is User, action == Action::"signContract", resource is Contract)
when { ((((principal.signingAuthority == 0) || (principal.signingAuthority == 1) || (principal.signingAuthority == 2)) && (resource.contractValue >= 0) && ((resource.requiredAuthority == 0) || (resource.requiredAuthority == 1) || (resource.requiredAuthority == 2))) && ((principal.roles.contains(Role::"Signatory") || principal.roles.contains(Role::"ContractAdmin"))) && (!(true) || (principal.signingAuthority >= resource.requiredAuthority) || (context.escalationApproved && (principal.roles.contains(Role::"Signatory"))))) };
