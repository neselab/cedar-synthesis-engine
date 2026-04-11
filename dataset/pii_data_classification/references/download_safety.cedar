// Ceiling: downloadDocument permitted only when ALL of:
//  (a) clearance is ONE LEVEL HIGHER than read (one tier stricter),
//  (b) the document is NOT Restricted (Restricted cannot be downloaded),
//  (c) PII training if the document contains PII,
//  (d) need-to-know for Restricted (vacuously true since Restricted is
//      disallowed by (b)).
permit (
    principal is User,
    action == Action::"downloadDocument",
    resource is Document
)
when {
    resource.classification != "Restricted"
    && (
        (resource.classification == "Public" && (principal.clearance == "L2" || principal.clearance == "L3" || principal.clearance == "L4"))
        || (resource.classification == "Internal" && (principal.clearance == "L3" || principal.clearance == "L4"))
        || (resource.classification == "Confidential" && principal.clearance == "L4")
    )
    && (!resource.containsPII || principal.hasPIITraining)
};
