// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is Identity::User,
    action == Billing::Action::"viewInvoice",
    resource is Billing::Invoice
)
when {
    principal == resource.customer
};

permit (
    principal is Identity::User,
    action == Shipping::Action::"viewAddress",
    resource is Shipping::Address
)
when {
    principal == resource.owner
};
