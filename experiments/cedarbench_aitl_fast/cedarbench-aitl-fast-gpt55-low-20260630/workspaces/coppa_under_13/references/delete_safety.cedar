// Ceiling: delete permitted only when the requesting principal is
// the owner of the data point. Any user may request deletion of
// their own data at any time (this satisfies COPPA §312.6 right of
// review/deletion as well as general data-subject rights).
permit (
    principal is User,
    action == Action::"delete",
    resource is DataPoint
)
when {
    principal == resource.owner
};
