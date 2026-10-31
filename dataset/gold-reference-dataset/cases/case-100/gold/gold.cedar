permit (principal is User, action == Action::"disburseReimbursement", resource is Reimbursement)
when { (((resource.amount >= 0)) && ((principal.roles.contains(Role::"Controller"))) && (!(((resource.amount > 25000))) || ((resource.report has approver) && (principal != resource.report.approver))) && ((resource.report has approver))) };
