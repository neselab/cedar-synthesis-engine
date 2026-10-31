permit (principal is User, action == Action::"approvePayroll", resource is PayrollRun)
when { (((resource.amount >= 0)) && ((principal.roles.contains(Role::"Manager") || principal.roles.contains(Role::"PayrollAdmin"))) && (!(((resource.amount > 50000000))) || (principal != resource.preparedBy)) && (!(true) || (resource.status == PayrollRunStatusValue::"submitted")) && (context.onVpn)) };
