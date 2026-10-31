Pull Request Merge and Review Access

A user may merge a pull request only if the user has the maintainer role, is not the pull request’s author, and the pull request targets the branch named exactly “main” and has at least one approval.

A user may review a pull request only if the user has the maintainer role, is not the pull request’s author, and the pull request has a nonnegative number of lines changed. The current time must be at or after the request’s scheduled review start and strictly before its scheduled review end. Times are in UTC. The reviewer role alone is not sufficient.

These are the only permissions: each activity is allowed if and only if all its stated requirements hold for a user acting on a pull request.
