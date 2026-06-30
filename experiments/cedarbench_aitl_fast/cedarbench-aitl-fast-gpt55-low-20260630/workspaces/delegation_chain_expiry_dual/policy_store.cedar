// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is User,
  action == Action::"read",
  resource is Resource
)
when {
  principal == resource.owner
};

permit (
  principal is User,
  action == Action::"write",
  resource is Resource
)
when {
  principal == resource.owner
};

permit (
  principal is User,
  action == Action::"read",
  resource is Resource
)
when {
  context has firstGrant &&
  context.firstGrant.delegatee == principal &&
  context.firstGrant.grantedAt <= context.now &&
  context.firstGrant.expiresAt >= context.now
};

permit (
  principal is User,
  action == Action::"write",
  resource is Resource
)
when {
  context has firstGrant &&
  context.firstGrant.delegatee == principal &&
  context.firstGrant.grantedAt <= context.now &&
  context.firstGrant.expiresAt >= context.now
};

permit (
  principal is User,
  action == Action::"read",
  resource is Resource
)
when {
  context has firstGrant &&
  context has secondGrant &&
  context.firstGrant.delegatee == context.secondGrant.delegator &&
  context.secondGrant.delegatee == principal &&
  context.firstGrant.grantedAt <= context.now &&
  context.firstGrant.expiresAt >= context.now &&
  context.secondGrant.grantedAt <= context.now &&
  context.secondGrant.expiresAt >= context.now
};

permit (
  principal is User,
  action == Action::"write",
  resource is Resource
)
when {
  context has firstGrant &&
  context has secondGrant &&
  context.firstGrant.delegatee == context.secondGrant.delegator &&
  context.secondGrant.delegatee == principal &&
  context.firstGrant.grantedAt <= context.now &&
  context.firstGrant.expiresAt >= context.now &&
  context.secondGrant.grantedAt <= context.now &&
  context.secondGrant.expiresAt >= context.now
};
