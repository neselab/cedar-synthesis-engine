permit (principal is User, action == Action::"approvePayroll", resource is PayrollRun)
when { (((resource.amount >= 0)) && ((principal.roles.contains(Role::"Manager") || principal.roles.contains(Role::"PayrollAdmin"))) && (!(((resource.amount > 10000000))) || (principal != resource.preparedBy)) && ((principal.roles.contains(Role::"Manager"))) && (context.onVpn)) };
