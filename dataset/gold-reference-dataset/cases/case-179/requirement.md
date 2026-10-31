Pull Request Merge and Review Access

A user may merge a pull request only if the user holds the maintainer role, the pull request has approved status, its target branch name begins with “release/”, and its approval count is nonnegative and at least two.

A user may review a pull request only if the user holds the maintainer role, is not the pull request’s author, and the pull request’s lines-changed count is nonnegative. The reviewer role alone is insufficient. If the pull request requires security review, the host application must also confirm that the security review has been completed; otherwise, this completion requirement does not apply.

These are the only permissions: each activity is allowed when all its stated requirements are met, and no other activities are authorized.
