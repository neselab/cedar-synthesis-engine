permit (principal is Identity::User, action == Audit::Action::"recordEvent", resource is Audit::Event)
when { principal == resource.actor };
