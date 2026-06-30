permit (principal is Identity::User, action == Shipping::Action::"viewAddress", resource is Shipping::Address)
when { principal == resource.owner };
