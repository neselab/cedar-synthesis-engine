permit (
  principal is User,
  action == Action::"request",
  resource is Document
)
when {
  principal.role == "requester"
};

permit (
  principal is User,
  action == Action::"review",
  resource is Document
)
when {
  principal.role == "reviewer"
};

permit (
  principal is User,
  action == Action::"approve",
  resource is Document
)
when {
  principal.role == "approver"
};

permit (
  principal is User,
  action == Action::"reject",
  resource is Document
)
when {
  principal.role == "approver"
};

permit (
  principal is User,
  action == Action::"escalate",
  resource is Document
)
when {
  principal.role == "requester"
};

permit (
  principal is User,
  action == Action::"delegate",
  resource is Document
)
when {
  principal.role == "approver"
};

permit (
  principal is User,
  action == Action::"cancel",
  resource is Document
)
when {
  principal.role == "requester"
};

permit (
  principal is User,
  action == Action::"resubmit",
  resource is Document
)
when {
  principal.role == "requester"
};

permit (
  principal is User,
  action == Action::"audit",
  resource is Document
)
when {
  principal.role == "auditor"
};

permit (
  principal is User,
  action == Action::"close",
  resource is Document
)
when {
  principal.role == "manager"
};

permit (
  principal is User,
  action == Action::"reopen",
  resource is Document
)
when {
  principal.role == "manager"
};

permit (
  principal is User,
  action == Action::"archive",
  resource is Document
)
when {
  principal.role == "manager"
};

permit (
  principal is User,
  action == Action::"export",
  resource is Document
)
when {
  principal.role == "auditor"
};

permit (
  principal is User,
  action == Action::"sign",
  resource is Document
)
when {
  principal.role == "approver"
};

permit (
  principal is User,
  action == Action::"countersign",
  resource is Document
)
when {
  principal.role == "manager"
};

permit (
  principal is User,
  action == Action::"annotate",
  resource is Document
)
when {
  principal.role == "requester"
};

permit (
  principal is User,
  action == Action::"comment",
  resource is Document
)
when {
  principal.role == "requester"
};

permit (
  principal is User,
  action == Action::"notify",
  resource is Document
)
when {
  principal.role == "manager"
};

permit (
  principal is User,
  action == Action::"cc",
  resource is Document
)
when {
  principal.role == "requester"
};

permit (
  principal is User,
  action == Action::"bcc",
  resource is Document
)
when {
  principal.role == "manager"
};