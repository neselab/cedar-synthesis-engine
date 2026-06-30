permit (
    principal is Employee,
    action == Action::"book",
    resource is Room
)
when {
    principal.level >= resource.minBookingLevel &&
    context.groupSize <= resource.capacity &&
    context.bookingStart > context.now
};

permit (
    principal is Employee,
    action == Action::"cancel",
    resource is Room
);

permit (
    principal is Employee,
    action == Action::"view",
    resource is Room
);