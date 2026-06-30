// Ceiling: accessField is permitted ONLY when one of three branches holds:
//   - declared purpose "treatment" + clinician role + field in
//     resource.purposeFieldsTreatment
//   - declared purpose "billing"   + billing_clerk role + field in
//     resource.purposeFieldsBilling
//   - declared purpose "research"  + researcher role + field in
//     resource.purposeFieldsResearch
// Cedar has no dynamic record key access, so branches are explicit.
permit (
    principal is Workforce,
    action == Action::"accessField",
    resource is PatientRecord
)
when {
    (context.declaredPurpose == "treatment"
        && principal.role == "clinician"
        && resource.purposeFieldsTreatment.contains(context.requestedField))
    || (context.declaredPurpose == "billing"
        && principal.role == "billing_clerk"
        && resource.purposeFieldsBilling.contains(context.requestedField))
    || (context.declaredPurpose == "research"
        && principal.role == "researcher"
        && resource.purposeFieldsResearch.contains(context.requestedField))
};
