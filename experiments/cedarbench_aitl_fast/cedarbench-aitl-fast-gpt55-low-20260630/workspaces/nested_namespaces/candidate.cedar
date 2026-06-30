permit (
  principal is Company::Identity::Employee,
  action == Company::Billing::Invoice::Action::"view",
  resource is Company::Billing::Invoice::Line
)
when {
  principal == resource.issuer ||
  principal == resource.owningTeam.manager ||
  principal.department == resource.issuer.department
};

permit (
  principal is Company::Identity::Employee,
  action == Company::Billing::Invoice::Action::"approve",
  resource is Company::Billing::Invoice::Line
)
when {
  (
    principal == resource.owningTeam.manager &&
    principal.level >= 3 &&
    resource.total <= 10000
  ) ||
  (
    principal.level >= 5 &&
    resource.total <= 100000
  )
};

permit (
  principal is Company::Identity::Employee,
  action == Company::Billing::Invoice::Action::"void",
  resource is Company::Billing::Invoice::Line
)
when {
  principal == resource.owningTeam.manager &&
  principal.level >= 5
};