// Ceiling: share permitted only when:
//   (a) the data category is "anonymous" (always shareable), OR
//   (b) the data category is "behavioral" or "geolocation" AND the
//       owning user is 13 or older.
//
// Personal data is NEVER shareable, regardless of age or parental
// consent — this is the COPPA-stricter rule for third-party sharing
// of children's PII (16 CFR Part 312.5(a)(2) prohibits conditioning
// participation on disclosure of more information than reasonably
// necessary, and §312.4 / §312.5 do not authorize disclosure of
// personal data of children even with parental consent in the
// strictest reading).
//
// Note that the age check is on resource.owner.dateOfBirth, not
// principal.dateOfBirth — the COPPA protection attaches to the
// person to whom the data pertains, not the person making the
// share request.
permit (
    principal is User,
    action == Action::"share",
    resource is DataPoint
)
when {
    resource.category == "anonymous"
    || ((resource.category == "behavioral" || resource.category == "geolocation")
        && context.now.durationSince(resource.owner.dateOfBirth) >= duration("4748d"))
};
