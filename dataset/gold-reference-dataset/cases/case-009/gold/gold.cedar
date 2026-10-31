permit (principal is User, action == Action::"authorizePort", resource is PortRequest)
when { (((resource.numberBlockSize >= 0)) && ((principal.roles.contains(Role::"PortingSpecialist") || principal.roles.contains(Role::"PortingSupervisor"))) && (!(true) || (resource.status == PortRequestStatusValue::"validated")) && (((context.authorizePortScheduledStart <= context.currentTime) && (context.currentTime < context.authorizePortScheduledEnd))) && (context.onCarrierNetwork)) };

permit (principal is User, action == Action::"completePort", resource is PortRequest)
when { (((resource.numberBlockSize >= 0)) && ((principal.roles.contains(Role::"LineTechnician") || principal.roles.contains(Role::"PortingSupervisor"))) && (!(true) || (principal == resource.assignedTechnician)) && (((principal.assignedCodePattern == "WHOLESALE-*") && (resource.carrierCode like "WHOLESALE-*"))) && (!((resource.numberBlockSize > 10)) || (principal.roles.contains(Role::"PortingSupervisor")))) };
