// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is User,
  action == Action::"withdraw",
  resource is Account
)
when {
  resource.balance.greaterThan(decimal("0.0001"))
};

permit (
  principal is User,
  action == Action::"transfer",
  resource is Transaction
)
when {
  resource.amount.greaterThan(decimal("0.0000")) &&
  resource.amount.lessThanOrEqual(decimal("1000000.0000"))
};

permit (
  principal is User,
  action == Action::"viewBalance",
  resource is Account
);
