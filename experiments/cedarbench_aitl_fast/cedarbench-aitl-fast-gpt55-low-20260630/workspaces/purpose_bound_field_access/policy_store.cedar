// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is Workforce,
  action == Action::"accessField",
  resource is PatientRecord
)
when {
  (
    context.declaredPurpose == "treatment" &&
    principal.role == "clinician" &&
    resource.purposeFieldsTreatment.contains(context.requestedField)
  ) ||
  (
    context.declaredPurpose == "billing" &&
    principal.role == "billing_clerk" &&
    resource.purposeFieldsBilling.contains(context.requestedField)
  ) ||
  (
    context.declaredPurpose == "research" &&
    principal.role == "researcher" &&
    resource.purposeFieldsResearch.contains(context.requestedField)
  )
};
