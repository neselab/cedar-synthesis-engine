permit (principal is User, action == Action::"executeLease", resource is ExecutedLease)
when { (((resource.lease.monthlyRent >= 0)) && ((principal.roles.contains(Role::"Broker") || principal.roles.contains(Role::"ComplianceOfficer"))) && (!(true) || (resource.lease.status == LeaseStatusValue::"signed")) && (resource.lease.segment.contains("regulated"))) };

permit (principal is User, action == Action::"reviewLease", resource is Lease)
when { (((resource.monthlyRent >= 0) && (resource.squareFootage >= 0) && ((resource.termMonths >= 1) && (resource.termMonths <= 120))) && ((principal.roles.contains(Role::"Broker") || principal.roles.contains(Role::"TransactionCoordinator"))) && (!(true) || (resource.status == LeaseStatusValue::"drafted")) && ((resource.leaseCode like "COMMERCIAL-*")) && (!((resource.monthlyRent > 1000000)) || (principal.roles.contains(Role::"Broker")))) };
