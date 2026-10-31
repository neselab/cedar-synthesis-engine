permit (principal is User, action == Action::"releaseToProduction", resource is WorkOrder)
when { ((((resource.defectCount >= 0) && (resource.defectCount <= 100))) && ((principal.roles.contains(Role::"Inspector") || principal.roles.contains(Role::"QualityManager"))) && (!(true) || (resource.status == WorkOrderStatusValue::"inspected")) && ((resource.holdFlag == false)) && ((resource.partCode like "SAFETY-*"))) };

permit (principal is User, action == Action::"signoffWorkOrder", resource is WorkOrder)
when { ((((resource.defectCount >= 0) && (resource.defectCount <= 100))) && ((principal.roles.contains(Role::"Inspector") || principal.roles.contains(Role::"QualityManager"))) && (!(true) || (principal != resource.operator)) && (context.onPlantNetwork)) };
