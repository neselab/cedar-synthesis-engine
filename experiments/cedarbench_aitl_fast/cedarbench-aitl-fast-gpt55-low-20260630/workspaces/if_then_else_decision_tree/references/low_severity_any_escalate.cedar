// Floor: any Responder MUST be permitted to escalate an incident
// whose severity is below 8. Below the threshold the escalate gate
// is unconditional.
permit (
    principal is Responder,
    action == Action::"escalate",
    resource is Incident
)
when {
    resource.severity <= 7
};
