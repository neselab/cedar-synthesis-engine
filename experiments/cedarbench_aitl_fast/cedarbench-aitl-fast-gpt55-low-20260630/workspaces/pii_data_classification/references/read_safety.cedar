// Ceiling: readDocument permitted only when ALL of:
//  (a) clearance dominates classification per the read table,
//  (b) if the document contains PII, the user has PII training,
//  (c) if the document is Restricted, the user is in the need-to-know set.
permit (
    principal is User,
    action == Action::"readDocument",
    resource is Document
)
when {
    (
        resource.classification == "Public"
        || (resource.classification == "Internal" && (principal.clearance == "L2" || principal.clearance == "L3" || principal.clearance == "L4"))
        || (resource.classification == "Confidential" && (principal.clearance == "L3" || principal.clearance == "L4"))
        || (resource.classification == "Restricted" && principal.clearance == "L4")
    )
    && (!resource.containsPII || principal.hasPIITraining)
    && (resource.classification != "Restricted" || principal in resource.needToKnow)
};
