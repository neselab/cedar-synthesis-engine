permit (principal is User, action == Action::"countersign", resource is Prescription)
when { (true && ((principal.roles.contains(Role::"AttendingPhysician"))) && (!(true) || (principal == resource.prescriber)) && (((("draft" == "draft") && (resource.status == PrescriptionStatusValue::"draft")) || (("draft" == "countersigned") && (resource.status == PrescriptionStatusValue::"countersigned")) || (("draft" == "dispensed") && (resource.status == PrescriptionStatusValue::"dispensed")))) && (context.mfaUsed)) };

permit (principal is User, action == Action::"dispense", resource is Prescription)
when { (true && ((principal.roles.contains(Role::"Pharmacist"))) && (!(true) || (resource.status == PrescriptionStatusValue::"countersigned")) && (context.mfaUsed)) };

permit (principal is User, action == Action::"writePrescription", resource is Prescription)
when { (true && ((principal.roles.contains(Role::"AttendingPhysician"))) && (!(true) || (principal != resource.patient))) };
