// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is Operator,
  action == Action::"connect",
  resource is Server
)
when {
  (
    (context.clientIp.isIpv4() && context.clientIp.isInRange(ip("10.0.0.0/8"))) ||
    (context.clientIp.isIpv6() && context.clientIp.isInRange(ip("2001:db8::/48")))
  ) &&
  (
    resource.serverIp.isLoopback() ||
    (context.clientIp.isIpv4() && resource.serverIp.isIpv4()) ||
    (context.clientIp.isIpv6() && resource.serverIp.isIpv6())
  )
};

permit (
  principal is Operator,
  action == Action::"manage",
  resource is Server
)
when {
  (context.clientIp.isIpv4() && context.clientIp.isInRange(ip("10.20.0.0/24"))) ||
  (context.clientIp.isIpv6() && context.clientIp.isInRange(ip("2001:db8:1::/64")))
};
