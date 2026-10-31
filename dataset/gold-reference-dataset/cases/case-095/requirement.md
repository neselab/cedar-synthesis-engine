Pull Request Merge and Review Access

A user may merge a pull request only if they hold the maintainer role, the pull request has a nonnegative approval count and approved status, and its target branch starts with “hotfix/” (with any characters or no characters after the slash). If the pull request requires security review, that review must have been completed.

A user may review a pull request only if they hold the reviewer or maintainer role, belong to the pull request’s repository team, and the pull request has a nonnegative number of lines changed and open status. If more than 500 lines have changed, an extended review must have been completed.

These are the only permissions: each activity is allowed when all its stated requirements are met, and no other activity is authorized.
