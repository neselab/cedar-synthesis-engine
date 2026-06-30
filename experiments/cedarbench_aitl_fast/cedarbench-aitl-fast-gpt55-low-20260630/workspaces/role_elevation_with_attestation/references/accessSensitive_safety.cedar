// Ceiling: accessSensitive permitted only when EITHER
//   (A) baseRole == "manager"  (standing authority), OR
//   (B) baseRole in {"user","lead"} AND elevationGranted == true
//       AND context has elevationJustification AND it is non-empty.
permit (
    principal is User,
    action == Action::"accessSensitive",
    resource is SensitiveResource
)
when {
    principal.baseRole == "manager"
    || (
        (principal.baseRole == "user" || principal.baseRole == "lead")
        && principal.elevationGranted == true
        && context has elevationJustification
        && context.elevationJustification != ""
    )
};
