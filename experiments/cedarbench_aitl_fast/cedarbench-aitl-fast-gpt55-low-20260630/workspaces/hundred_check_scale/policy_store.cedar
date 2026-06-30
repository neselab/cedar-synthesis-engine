// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"viewOrder",
    resource is Order
) when {
    principal.role == "viewer" ||
    principal.role == "cs_agent" ||
    principal.role == "cs_manager" ||
    principal.role == "fulfillment" ||
    principal.role == "warehouse_lead" ||
    principal.role == "returns" ||
    principal.role == "finance_ops" ||
    principal.role == "finance_manager" ||
    principal.role == "platform_admin" ||
    principal.role == "security_admin"
};

permit (
    principal is User,
    action == Action::"listOrders",
    resource is Order
) when {
    principal.role == "viewer" ||
    principal.role == "cs_agent" ||
    principal.role == "cs_manager" ||
    principal.role == "fulfillment" ||
    principal.role == "warehouse_lead" ||
    principal.role == "returns" ||
    principal.role == "finance_ops" ||
    principal.role == "finance_manager" ||
    principal.role == "platform_admin" ||
    principal.role == "security_admin"
};

permit (
    principal is User,
    action == Action::"updateCart",
    resource is Order
) when {
    resource.status == "cart" &&
    (
        principal.role == "viewer" ||
        principal.role == "cs_agent" ||
        principal.role == "cs_manager"
    )
};

permit (
    principal is User,
    action == Action::"placeOrder",
    resource is Order
) when {
    resource.status == "pending" &&
    (
        principal.role == "viewer" ||
        principal.role == "cs_agent" ||
        principal.role == "cs_manager"
    )
};

permit (
    principal is User,
    action == Action::"cancelOrder",
    resource is Order
) when {
    resource.status == "pending" &&
    (
        principal.role == "cs_agent" ||
        principal.role == "cs_manager" ||
        principal.role == "finance_ops" ||
        principal.role == "finance_manager"
    )
};

permit (
    principal is User,
    action == Action::"refundOrder",
    resource is Order
) when {
    resource.status == "delivered" &&
    (
        principal.role == "cs_manager" ||
        principal.role == "finance_ops" ||
        principal.role == "finance_manager"
    )
};

permit (
    principal is User,
    action == Action::"shipOrder",
    resource is Order
) when {
    resource.status == "pending" &&
    (
        principal.role == "fulfillment" ||
        principal.role == "warehouse_lead"
    )
};

permit (
    principal is User,
    action == Action::"markDelivered",
    resource is Order
) when {
    resource.status == "shipped" &&
    (
        principal.role == "fulfillment" ||
        principal.role == "warehouse_lead"
    )
};

permit (
    principal is User,
    action == Action::"modifyPricing",
    resource is Order
) when {
    principal.role == "finance_manager" ||
    principal.role == "platform_admin"
};

permit (
    principal is User,
    action == Action::"adminOverride",
    resource is Order
) when {
    principal.role == "platform_admin" ||
    principal.role == "security_admin"
};
