// Ceiling for viewEmergency: any Approver may view. The schema
// constrains principal to Approver, so the trivial permit is an
// upper bound — any candidate that permits viewEmergency at all
// must be no more permissive than this.
permit (
    principal is Approver,
    action == Action::"viewEmergency",
    resource is EmergencyAction
);
