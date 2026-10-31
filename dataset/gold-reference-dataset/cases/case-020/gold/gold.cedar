permit (principal is User, action == Action::"authorizeRefill", resource is Prescription)
when { ((((resource.refillsRemaining >= 0) && (resource.refillsRemaining <= 12))) && ((principal.roles.contains(Role::"PharmacistInCharge"))) && (!(true) || (resource.status == PrescriptionStatusValue::"dispensed")) && ((resource.prescriberDEA like "BC*")) && ((resource.refillsRemaining > 0))) };

permit (principal is User, action == Action::"verifyPrescription", resource is Prescription)
when { ((((resource.refillsRemaining >= 0) && (resource.refillsRemaining <= 12))) && ((principal.roles.contains(Role::"StaffPharmacist") || principal.roles.contains(Role::"PharmacistInCharge"))) && (!(true) || (principal != resource.enteredBy)) && ((principal.roles.contains(Role::"PharmacistInCharge"))) && (!((resource.refillsRemaining > 0)) || context.verifyPrescriptionV6ReviewCompleted)) };
