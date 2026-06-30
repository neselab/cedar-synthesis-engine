permit (
    principal is User,
    action == Action::"View",
    resource is Document
) when {
    principal in Role::"SponsorRepresentative" &&
    resource.studyPhase == "Phase-3" &&
    resource.projectStatus == "Active"
};