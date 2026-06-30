// Floor for viewEmergency: any Approver MUST be able to view.
permit (
    principal is Approver,
    action == Action::"viewEmergency",
    resource is EmergencyAction
);
