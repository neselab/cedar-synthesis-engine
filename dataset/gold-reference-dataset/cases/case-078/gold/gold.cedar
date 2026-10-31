permit (principal is User, action == Action::"confirmDelivery", resource is Shipment)
when { (((resource.pieceCount >= 0)) && ((principal.roles.contains(Role::"Driver") || principal.roles.contains(Role::"DepotSupervisor"))) && (!(true) || (resource.status == ShipmentStatusValue::"intransit")) && (!(resource.hazmatClass.contains("flammable")) || context.custodySignatureCaptured) && (context.proofOfDelivery)) };

permit (principal is User, action == Action::"dispatchShipment", resource is Shipment)
when { (((resource.pieceCount >= 0)) && ((principal.roles.contains(Role::"Driver") || principal.roles.contains(Role::"DispatchManager"))) && (!(true) || (resource.status == ShipmentStatusValue::"created")) && (resource.hazmatClass.contains("toxic")) && (!((resource.pieceCount > 1000)) || (principal.roles.contains(Role::"DispatchManager")))) };
