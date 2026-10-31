permit (principal is User, action == Action::"releaseToProduction", resource is WorkOrder)
when { ((((resource.defectCount >= 0) && (resource.defectCount <= 100))) && ((principal.roles.contains(Role::"Inspector") || principal.roles.contains(Role::"QualityManager"))) && (!(true) || (resource.status == WorkOrderStatusValue::"inspected")) && (((context.releaseToProductionScheduledStart <= context.currentTime) && (context.currentTime < context.releaseToProductionScheduledEnd))) && ((resource.partCode like "CONTROLLED-*"))) };

permit (principal is User, action == Action::"signoffWorkOrder", resource is WorkOrder)
when { ((((resource.defectCount >= 0) && (resource.defectCount <= 100))) && ((principal.roles.contains(Role::"Inspector") || principal.roles.contains(Role::"QualityManager"))) && (!(true) || (resource.status == WorkOrderStatusValue::"inprogress")) && ((resource.defectCount <= 2)) && (context.onPlantNetwork)) };
