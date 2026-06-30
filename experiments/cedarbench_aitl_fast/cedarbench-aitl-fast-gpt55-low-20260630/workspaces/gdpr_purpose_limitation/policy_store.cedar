// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal,
  action == Action::"read",
  resource
)
when {
  principal is Processor
  && resource is PersonalData
  && resource.subjectConsent == true
  && (
    resource.allowedPurposes.contains(context.declaredPurpose)
    || (context has compatibleUseApproval && context.compatibleUseApproval == true)
  )
};

permit (
  principal,
  action == Action::"process",
  resource
)
when {
  principal is Processor
  && resource is PersonalData
  && resource.subjectConsent == true
  && (
    resource.allowedPurposes.contains(context.declaredPurpose)
    || (context has compatibleUseApproval && context.compatibleUseApproval == true)
  )
  && (
    principal.role == "controller"
    || principal.role == "processor"
  )
};

permit (
  principal,
  action == Action::"disclose",
  resource
)
when {
  principal is Processor
  && resource is PersonalData
  && resource.subjectConsent == true
  && (
    resource.allowedPurposes.contains(context.declaredPurpose)
    || (context has compatibleUseApproval && context.compatibleUseApproval == true)
  )
  && principal.role == "dpo"
};
